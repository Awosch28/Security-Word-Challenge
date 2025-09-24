'''Config File'''
import os

# Google API Settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Flask Settings
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
DEBUG = os.getenv("FLASK_DEBUG", "True")
