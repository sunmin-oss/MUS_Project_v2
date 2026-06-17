"""
Routes 套件

集中管理所有 Blueprint，由 main.py 統一匯入。
"""

from routes.auth import auth_bp
from routes.medications import medications_bp
from routes.safety import safety_bp
from routes.consult import consult_bp

__all__ = ["auth_bp", "medications_bp", "safety_bp", "consult_bp"]
