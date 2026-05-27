"""
Medications Blueprint（/api/user）

用藥管理 CRUD + 排程 + 服藥紀錄 + Push Token。
"""

import logging
from datetime import date, datetime, time

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.medication import Medication, MedicationSchedule, AdherenceLog, PushToken
from models.profile import Profile

logger = logging.getLogger(__name__)

medications_bp = Blueprint("medications", __name__, url_prefix="/api/user")


# ============================================
# S1-1  Medications CRUD
# ============================================


@medications_bp.route("/medications", methods=["GET"])
@jwt_required()
def list_medications():
    user_id = int(get_jwt_identity())
    profile_id = request.args.get("profile_id", type=int)
    active_only = request.args.get("active", "true").lower() == "true"

    q = Medication.query.filter_by(user_id=user_id)
    if profile_id:
        q = q.filter_by(profile_id=profile_id)
    if active_only:
        q = q.filter_by(is_active=True)

    meds = q.order_by(Medication.created_at.desc()).all()
    return jsonify({"success": True, "medications": [m.to_dict() for m in meds]}), 200


@medications_bp.route("/medications", methods=["POST"])
@jwt_required()
def create_medication():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "缺少 JSON body"}), 400

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "name 為必填"}), 400

    profile_id = data.get("profile_id")
    if not profile_id:
        return jsonify({"success": False, "error": "profile_id 為必填"}), 400

    # 確認 profile 屬於此 user
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
    if not profile:
        return jsonify({"success": False, "error": "Profile 不存在"}), 404

    # 解析日期
    try:
        start_date = date.fromisoformat(
            data.get("start_date", date.today().isoformat())
        )
    except ValueError:
        return (
            jsonify({"success": False, "error": "start_date 格式須為 YYYY-MM-DD"}),
            400,
        )

    end_date = None
    if data.get("end_date"):
        try:
            end_date = date.fromisoformat(data["end_date"])
        except ValueError:
            return (
                jsonify({"success": False, "error": "end_date 格式須為 YYYY-MM-DD"}),
                400,
            )

    med = Medication(
        user_id=user_id,
        profile_id=profile_id,
        drug_id=data.get("drug_id"),
        name=name,
        dosage=data.get("dosage"),
        unit=data.get("unit"),
        frequency=data.get("frequency", "daily"),
        duration_days=data.get("duration_days"),
        start_date=start_date,
        end_date=end_date,
        stock_qty=data.get("stock_qty"),
        note=data.get("note"),
    )
    db.session.add(med)
    db.session.flush()  # 取得 med.id

    # 建立排程
    for sched in data.get("schedules", []):
        ts = (sched.get("time_slot") or "").strip()
        if not ts:
            continue
        scheduled_time = None
        if sched.get("scheduled_time"):
            try:
                scheduled_time = time.fromisoformat(sched["scheduled_time"])
            except ValueError:
                pass
        db.session.add(
            MedicationSchedule(
                medication_id=med.id,
                time_slot=ts,
                scheduled_time=scheduled_time,
                dose_qty=sched.get("dose_qty", 1.0),
            )
        )

    db.session.commit()
    logger.info(f"✓ 新增用藥: {name} (med_id={med.id}, user={user_id})")
    return jsonify({"success": True, "medication": med.to_dict()}), 201


@medications_bp.route("/medications/<int:med_id>", methods=["GET"])
@jwt_required()
def get_medication(med_id):
    user_id = int(get_jwt_identity())
    med = Medication.query.filter_by(id=med_id, user_id=user_id).first()
    if not med:
        return jsonify({"success": False, "error": "用藥紀錄不存在"}), 404
    return jsonify({"success": True, "medication": med.to_dict()}), 200


@medications_bp.route("/medications/<int:med_id>", methods=["PUT"])
@jwt_required()
def update_medication(med_id):
    user_id = int(get_jwt_identity())
    med = Medication.query.filter_by(id=med_id, user_id=user_id).first()
    if not med:
        return jsonify({"success": False, "error": "用藥紀錄不存在"}), 404

    data = request.get_json(silent=True) or {}
    for field in (
        "name",
        "dosage",
        "unit",
        "frequency",
        "duration_days",
        "stock_qty",
        "note",
    ):
        if field in data:
            setattr(med, field, data[field])

    if "is_active" in data:
        med.is_active = bool(data["is_active"])
    if "start_date" in data:
        try:
            med.start_date = date.fromisoformat(data["start_date"])
        except ValueError:
            return jsonify({"success": False, "error": "start_date 格式錯誤"}), 400
    if "end_date" in data:
        med.end_date = (
            date.fromisoformat(data["end_date"]) if data["end_date"] else None
        )

    # 若有 schedules 則全部替換
    if "schedules" in data:
        MedicationSchedule.query.filter_by(medication_id=med.id).delete()
        for sched in data["schedules"]:
            ts = (sched.get("time_slot") or "").strip()
            if not ts:
                continue
            scheduled_time = None
            if sched.get("scheduled_time"):
                try:
                    scheduled_time = time.fromisoformat(sched["scheduled_time"])
                except ValueError:
                    pass
            db.session.add(
                MedicationSchedule(
                    medication_id=med.id,
                    time_slot=ts,
                    scheduled_time=scheduled_time,
                    dose_qty=sched.get("dose_qty", 1.0),
                )
            )

    db.session.commit()
    return jsonify({"success": True, "medication": med.to_dict()}), 200


