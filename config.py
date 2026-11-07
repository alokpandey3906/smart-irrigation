"""Application configuration."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    # Vercel functions can only write to /tmp; local installs use instance/.
    default_database = os.path.join("/tmp", "irrigation.db") if os.environ.get("VERCEL") else os.path.join(BASE_DIR, "instance", "irrigation.db")
    DATABASE = os.environ.get("DATABASE", default_database)
