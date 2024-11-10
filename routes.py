from datetime import datetime

from bson import ObjectId
from flask import request
from auth import get_fitbit_session
from config import VERIFICATION_CODE
from health_data import analyze_and_store_panic_attacks, panic_attacks_collection
from flask import Blueprint, jsonify
from service import fetch_with_backoff, get_last_processed_date, update_last_processed_date, fetch_fitbit_data, \
    format_response

routes = Blueprint('routes', __name__)

@routes.route('/api/get-panic-attacks', methods=['GET'])
def get_panic_attacks():
    """
    Endpoint to retrieve panic attacks filtered by a date range.
    Query parameters:
    - start_date: the beginning date in YYYY-MM-DD format
    - end_date: the ending date in YYYY-MM-DD format
    """
    # Retrieve query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Prepare the query filter based on date range
    date_filter = {}
    if start_date:
        # Parse start_date into a datetime object at midnight (start of the day)
        date_filter["$gte"] = start_date
    if end_date:
        # Parse end_date into a datetime object at the end of the day
        date_filter["$lte"] = end_date

    # Only apply the date filter if start_date or end_date is specified
    query = {"date": date_filter} if date_filter else {}
    print(query)
    # Query the panic_attacks collection with the date filter
    panic_attacks = list(panic_attacks_collection.find(query, {"_id": 0}))  # Exclude the MongoDB _id field

    return jsonify({"panic_attacks": panic_attacks}), 200


@routes.route('/api/sleep-data', methods=['GET'])
def get_irregular_rhythm_notification():
    date = request.args.get('date')
    fitbit = get_fitbit_session()
    sleep_data = fetch_with_backoff(f'https://api.fitbit.com/1.2/user/-/sleep/date/{date}.json', fitbit)
    print("sleep_data", sleep_data)

    return sleep_data, 200


@routes.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Handle Fitbit verification request
    if request.method == 'GET' and 'verify' in request.args:
        if VERIFICATION_CODE == request.args.get('verify'):
            return VERIFICATION_CODE, 204
        else:
            return '', 404
    print("webhook")
    # Handle actual data from Fitbit webhook (POST requests)
    if request.method == 'POST':
        data = request.json
        print("Received Fitbit data:", data)
        fitbit = get_fitbit_session()
        last_entry = get_last_processed_date()
        today_date = datetime.today().strftime("%Y-%m-%d")
        print(last_entry)
        if last_entry is None:
            hrv_data = fetch_with_backoff(f'https://api.fitbit.com/1/user/-/hrv/date/{today_date}/all.json', fitbit)
        else:
            hrv_data = fetch_with_backoff(
                f'https://api.fitbit.com/1/user/-/hrv/date/{last_entry}/{today_date}/all.json',
                fitbit)

        print("hrv_data", hrv_data)

        heart_rate_data = fetch_with_backoff(
            f'https://api.fitbit.com/1/user/-/activities/heart/date/{last_entry}/{today_date}/1min.json', fitbit)
        print("heart_rate_data", heart_rate_data)
        update_last_processed_date(today_date)

        analyze_and_store_panic_attacks(hrv_data=hrv_data, heart_rate_data=heart_rate_data)
        return '', 204  # Confirm receipt of data



# 1. Calendar Sleep Tracker
@routes.route('/api/sleep-tracker', methods=['GET'])
def get_sleep_tracker():
    # Get the date from query parameters, or use a default date if not provided
    date = request.args.get('date', '2024-10-28')

    # Sample response data based on the requested date
    response = {
        "date": date,
        "sleep_distribution": {
            "light_sleep": 80,
            "deep_sleep": 20
        },
        "bed_time": 1729211400,  # Timestamp for "2024-10-28 01:30 AM"
        "deep_sleep_time": 21600,  # 6 hours in seconds
        "light_sleep_time": 7200,  # 2 hours in seconds
        "wake_up_time": 1729240200,  # Timestamp for "2024-10-28 09:30 AM"
        "total_sleep_time": 28800  # 8 hours in seconds
    }

    # Dummy logic to change data based on date (for example purposes)
    if date == "2024-10-29":
        response["sleep_distribution"] = {"light_sleep": 70, "deep_sleep": 30}
        response["bed_time"] = "12:30"
        response["deep_sleep_time"] = "5 hrs 30 mins"
        response["light_sleep_time"] = "2 hrs 30 mins"
        response["wake_up_time"] = "08:30 AM"
        response["total_sleep_time"] = "8 hrs 0 mins"

    return jsonify(response)


# 2. Calendar Trend (Sleep Quality)
@routes.route('/api/sleep-quality', methods=['GET'])
def get_sleep_quality():
    response = {
        "date": "2024-10-28",
        "sleep_quality": [
            {"day": "Mon", "date": "2024-10-21", "quality_percentage": 72.5},
            {"day": "Tue", "date": "2024-10-22", "quality_percentage": 78.3},
            {"day": "Wed", "date": "2024-10-23", "quality_percentage": 85.1},
            {"day": "Thu", "date": "2024-10-24", "quality_percentage": 76.0},
            {"day": "Fri", "date": "2024-10-25", "quality_percentage": 80.0}
        ],
        "average_sleep_quality": 78.4
    }
    return jsonify(response)


# 4. Heart Rate Page
@routes.route('/api/heart-rate', methods=['GET'])
def get_heart_rate():
    response = {
        "date": "2024-10-28",
        "current_bpm": 79,
        "hourly_readings": [
            {"time": "09:00 AM", "bpm": 81},
            {"time": "10:00 AM", "bpm": 64},
            {"time": "11:00 AM", "bpm": 70}
        ],
        "average_bpm_last_3_hours": 71.67
    }
    return jsonify(response)


# 5. My Profile
@routes.route('/api/profile', methods=['GET'])
def user_summary():
    try:
        sleep_data, hr_data, br_data, profile_data = fetch_fitbit_data()
        response = format_response(sleep_data, hr_data, br_data, profile_data)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes.route('/api/alert-history', methods=['GET'])
def get_alert_history():
    response = {
        "alerts": [
            {"date": "2024-10-27", "time": "07:45 AM", "message": "High heart rate detected"},
            {"date": "2024-10-26", "time": "02:30 PM", "message": "Abnormal breathing pattern"},
            {"date": "2024-10-25", "time": "11:00 PM", "message": "Potential panic attack detected"}
        ]
    }
    return jsonify(response)


@routes.route('/api/confirm-panic-attack/<string:panic_id>', methods=['PUT'])
def confirm_panic_attack(panic_id):
    try:
        # Convert the string ID to an ObjectId
        object_id = ObjectId(panic_id)
    except Exception as e:
        return jsonify({"error": "Invalid ID format"}), 400

    # Attempt to update the panic attack confirmation
    result = panic_attacks_collection.update_one(
        {"_id": object_id},
        {"$set": {"panic_attack_confirmed": True}}
    )

    # Check if any document was modified
    if result.matched_count == 0:
        return jsonify({"error": "No panic attack found with the provided ID"}), 404
    elif result.modified_count == 1:
        return jsonify({"message": "Panic attack confirmed successfully"}), 200
    else:
        return jsonify({"error": "Failed to confirm panic attack"}), 500