"""Flask app logic"""
# Python Standard Libraries
import datetime
import json
import logging
import os
import random
import sqlite3

# logging untility
from logging.config import dictConfig

# Third-party libraries
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,  # needed for Google sign-in
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
from db import init_db_command
from user import User

# set random seed 42 for reproducibility (important to maintain stable word lists)
random.seed(42)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Use secret key to cryptographically sign cookies and other items
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive databse setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

@login_manager.user_loader
def load_user(user_id):
    '''Flask-Login helper to retrieve a user from our db'''
    return User.get(user_id)

ALLOWED_DOMAINS = {"gmail.com"} # Only allow users from these domains

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress a warning
# db = SQLAlchemy(app)

# Reverse Proxy Config
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

logging.basicConfig(level=logging.DEBUG)


#############
# Data #
#############
print("Loading data...")

# data_dir = "data/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_characters():
    '''Load Chars from Chars File.'''
    characters = set()
    characters_file = os.path.join(DATA_DIR, "characters.txt")
    try:
        with open(characters_file, "r", encoding="utf-8") as f:
            characters = [line.strip() for line in f]
        return characters
    except FileNotFoundError as e:
        app.logger.debug("Could not load characters file: %s", e)
        return ("Could not load characters file: %s", e)


language_characters = load_characters()

def load_words(characters):
    '''loads the words and does some basic QA'''
    words = []
    words_file = os.path.join(DATA_DIR, "words.txt")
    try:
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                words.append(line.strip())
    except FileNotFoundError as e:
        app.logger.debug("Could not load words file: %s", e)
        return ("Could not load words file: %s", e)

    try:
        # QA
        words = [word.lower() for word in words if word.isalpha()]
        app.logger.debug("Word list after isAlpha: %s", words)
        # remove words without correct characters
        words = [
            word
            for word in words
            if all(char in characters for char in word)
        ]
        app.logger.debug("Word list after character check: %s", words)

        # we don't want words in order, so we shuffle
        random.shuffle(words)
        app.logger.debug("Word list after shuffle: %s", words)

        return words
    except Exception as e:
        app.logger.debug("Unexpected error in load_words: %s", e)
        return ("Unexpected error when loading words: %s", e)


def load_helper_text():
    '''Load Help text'''
    lang_config_file = os.path.join(DATA_DIR, "language_config.json")
    try:
        with open(lang_config_file, "r", encoding="utf-8") as f:
            lang_config = json.load(f)
        return lang_config
    except FileNotFoundError as e:
        app.logger.debug("Could not open language config file: %s", e)
        return ("Could not open language config file: %s", e)


def load_words_supplement(characters):
    '''loads the supplemental words file if it exists'''
    words_sup_file = os.path.join(DATA_DIR, "words_supplement.txt")
    try:
        with open(words_sup_file, "r", encoding="utf-8") as f:
            supplemental_words = [line.strip() for line in f]
        supplemental_words = [
            word
            for word in supplemental_words
            if all(char in characters for char in word)
        ]
        return supplemental_words
    except FileNotFoundError as e:
        app.logger.debug("Could not open word supplement file: %s", e)
        return ("Could not open word supplement file: %s", e)


def load_language_config():
    '''Load language configuration'''
    lang_config_file = os.path.join(DATA_DIR, "language_config.json")
    try:
        with open(lang_config_file, "r", encoding="utf-8") as f:
            lang_config = json.load(f)
        return lang_config
    except FileNotFoundError as e:
        app.logger.debug("Could not open language config file: %s", e)
        return ("Could not open language config file: %s", e)


def load_keyboard():
    '''Load keyboard'''
    keyboard_file = os.path.join(DATA_DIR, "keyboard.json")
    try:
        with open(keyboard_file, "r", encoding="utf-8") as f:
            kb = json.load(f)
        return kb
    except FileNotFoundError as e:
        app.logger.debug("Could not open keyboard file: %s", e)
        return ("Could not open keyboard file: %s", e)


def get_todays_idx():
    '''Get today's index'''
    try:
        n_days = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days
        idx = n_days - 18992 + 195  # need to go back to understand this part
        return idx
    except Exception as e:
        app.logger.debug("Unexpected error in get_todays_idx: %s", e)
        return ("Unexceted error in get_todays_idx: %s", e)

def get_google_provider_cfg():
    '''Get provider configuration from Google'''
    try:
        return requests.get(GOOGLE_DISCOVERY_URL, timeout=30).json()
    except Exception as e:
        return ("Failed to retrieve Google provider configuration: %s", e)

