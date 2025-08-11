from flask import (
    Flask,
    render_template,
    make_response,
    redirect,
    url_for,
    request,
)
from logging.config import dictConfig
import json

import datetime
import glob
import random
import logging

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

app = Flask(__name__)
app.config.from_pyfile('config.py')

logging.basicConfig(level=logging.DEBUG)


#############
# Data #
#############
print("Loading data...")

data_dir = "data/"  

# this could go in a modules file
def load_characters():
    characters = set()
    try:
        with open(f"{data_dir}words.txt", "r") as f:
            for line in f:
                characters.update(line.strip())
        with open(f"{data_dir}characters.txt", "w") as f:
            # write char per newline
            for char in characters:
                f.write(char + "\n")
        return characters
    except Exception as e:
        logging.exception("unexpected error in load_characters")
    
def load_words(characters):
    """loads the words and does some basic QA"""
    words = []
    try:
        with open(f"{data_dir}words.txt", "r") as f:
            for line in f:
                words.append(line.strip())

        # QA
        words = [word.lower() for word in words if word.isalpha()]
        # remove words without correct characters
        words = [
            word
            for word in words
            if all(char in characters for char in word)
        ]

        # we don't want words in order, so we shuffle
        random.shuffle(words)
        
        return words
    except Exception as e:
        logging.exception("Unexpected error in load_words")


def load_helper_text():
    try:
        with open(f"{data_dir}language_config.json","r") as f:
            language_config = json.load(f)
        return language_config
    except:
        return "could not load helper text"
    

def load_keyboard():
    try:
        with open(f"{data_dir}keyboard.json", "r") as f:
            keyboard = json.load(f)
        return keyboard
    except:
        logging.warning("could not load keyboard")
        return "could not load keyboard"
    

def get_todays_idx():
    try:
        n_days = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days
        idx = n_days - 18992 + 195  # need to go back to understand this part
        return idx
    except Exception as e:
        logging.exception("Unexpected error in get_todays_idx")
        return -1

###########
# ROUTES
###########


# before request, redirct to https (unless localhost)
@app.before_request
def before_request():
    app.logger.debug("BEFORE REQUEST")
    if (
        request.url.startswith("http://")
        and not "localhost" in request.url
        and not "127.0.0." in request.url
    ):
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)
    

@app.route("/")
def index():
    try:
        todays_idx=get_todays_idx()
        app.logger.info(f"Rendering index.html with todays_idx={todays_idx}")
        return render_template("index.html", todays_idx=todays_idx, message="successfully returned render template")
    except Exception as e:
        app.logger.info("Error rendering index page")
        return render_template("error.html", message="An unexpected error occurred."), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    