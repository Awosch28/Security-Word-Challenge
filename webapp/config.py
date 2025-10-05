'''Config File'''
import os
from dotenv import load_dotenv

# Allow loading values from a .env file
load_dotenv()

# Google API Settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Flask Settings
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
DEBUG = os.getenv("FLASK_DEBUG", "True")

# WSGI Settings
WSGI_X_FOR = os.getenv("WSGI_X_FOR", "0")
WSGI_X_PROTO = os.getenv("WSGI_X_PROTO", "0")
WSGI_X_HOST = os.getenv("WSGI_X_HOST", "0")
WSGI_X_PREFIX = os.getenv("WSGI_X_PREFIX", "0")

# Game Settings
ALLOWED_DOMAINS = os.getenv("ALLOWED_DOMAINS", "").split(",")
