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
AUTHORIZATION_BASE_URL = 'https://www.fitbit.com/oauth2/authorize'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")

# MongoDB Setup
mongo_client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = mongo_client["health_data"]
panic_attacks_collection = db["panic_attacks"]
last_processed_collection = db["last_processed"]

# Threshold values for detecting panic attacks
PANIC_THRESHOLD = {
    "rmssd": 30,  # Low RMSSD indicating high physiological arousal
    "hf": 1000,  # High HF component indicating autonomic response
    "lf": 1000,  # High LF component indicating autonomic response
    "coverage": 0.9,  # Minimum coverage for reliable data
    "hr_zone_minutes": 10,  # Significant time in elevated heart rate zones
    "hr_increase": 1.5,  # 50% increase from resting heart rate
}
