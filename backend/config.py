import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# DEBUG_GPT (legacy) removed, use ENABLE_GPT
ENABLE_GPT = os.getenv("ENABLE_GPT", "false").lower() in ("1","true","yes")

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")