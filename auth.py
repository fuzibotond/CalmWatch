# auth.py
from flask import session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
from config import CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_BASE_URL, TOKEN_URL, db


def get_fitbit_oauth():
    return OAuth2Session(
        CLIENT_ID,
        redirect_uri='http://localhost:5000/callback',
        scope=[
            'sleep', 'heartrate', 'profile', 'activity', 'nutrition',
            'oxygen_saturation', 'respiratory_rate', 'settings',
            'temperature', 'weight'
        ]
    )


def get_fitbit_session():
    token_data = db["tokens"].find_one({"user": "default"})
    if not token_data:
        return None
    return OAuth2Session(CLIENT_ID, token=token_data["oauth_token"])


def login():
    fitbit = get_fitbit_oauth()
    authorization_url, state = fitbit.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state

    return redirect(authorization_url)


def callback():
    fitbit = get_fitbit_oauth()
    fitbit.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.url,
    )
    # Store token in the database instead of session for background access
    db["tokens"].update_one(
        {"user": "default"},
        {"$set": {"oauth_token": fitbit.token}},
        upsert=True
    )
    # Call create_subscription after storing the token
    create_subscription()
    return 'You have been logged in with Fitbit!'


def create_subscription():
    url = f'https://api.fitbit.com/1/user/-/apiSubscriptions/1.json'
    fitbit = get_fitbit_session()
    if not fitbit:
        return jsonify({"error": "User not logged in"}), 401

    response = fitbit.post(url)
    if response.status_code == 200:
        print("Subscription created successfully!")
    else:
        print(f"Failed to create subscription: {response.status_code} - {response.text}")
