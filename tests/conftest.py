"""pytest 共用 fixtures（P0-4）"""

import os
import sys

import pytest

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """提供測試用 Flask app（使用既有 drug_recognition.db）"""
    from main import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    """提供 Flask test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """提供 SQLAlchemy session（在 app context 內）"""
    from models import db

    with app.app_context():
        yield db.session
