# config.py
import os
from pymongo import MongoClient

# Allow OAuthlib to use HTTP for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth and API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
VERIFICATION_CODE = os.getenv("VERIFICATION_CODE")
REDIRECT_URI = os.getenv("REDIRECT_URI")
MONGODB_URI = os.getenv("MONGODB_URI")
AUTHORIZATION_BASE_URL = 'https://www.fitbit.com/oauth2/authorize'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")


PANIC_THRESHOLD_RMSSD = os.getenv("PANIC_THRESHOLD_RMSSD")
PANIC_THRESHOLD_HF = os.getenv("PANIC_THRESHOLD_HF")
PANIC_THRESHOLD_LF = os.getenv("PANIC_THRESHOLD_LF")
PANIC_THRESHOLD_COVERAGE = os.getenv("PANIC_THRESHOLD_COVERAGE")
PANIC_THRESHOLD_HR_ZONE_MINUTES = os.getenv("PANIC_THRESHOLD_HR_ZONE_MINUTES")
PANIC_THRESHOLD_HR_INCREASE = os.getenv("PANIC_THRESHOLD_HR_INCREASE")


# Threshold values for detecting panic attacks
PANIC_THRESHOLD = {
    "rmssd": os.getenv("PANIC_THRESHOLD_RMSSD"),  # Low RMSSD indicating high physiological arousal
    "hf": os.getenv("PANIC_THRESHOLD_HF"),  # High HF component indicating autonomic response
    "lf": os.getenv("PANIC_THRESHOLD_LF"),  # High LF component indicating autonomic response
    "coverage": os.getenv("PANIC_THRESHOLD_COVERAGE"),  # Minimum coverage for reliable data
    "hr_zone_minutes": os.getenv("PANIC_THRESHOLD_HR_ZONE_MINUTES"),  # Significant time in elevated heart rate zones
    "hr_increase": os.getenv("PANIC_THRESHOLD_HR_INCREASE"),  # 50% increase from resting heart rate
    "hr_spike_increase": os.getenv("PANIC_THRESHOLD_HR_SPIKE_INCREASE"),  # Spike threshold for HR in beats per minute
    "hr_sustained_duration": os.getenv("PANIC_THRESHOLD_HR_SUSTAINED_DURATION")  # Duration in minutes for sustained elevated HR
}
