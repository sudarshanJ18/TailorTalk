import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

class Settings:
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    BUSINESS_START_HOUR = int(os.getenv("BUSINESS_START_HOUR", "9"))
    BUSINESS_END_HOUR = int(os.getenv("BUSINESS_END_HOUR", "17"))
    CALENDAR_ID = os.getenv("CALENDAR_ID")

    # ✅ Dynamically resolve absolute path
    GOOGLE_CREDENTIALS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "credentials",
        "credentials.json"
    )

settings = Settings()
