"""Application configuration."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    # SQLite file that stores recommendation history.
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "irrigation.db"))
