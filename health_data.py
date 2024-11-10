from datetime import datetime
from config import PANIC_THRESHOLD, MONGODB_URI

# Connect to MongoDB
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = MONGODB_URI
# Create a new client and connect to the server
client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client["health_data"]
panic_attacks_collection = db["panic_attacks"]
last_processed_collection = db["last_processed"]


# Function to save panic attack event
def save_panic_attack(timestamp, metrics, criteria, reason):
    panic_attack_record = {
        "timestamp": timestamp,
        "detected_timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "criteria": criteria,
        "panic_attack_detected": True,
        "reason": reason,
        "panic_attack_confirmed": False
    }
    panic_attacks_collection.insert_one(panic_attack_record)
    print(f"Panic attack detected and recorded for timestamp {timestamp}:", metrics)


# Function to analyze minute-level HRV data
def analyze_hrv_data(hrv_data):
    for entry in hrv_data['hrv']:
        for minute_data in entry['minutes']:
            timestamp = minute_data['minute']
            rmssd = minute_data['value'].get('rmssd', float('inf'))
            hf = minute_data['value'].get('hf', 0)
            lf = minute_data['value'].get('lf', 0)
            coverage = minute_data['value'].get('coverage', 0)

            # Check if HRV data meets panic thresholds
            if (
                    rmssd <= PANIC_THRESHOLD["rmssd"] and
                    hf >= PANIC_THRESHOLD["hf"] and
                    lf >= PANIC_THRESHOLD["lf"] and
                    coverage >= PANIC_THRESHOLD["coverage"]
            ):
                metrics = {"rmssd": rmssd, "hf": hf, "lf": lf, "coverage": coverage}
                criteria = {k: v for k, v in PANIC_THRESHOLD.items() if k in metrics}
                save_panic_attack(timestamp, metrics, criteria, reason="HRV analysis")


# Function to analyze daily heart rate zones
def analyze_heart_rate_zones(heart_rate_data):
    for daily_data in heart_rate_data['activities-heart']:
        date = daily_data['dateTime']
        resting_hr = daily_data['value'].get("restingHeartRate", 0)

        elevated_minutes = 0
        for zone in daily_data['value'].get("heartRateZones", []):
            if zone['name'] in ["Fat Burn", "Cardio", "Peak"]:
                elevated_minutes += zone["minutes"]

        # Calculate threshold for significant heart rate increase
        hr_threshold = resting_hr * PANIC_THRESHOLD["hr_increase"]

        # Check if the user spent significant time in elevated HR zones
        if elevated_minutes >= PANIC_THRESHOLD["hr_zone_minutes"]:
            metrics = {
                "resting_hr": resting_hr,
                "elevated_minutes": elevated_minutes,
                "hr_threshold": hr_threshold
            }
            criteria = {k: v for k, v in PANIC_THRESHOLD.items() if k in metrics}
            save_panic_attack(date, metrics, criteria, reason="Heart rate zone analysis")

def analyze_and_store_panic_attacks(hrv_data, heart_rate_data):
    # Call both functions
    analyze_hrv_data(hrv_data)
    analyze_heart_rate_zones(heart_rate_data)
