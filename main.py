import datetime

from flask import Flask, redirect, request, session, jsonify
from requests_oauthlib import OAuth2Session
import os

# Allow OAuthlib to use HTTP for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session handling


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
authorization_base_url = 'https://www.fitbit.com/oauth2/authorize'
token_url = 'https://api.fitbit.com/oauth2/token'


# Define the OAuth2 session object
def get_fitbit_oauth():
    return OAuth2Session(client_id, redirect_uri='http://localhost:5000/callback',
                         scope=['sleep', 'heartrate', 'profile', 'activity', 'heartrate', 'nutrition',
                                'oxygen_saturation', 'respiratory_rate', 'settings', 'temperature', 'weight'])


# Helper function to get an authorized session
def get_fitbit_session():
    token = session.get('oauth_token')
    if not token:
        return None
    return OAuth2Session(client_id, token=token)


@app.route('/login')
def login():
    fitbit = get_fitbit_oauth()
    authorization_url, state = fitbit.authorization_url(authorization_base_url)
    # Store the state in the session to validate the callback
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    fitbit = get_fitbit_oauth()
    # Fetch the authorization response from the URL
    fitbit.fetch_token(
        token_url,
        client_secret=client_secret,
        authorization_response=request.url,
    )
    # Store token in the session for future use
    session['oauth_token'] = fitbit.token
    return 'You have been logged in with Fitbit!'


# Profile endpoint
# @app.route('/api/profile', methods=['GET'])
# def get_profile():
#     fitbit = get_fitbit_session()
#     if not fitbit:
#         return jsonify({"error": "User not logged in"}), 401
#
#     response = fitbit.get('https://api.fitbit.com/1/user/-/profile.json')
#     return jsonify(response.json())


# Sleep data endpoint with date parameter
@app.route('/api/sleep', methods=['GET'])
def get_sleep():
    fitbit = get_fitbit_session()
    if not fitbit:
        return jsonify({"error": "User not logged in"}), 401

    # Get the date from the query parameter, default to today's date if not provided
    date = datetime.date.today().strftime('%Y-%m-%d')
    url = f'https://api.fitbit.com/1.2/user/-/sleep/date/{date}.json'

    response = fitbit.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to retrieve sleep data"}), response.status_code


# 1. Calendar Sleep Tracker
@app.route('/api/sleep-tracker', methods=['GET'])
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
@app.route('/api/sleep-quality', methods=['GET'])
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


# 3. Main Page
@app.route('/api/main-page', methods=['GET'])
def get_main_page():
    response = {
        "status": "active",
        "notifications": [
            {"type": "alert", "message": "Heart rate increased significantly", "time": "08:45 AM"},
            {"type": "reminder", "message": "Time to wind down for sleep", "time": "09:00 PM"}
        ]
    }
    return jsonify(response)


# 4. Heart Rate Page
@app.route('/api/heart-rate', methods=['GET'])
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
@app.route('/api/profile', methods=['GET'])
def get_profile():
    response = {
        "username": "Kasap312",
        "activity_stats": {
            "sleep": "7 hrs",
            "heart_rate": "80 BPM",
            "breathing_rate": "23 BPM"
        },
        "recent_activities": [
            {"type": "sleep", "duration": "7 hrs"},
            {"type": "heart_rate", "bpm": 80},
            {"type": "breathing_rate", "bpm": 23}
        ]
    }
    return jsonify(response)


# 6. Alert History
@app.route('/api/alert-history', methods=['GET'])
def get_alert_history():
    response = {
        "alerts": [
            {"date": "2024-10-27", "time": "07:45 AM", "message": "High heart rate detected"},
            {"date": "2024-10-26", "time": "02:30 PM", "message": "Abnormal breathing pattern"},
            {"date": "2024-10-25", "time": "11:00 PM", "message": "Potential panic attack detected"}
        ]
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
