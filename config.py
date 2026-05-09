import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Mauricec95/superset")
GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]

DEVIN_API_KEY = os.environ["DEVIN_API_KEY"]
DEVIN_API_BASE = os.environ.get("DEVIN_API_BASE", "https://api.devin.ai/v1")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "30"))
DEVIN_TRIGGER_LABEL = os.environ.get("DEVIN_TRIGGER_LABEL", "devin-fix")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/sessions.db")
