"""
config.py
Central configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Flask
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Misc
    APP_NAME: str = "Academy Management System"

    # Current academic year used for roll number generation
    ACADEMIC_YEAR: int = int(os.getenv("ACADEMIC_YEAR", "2025"))

    # Default passwords used by seed script
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_PRINCIPAL_PASSWORD: str = "principal123"