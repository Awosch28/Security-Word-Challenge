"""Flask app logic"""
# Python Standard Libraries
import json
import logging
import os
import random

# Third-party libraries
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    # session,  # needed for Google sign-in
    request,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# used to allow the Flask app to work behind a reverse proxy
from werkzeug.middleware.proxy_fix import ProxyFix

# Internal Imports
# from db import get_db, close_connection, query_db
from utils import (
    get_google_provider_cfg,
    BASE_DIR,
    logger
)

from models import (
    Language,
    User,
    Result
)

from database import (
    db_session, 
    init_db
)

# set random seed 42 for reproducibility (important to maintain stable word lists)
random.seed(42)

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
print(f"client id: {GOOGLE_CLIENT_ID}")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
print(f"client_secret: {GOOGLE_CLIENT_SECRET}")

# Flask app setup
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Create the database
init_db()

# Use secret key to cryptographically sign cookies and other items
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

@login_manager.user_loader
def load_user(user_id):
    '''Flask-Login helper to retrieve a user from our db'''
    try:
        user = User.get_user(user_id)
        return user
    except Exception as e:
        logger.debug("Error loading user: %s", e)

ALLOWED_DOMAINS = ["gmail.com", "netskope.com"] # Only allow users from these domains

# Reverse Proxy Config
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

logging.basicConfig(level=logging.DEBUG)

@app.teardown_appcontext
def shutdown_session(exception=None):
    '''Flask will automatically remove database sessions at the end of the request or when the applicaiton shuts down'''
    db_session.remove()


###########
# ROUTES
###########
@app.before_request
def before_request():
    '''Before request, redirect to https'''
    logger.debug("BEFORE REQUEST")
    if (
        request.url.startswith("http://")
        and not "localhost" in request.url
        and not "127.0.0." in request.url
        and not "192.168.1.230" in request.url
    ):
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


@app.route("/")
def index():
    '''Prompt Users to Sign In w/ Google.'''
    logger.debug("/")
    logger.debug("current user: %s", current_user)
    try:
        if current_user.is_authenticated:
            return (
                f"<p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>"
                "<div><p>Google Profile Picture:</p>"
                '<a class="button" href="/logout">Logout</a>'
            )
        return '<a class="button" href="/login">Google Login</a>'
    except Exception as e:
        logger.info("Error rendering index page: %s", e)
        return render_template("error.html", message=f"An unexpected error occurred: {e}"), 500


@app.route("/login")
def login():
    '''Google Account Login.'''
    # Find out what URL to hit for Google Login
    google_provider_cfg = get_google_provider_cfg()
    logger.debug("google provider cfg: %s", google_provider_cfg)
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    logger.debug("authorization_endpoint: %s", authorization_endpoint)
    logger.debug("request.base_url: %s", request.base_url)

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    )

    logger.debug("request_uri: %s", request_uri)
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    '''Google Account Callback'''
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    logger.debug("Got the Google code: %s", code)

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    logger.debug("token_endpoint: %s", token_endpoint)

    # Prepare and send a request to get tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    logger.debug("token_url: %s", token_url)
    logger.debug("headers: %s", headers)
    logger.debug("body: %s", body)


    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        timeout=30
    )

    logger.debug("token_response: %s", token_response)

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens, we find and hit the URL
    # from Google that gives the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body, timeout=30)

    # Make sure their email is verified
    # The user authenticated with Google, authorized the
    # app, and now we've verified their email through Google
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Check if the account is part of the organization
    logger.debug("domain: %s", email.split("@")[-1])
    if email.split("@")[-1] not in ALLOWED_DOMAINS:
        return "Access denied: you must use a company email address.", 403
  
    user = User.create_user(unique_id, name, email)

    # Begin user session by logging the user in
    login_user(user)

    # Send user to game
    return redirect(url_for("game"))


@app.route("/logout")
@login_required
def logout():
    '''Google Account Logout.'''
    logout_user()
    return redirect(url_for("index"))


# game route
@app.route("/game")
@login_required
def game():
    '''Runs the game.'''
    logger.debug("/game")
    language = Language()
    logger.debug("daily word is: %s", language.daily_word)  # this should only be temporary
    # ... perform database operations ...
    result = Result.get_result(current_user.id)
    logger.debug("get-result: %s", result.id)
    logger.debug("get-result: %s", result.game_over)
    logger.debug("get-result: %s", result.game_lost)
    logger.debug("get-result: %s", result.game_won)

    return render_template("game.html", language=language, result=result or {
        "result.game_over": False
        }
    )

# @app.route("/update-game-state")

@app.route("/update-game-result", methods=['POST'])
def process_result():
    '''do necessary conversations, then update record'''
    data = request.get_json() # Get data sent from JavaScript
    logger.debug("update-game-result: %s", data)
    # Process data in python
    user_id = current_user.user_id
    num_attempts = data['num_attempts']
    tiles = data['tiles']
    tile_classes = data['tile_classes']
    game_over = data['game_over']
    game_lost = data['game_lost']
    game_won = data['game_won']

    return Result.update_result(user_id, num_attempts, tiles, tile_classes, game_over, game_lost, game_won)


@app.route("/get-game-result", methods=['GET'])
def get_result():
    '''get today's result for player'''
    user_id = current_user.user_id

    return Result.get_result(user_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, ssl_context="adhoc", debug=True)
