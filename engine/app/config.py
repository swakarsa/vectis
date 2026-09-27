"""
engine/app/config.py
====================
Centralized application configuration and environment settings for Vectis Sentinel.
Zero hardcoding: all runtime defaults, URLs, and identities are dynamically resolved.
"""

import os

class Settings:
    DEFAULT_REPO: str = os.getenv("VECTIS_DEFAULT_REPO", "vectis-sentinel/release-gate")
    DEFAULT_APPROVER: str = os.getenv("VECTIS_DEFAULT_APPROVER", "security-lead@vectis.dev")
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

settings = Settings()
