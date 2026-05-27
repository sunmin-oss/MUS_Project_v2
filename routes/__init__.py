"""
Routes 套件

集中管理所有 Blueprint，由 main.py 統一匯入。
"""

from routes.auth import auth_bp

__all__ = ["auth_bp"]
