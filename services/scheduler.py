"""
用藥提醒排程服務（S1-3 / S1-6）

使用 APScheduler 單機排程：
- 每分鐘掃描到期的用藥排程 → 觸發 mock 推播
- 每小時掃描庫存低於閾值 → 觸發補藥提醒
"""

import logging
from datetime import date, datetime, time, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# 延遲 import 避免循環依賴
_scheduler: BackgroundScheduler | None = None
_app = None


def init_scheduler(app):
    """在 Flask app context 中初始化排程器"""
    global _scheduler, _app
    _app = app

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _check_medication_reminders,
        "interval",
        minutes=1,
        id="medication_reminder",
        replace_existing=True,
    )
    _scheduler.add_job(
        _check_stock_alerts,
        "interval",
        hours=1,
        id="stock_alert",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("⏰ APScheduler 已啟動（用藥提醒 1min / 庫存檢查 1hr）")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("⏰ APScheduler 已停止")


def _check_medication_reminders():
    """掃描排程，對到期的用藥發送提醒推播"""
    if not _app:
        return

    with _app.app_context():
        from models.medication import Medication, MedicationSchedule
        from services.push_service import push_service

        now = datetime.now()
        current_time = now.time()
        today = now.date()

        # 找出 30 分鐘內到期的排程（含當前時段）
        window_start = (
            datetime.combine(today, current_time) - timedelta(minutes=1)
        ).time()
        window_end = (
            datetime.combine(today, current_time) + timedelta(minutes=30)
        ).time()

        # 取得所有活躍用藥的排程
        active_meds = Medication.query.filter(
            Medication.is_active == True,  # noqa: E712
            Medication.start_date <= today,
            (Medication.end_date >= today)
            | (Medication.end_date == None),  # noqa: E711
        ).all()

        for med in active_meds:
            for sched in med.schedules:
                if not sched.scheduled_time:
                    continue

                # 檢查是否在提醒窗口內
                if window_start <= sched.scheduled_time <= window_end:
                    push_service.send_to_user(
                        user_id=med.user_id,
                        title="用藥提醒 💊",
                        body=f"該吃 {med.name} 了（{sched.time_slot}，{sched.dose_qty} {med.unit or '份'}）",
                        data={
                            "type": "medication_reminder",
                            "medication_id": med.id,
                            "schedule_id": sched.id,
                        },
                    )


def _check_stock_alerts():
    """掃描庫存低於閾值的用藥，發送補藥提醒"""
    if not _app:
        return

    with _app.app_context():
        from models.medication import Medication
        from services.push_service import push_service

        LOW_STOCK_THRESHOLD = 5

        low_stock_meds = Medication.query.filter(
            Medication.is_active == True,  # noqa: E712
            Medication.stock_qty != None,  # noqa: E711
            Medication.stock_qty <= LOW_STOCK_THRESHOLD,
            Medication.stock_qty > 0,
        ).all()

        for med in low_stock_meds:
            push_service.send_to_user(
                user_id=med.user_id,
                title="補藥提醒 📦",
                body=f"{med.name} 庫存剩餘 {med.stock_qty} {med.unit or '份'}，請盡早補充",
                data={
                    "type": "stock_alert",
                    "medication_id": med.id,
                    "stock_qty": med.stock_qty,
                },
            )
