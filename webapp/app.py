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
        app.logger.debug("unexpected error in load_characters")
    

language_characters = load_characters()

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
        app.logger.debug("Unexpected error in load_words")


def load_helper_text():
    try:
        with open(f"{data_dir}language_config.json","r") as f:
            language_config = json.load(f)
        return language_config
    except:
        app.logger.debug("could not load helper text")
        return "could not load helper text"


def load_language_config():
    try:
        with open(f"{data_dir}language_config.json", "r") as f:
            language_config = json.load(f)
        return language_config
    except:
        app.logger.debug("could not load language config")
        return "could not load language config"
    

def load_keyboard():
    try:
        with open(f"{data_dir}keyboard.json", "r") as f:
            keyboard = json.load(f)
        return keyboard
    except:
        app.logger.debug("could not load keyboard")
        return "could not load keyboard"
    

def get_todays_idx():
    try:
        n_days = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days
        idx = n_days - 18992 + 195  # need to go back to understand this part
        return idx
    except Exception as e:
        app.logger.debug("Unexpected error in get_todays_idx")
        return -1

language_words = load_words(language_characters)
language_config = load_language_config()
keyboard = load_keyboard()


###############################################################################
# CLASSES
###############################################################################


class Language:
    """Holds the attributes of a language"""

    def __init__(self, word_list):  # removed lang code as input as it is not needed
        # self.language_code = language_code
        self.word_list = word_list
        # self.word_list_supplement = language_codes_5words_supplements[language_code]
        todays_idx = get_todays_idx()
        self.daily_word = word_list[todays_idx % len(word_list)]
        self.todays_idx = todays_idx
        self.config = language_config

        self.characters = language_characters
        # remove chars that aren't used to reduce bloat a bit
        characters_used = []
        for word in self.word_list:
            characters_used += list(word)
        characters_used = list(set(characters_used))
        self.characters = [char for char in self.characters if char in characters_used]

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


# before request, redirct to https (unless localhost)
@app.before_request
def before_request():
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
    app.logger.debug("/")
    try:
        todays_idx=get_todays_idx()
        app.logger.info(f"Rendering index.html with todays_idx={todays_idx}")
        return render_template("index.html", todays_idx=todays_idx, message="successfully returned render template")
    except Exception as e:
        app.logger.info("Error rendering index page")
        return render_template("error.html", message="An unexpected error occurred."), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


# game route
@app.route("/game")
def game():
    word_list = language_words
    language = Language(word_list)
    return render_template("game.html", language=language)