# Retry parameters
import time

from auth import get_fitbit_session
from health_data import last_processed_collection

MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # initial backoff in seconds


def get_last_processed_date():
    last_entry = last_processed_collection.find_one({"type": "last_processed_date"})
    return last_entry["date"] if last_entry else None


def update_last_processed_date(date):
    try:
        last_processed_collection.update_one(
            {"type": "last_processed_date"},
            {"$set": {"date": date}},
            upsert=True)
    except Exception as e:
        print("Last processed date update fail:", e)
        return False


def fetch_with_backoff(url, fitbit_session):
    """
    Helper function to fetch data from the Fitbit API with exponential backoff.
    """
    retries = 0
    backoff = INITIAL_BACKOFF

    while retries < MAX_RETRIES:
        response = fitbit_session.get(url)
        data = response.json()

        # Check if request was successful
        if response.status_code == 200 and data.get("success", True):
            return data  # Return the successful data

        # If rate-limited, print a message and retry after a backoff period
        if response.status_code == 429 or any(
                err.get('message') == 'Too Many Requests' for err in data.get('errors', [])):
            print(f"Rate limit hit. Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2  # Exponential increase in backoff time
            retries += 1
        else:
            # Handle other errors
            print(f"Error fetching data: {data}")
            return None

    print("Max retries reached. Could not retrieve data.")
    return None


# Fetch data from Fitbit API
def fetch_fitbit_data():
    fitbit = get_fitbit_session()

    # Fetch sleep data
    sleep_response = fitbit.get("https://api.fitbit.com/1.2/user/-/sleep/date/today.json")
    sleep_data = sleep_response.json()
    print(sleep_data)

    # Fetch heart rate data
    hr_response = fitbit.get("https://api.fitbit.com/1/user/-/activities/heart/date/today/1d.json")
    hr_data = hr_response.json()
    print(hr_data)

    # Fetch breathing rate data (if available)
    br_response = fitbit.get("https://api.fitbit.com/1/user/-/br/date/today/all.json")
    br_data = br_response.json()
    print(br_data)

    profile_response = fitbit.get("https://api.fitbit.com/1/user/-/profile.json")
    profile_data = profile_response.json()
    print(profile_data)

    return sleep_data, hr_data, br_data, profile_data


# Helper function to format data
def format_response(sleep_data, hr_data, br_data, profile_data):
    # Extract sleep duration
    if 'sleep' in sleep_data and sleep_data['sleep']:
        total_sleep_seconds = sleep_data['summary']['totalMinutesAsleep'] * 60
        sleep_duration = f"{total_sleep_seconds // 3600} hrs {(total_sleep_seconds % 3600) // 60} mins"
    else:
        sleep_duration = "N/A"

    # Extract heart rate data
    resting_heart_rate = hr_data['activities-heart'][0]['value'].get('restingHeartRate', "N/A")
    heart_rate = f"{resting_heart_rate} BPM" if resting_heart_rate != "N/A" else "N/A"
    avg_breathing_rate = "N/A"
    # Extract breathing rate data
    if 'br' in br_data and br_data['br']:
        avg_breathing_rate = br_data['br'][0]['value']['breathingRate']
        breathing_rate = f"{avg_breathing_rate} BPM"
    else:
        breathing_rate = "N/A"

    # Format response
    response = {
        "username": profile_data["user"]["firstName"],
        "activity_stats": {
            "sleep": sleep_duration,
            "heart_rate": heart_rate,
            "breathing_rate": breathing_rate
        },
        "recent_activities": [
            {"type": "sleep", "duration": sleep_duration},
            {"type": "heart_rate", "bpm": resting_heart_rate},
            {"type": "breathing_rate", "bpm": avg_breathing_rate}
        ]
    }

    return response