@medications_bp.route("/medications/<int:med_id>", methods=["DELETE"])
@jwt_required()
def delete_medication(med_id):
    user_id = int(get_jwt_identity())
    med = Medication.query.filter_by(id=med_id, user_id=user_id).first()
    if not med:
        return jsonify({"success": False, "error": "用藥紀錄不存在"}), 404

    db.session.delete(med)
    db.session.commit()
    return jsonify({"success": True, "message": "用藥紀錄已刪除"}), 200


# ============================================
# S1-7  Adherence Logs（服藥紀錄）
# ============================================


@medications_bp.route("/adherence", methods=["POST"])
@jwt_required()
def log_adherence():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "缺少 JSON body"}), 400

    medication_id = data.get("medication_id")
    status = (data.get("status") or "").strip()
    if not medication_id or status not in ("taken", "skipped", "late"):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "medication_id 和 status(taken/skipped/late) 為必填",
                }
            ),
            400,
        )

    # 確認用藥屬於此 user
    med = Medication.query.filter_by(id=medication_id, user_id=user_id).first()
    if not med:
        return jsonify({"success": False, "error": "用藥紀錄不存在"}), 404

    try:
        sched_date = date.fromisoformat(
            data.get("scheduled_date", date.today().isoformat())
        )
    except ValueError:
        return jsonify({"success": False, "error": "scheduled_date 格式錯誤"}), 400

    taken_at = None
    if status in ("taken", "late"):
        taken_at = datetime.utcnow()

    log = AdherenceLog(
        user_id=user_id,
        medication_id=medication_id,
        schedule_id=data.get("schedule_id"),
        status=status,
        taken_at=taken_at,
        scheduled_date=sched_date,
        note=data.get("note"),
    )
    db.session.add(log)

    # 扣減庫存
    if status == "taken" and med.stock_qty is not None and med.stock_qty > 0:
        med.stock_qty = max(0, med.stock_qty - 1)

    db.session.commit()
    return jsonify({"success": True, "log": log.to_dict()}), 201


@medications_bp.route("/adherence", methods=["GET"])
@jwt_required()
def list_adherence():
    """取得服藥紀錄（依日期範圍）"""
    user_id = int(get_jwt_identity())
    start = request.args.get("start")
    end = request.args.get("end")
    medication_id = request.args.get("medication_id", type=int)

    q = AdherenceLog.query.filter_by(user_id=user_id)
    if medication_id:
        q = q.filter_by(medication_id=medication_id)
    if start:
        try:
            q = q.filter(AdherenceLog.scheduled_date >= date.fromisoformat(start))
        except ValueError:
            pass
    if end:
        try:
            q = q.filter(AdherenceLog.scheduled_date <= date.fromisoformat(end))
        except ValueError:
            pass

    logs = q.order_by(AdherenceLog.scheduled_date.desc()).all()
    return jsonify({"success": True, "logs": [l.to_dict() for l in logs]}), 200


@medications_bp.route("/adherence/stats", methods=["GET"])
@jwt_required()
def adherence_stats():
    """服藥統計（取近 N 天遵從率）"""
    user_id = int(get_jwt_identity())
    days = request.args.get("days", 30, type=int)
    from datetime import timedelta

    since = date.today() - timedelta(days=days)

    logs = AdherenceLog.query.filter(
        AdherenceLog.user_id == user_id,
        AdherenceLog.scheduled_date >= since,
    ).all()

    total = len(logs)
    taken = sum(1 for l in logs if l.status == "taken")
    skipped = sum(1 for l in logs if l.status == "skipped")
    late = sum(1 for l in logs if l.status == "late")
    rate = round(taken / total * 100, 1) if total > 0 else 0

    return (
        jsonify(
            {
                "success": True,
                "stats": {
                    "days": days,
                    "total": total,
                    "taken": taken,
                    "skipped": skipped,
                    "late": late,
                    "adherence_rate": rate,
                },
            }
        ),
        200,
    )


# ============================================
# S1-2  Push Token 註冊
# ============================================


@medications_bp.route("/push-token", methods=["POST"])
@jwt_required()
def register_push_token():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "缺少 JSON body"}), 400

    token = (data.get("token") or "").strip()
    platform = (data.get("platform") or "").strip().lower()

    if not token:
        return jsonify({"success": False, "error": "token 為必填"}), 400
    if platform not in ("ios", "android", "web"):
        return (
            jsonify({"success": False, "error": "platform 須為 ios/android/web"}),
            400,
        )

    # Upsert：若已存在則更新
    existing = PushToken.query.filter_by(token=token).first()
    if existing:
        existing.user_id = user_id
        existing.platform = platform
        existing.is_active = True
    else:
        db.session.add(
            PushToken(
                user_id=user_id,
                token=token,
                platform=platform,
            )
        )

    db.session.commit()
    return jsonify({"success": True, "message": "Push token 已註冊"}), 200


@medications_bp.route("/push-token", methods=["DELETE"])
@jwt_required()
def unregister_push_token():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    token = (data.get("token") or "").strip() if data else ""
    if not token:
        return jsonify({"success": False, "error": "token 為必填"}), 400

    pt = PushToken.query.filter_by(token=token, user_id=user_id).first()
    if pt:
        pt.is_active = False
        db.session.commit()

    return jsonify({"success": True, "message": "Push token 已取消"}), 200
