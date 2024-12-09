# app.py
from flask import Flask
from flask_cors import CORS

from routes import routes
import auth, os

app = Flask(__name__)
app.secret_key = os.urandom(24)
cors = CORS(app) # allow CORS for all domains on all routes.
app.config['CORS_HEADERS'] = 'Content-Type'
app.register_blueprint(routes)


# Authentication routes
app.add_url_rule('/login', 'login', auth.login)
app.add_url_rule('/callback', 'callback', auth.callback)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
