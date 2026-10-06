import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "sisyloan_session")
    SESSION_DURATION_HOURS = int(os.getenv("SESSION_DURATION_HOURS", "12"))
    SESSION_IDLE_MINUTES = int(os.getenv("SESSION_IDLE_MINUTES", "30"))
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
    COMPANY_ID = int(os.getenv("COMPANY_ID", "1"))