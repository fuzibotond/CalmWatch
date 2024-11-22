from datetime import datetime, timedelta
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
def save_panic_attack(timestamp, metrics, criteria, reason, reason_type):
    panic_attack_record = {
        "timestamp": timestamp,
        "detected_timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "criteria": criteria,
        "panic_attack_detected": True,
        "reason": reason,
        "panic_attack_confirmed": False,
        "type": reason_type
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
                save_panic_attack(timestamp, metrics, criteria, reason="HRV analysis", reason_type="hrv_rate")


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
        hr_threshold = resting_hr * int(PANIC_THRESHOLD["hr_increase"])

        # Check if the user spent significant time in elevated HR zones
        if elevated_minutes >= int(PANIC_THRESHOLD["hr_zone_minutes"]):
            metrics = {
                "resting_hr": resting_hr,
                "elevated_minutes": elevated_minutes,
                "hr_threshold": hr_threshold
            }
            criteria = {k: v for k, v in PANIC_THRESHOLD.items() if k in metrics}
            save_panic_attack(date, metrics, criteria, reason="Heart rate zone analysis", reason_type="heart_rate_zone")

    # Check for sustained heart rate spikes using intraday data
    intraday_data = heart_rate_data.get("activities-heart-intraday", {}).get("dataset", [])
    elevated_start = None
    elevated_duration = timedelta()

    for i in range(1, len(intraday_data)):
        current_entry = intraday_data[i]
        previous_entry = intraday_data[i - 1]

        # Parse the timestamps
        current_time = datetime.strptime(current_entry['time'], "%H:%M:%S")
        previous_time = datetime.strptime(previous_entry['time'], "%H:%M:%S")

        # Calculate the difference in heart rate
        hr_increase = current_entry['value'] - previous_entry['value']

        # Check if heart rate increase meets the spike threshold
        if hr_increase >= int(PANIC_THRESHOLD["hr_spike_increase"]):
            if not elevated_start:
                elevated_start = current_time
            elevated_duration += (current_time - previous_time)
        else:
            # If heart rate is back to normal, reset elevated start and duration
            if elevated_duration >= timedelta(minutes=int(PANIC_THRESHOLD["hr_sustained_duration"])):
                metrics = {
                    "start_time": elevated_start.strftime("%H:%M:%S"),
                    "end_time": current_time.strftime("%H:%M:%S"),
                    "duration": str(elevated_duration),
                    "max_hr": current_entry['value']
                }
                criteria = {
                    "hr_spike_increase": PANIC_THRESHOLD["hr_spike_increase"],
                    "hr_sustained_duration": PANIC_THRESHOLD["hr_sustained_duration"]
                }
                save_panic_attack(date, metrics, criteria, reason="Sustained high heart rate spike",
                                  reason_type="heart_rate_spike")
            elevated_start = None
            elevated_duration = timedelta()

    # Add the last sustained panic attack if it ended with the dataset
    if elevated_duration >= timedelta(minutes=int(PANIC_THRESHOLD["hr_sustained_duration"])):
        metrics = {
            "start_time": elevated_start.strftime("%H:%M:%S"),
            "end_time": current_time.strftime("%H:%M:%S"),
            "duration": str(elevated_duration),
            "max_hr": current_entry['value']
        }
        criteria = {
            "hr_spike_increase": PANIC_THRESHOLD["hr_spike_increase"],
            "hr_sustained_duration": PANIC_THRESHOLD["hr_sustained_duration"]
        }
        save_panic_attack(date, metrics, criteria, reason="Sustained high heart rate spike",
                          reason_type="sustained_high_heart_rate_spike")


def analyze_and_store_panic_attacks(hrv_data, heart_rate_data):
    # Call both functions
    analyze_hrv_data(hrv_data)
    analyze_heart_rate_zones(heart_rate_data)