language_words = load_words(language_characters)
language_words_supplement = load_words_supplement(language_characters)
language_config = load_language_config()
keyboard = load_keyboard()


###############################################################################
# CLASSES
###############################################################################


class Language:
    '''Holds the attributes of a language'''

    def __init__(self, word_list, word_list_supplement):
        # self.language_code = language_code
        self.word_list = word_list
        self.word_list_supplement = word_list_supplement
        # self.word_list_supplement = language_codes_5words_supplements[language_code]
        todays_idx = get_todays_idx()
        self.daily_word = word_list[todays_idx % len(word_list)]
        self.todays_idx = todays_idx
        self.config = language_config

        self.characters = language_characters
        # remove chars that aren't used to reduce bloat a bit
        """characters_used = []
        for word in self.word_list:
            characters_used += list(word)
        characters_used = list(set(characters_used))
        self.characters = [char for char in self.characters if char in characters_used]"""

        self.keyboard = keyboard
        if self.keyboard == []:  # if no keyboard defined, then use available chars
            # keyboard of ten characters per row
            for i, c in enumerate(self.characters):
                if i % 10 == 0:
                    self.keyboard.append([])
                self.keyboard[-1].append(c)
            self.keyboard[-1].insert(0, "⇨")
            self.keyboard[-1].append("⌫")

            # Deal with bottom row being too crammed:
            if len(self.keyboard[-1]) == 11:
                popped_c = self.keyboard[-1].pop(1)
                self.keyboard[-2].insert(-1, popped_c)
            if len(self.keyboard[-1]) == 12:
                popped_c = self.keyboard[-2].pop(0)
                self.keyboard[-3].insert(-1, popped_c)
                popped_c = self.keyboard[-1].pop(2)
                self.keyboard[-2].insert(-1, popped_c)
                popped_c = self.keyboard[-1].pop(2)
                self.keyboard[-2].insert(-1, popped_c)





###########
# ROUTES
###########
@app.before_request
def before_request():
    '''Before request, redirect to https'''
    app.logger.debug("BEFORE REQUEST")
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
    app.logger.debug("/")
    try:
        if current_user.is_authenticated:
            return (
                f"<p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>"
                "<div><p>Google Profile Picture:</p>"
                f'<img src="{current_user.profile_pic}" alt="Google profile pic"></img></div>'
                '<a class="button" href="/logout">Logout</a>'
            )
        else:
            return '<a class="button" href="/login">Google Login</a>'
    except Exception as e:
        app.logger.info("Error rendering index page: %s", e)
        return render_template("error.html", message=f"An unexpected error occurred: {e}"), 500


@app.route("/login")
def login():
    '''Google Account Login.'''
    # Find out what URL to hit for Google Login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    app.logger.debug("authorization_endpoint: %s", authorization_endpoint)
    app.logger.debug("request.base_url: %s", request.base_url)

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )

    app.logger.debug("request_uri: %s", request_uri)
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    '''Google Account Callback'''
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    app.logger.debug("Got the Google code: %s", code)

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    app

    app.logger.debug("token_endpoint: %s", token_endpoint)

    # Prepare and send a request to get tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    app.logger.debug("token_url: %s", token_url)
    app.logger.debug("headers: %s", headers)
    app.logger.debug("body: %s", body)


    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        timeout=30
    )

    app.logger.debug("token_response: %s", token_response)

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
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Check if the account is part of the organization
    if users_email.split("@")[-1] not in ALLOWED_DOMAINS:
        return "Access denied: you must use a company email address.", 403

    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the databse.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    '''Google Account Logout.'''
    logout_user()
    return redirect(url_for("index"))


@app.before_request
def require_login():
    '''Protect Routes by Checking Login.'''
    '''May not need this if I can use @login_required decorator'''
    if (
        "user" not in session
        and not (request.endpoint in ["login", "auth_callback", "static"])
    ):
        return redirect(url_for("login"))


# game route
@app.route("/game")
def game():
    '''Runs the game.'''
    app.logger.debug("/game")
    word_list = language_words
    word_list_supplement = language_words_supplement
    app.logger.debug("word list: %s", word_list)
    language = Language(word_list, word_list_supplement)
    app.logger.debug("daily word is: %s", language.daily_word)  # this should only be temporary
    return render_template("game.html", language=language)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, ssl_context="adhoc", debug=True)
