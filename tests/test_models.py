"""ORM Model 煙霧測試（P0-1 DoD）"""

from models import Drug, DrugImage, NhiCache, ApiLog, db


def test_models_importable():
    assert Drug.__tablename__ == "drugs"
    assert DrugImage.__tablename__ == "drug_images"
    assert NhiCache.__tablename__ == "nhi_cache"
    assert ApiLog.__tablename__ == "api_logs"


def test_drug_query_no_error(db_session):
    """確認 SQLAlchemy 可成功 query 既有資料表"""
    count = db_session.query(Drug).count()
    assert count >= 0  # 不論有沒有資料都不該爆


def test_drug_first_row_to_dict(db_session):
    """若資料庫有資料，第一筆能正確轉成 dict"""
    drug = db_session.query(Drug).first()
    if drug is None:
        return  # 空 DB 略過
    d = drug.to_dict()
    assert "id" in d and "chinese_name" in d
    assert d["id"] == drug.id


def test_drug_images_relationship(db_session):
    """測試 drug -> images 關聯可呼叫"""
    drug = db_session.query(Drug).first()
    if drug is None:
        return
    # 不論有沒有圖片，呼叫不該爆
    imgs = drug.images.limit(3).all()
    assert isinstance(imgs, list)


def test_api_log_insert_and_query(db_session):
    """測試可寫入 api_logs 並讀回"""
    log = ApiLog(
        endpoint="/api/_test_orm",
        method="GET",
        status_code=200,
        duration_ms=12.3,
        query_params="{}",
    )
    db_session.add(log)
    db_session.commit()

    try:
        fetched = db_session.query(ApiLog).filter_by(endpoint="/api/_test_orm").first()
        assert fetched is not None
        assert fetched.status_code == 200
    finally:
        # 清理測試資料
        db_session.query(ApiLog).filter_by(endpoint="/api/_test_orm").delete()
        db_session.commit()
