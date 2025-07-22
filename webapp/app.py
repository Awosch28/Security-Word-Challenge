from flask import (
    Flask,
    render_template,
    make_response,
    redirect,
    url_for,
    request,
)
import json

import datetime
import glob
import random

# set random seed 42 for reproducibility (important to maintain stable word lists)
random.seed(42)

app = Flask(__name__)


#############
# Data #
#############
print("Loading data...")

data_dir = "data/"  

# this could go in a modules file
def load_characters():
    characters = set()
    with open(f"{data_dir}words.txt", "r") as f:
        for line in f:
            characters.update(line.strip())
    with open(f"{data_dir}chatacters.txt", "w") as f:
        # write char per newline
        for char in characters:
            f.write(char + "\n")
    return characters
    
def load_words(characters):
    """loads the words and does some basic QA"""
    words = []
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


def load_helper_text():
    try:
        with open(f"{data_dir}language_config.json","r") as f:
            language_config = json.load(f)
        return language_config
    except:
        return "could not helper text"
    

def load_keyboard():
    try:
        with open(f"{data_dir}keyboard.json", "r") as f:
            keyboard = json.load(f)
        return keyboard
    except:
        return []
    

def get_todays_idx():
    idx = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime(1970)
    return idx


###########
# ROUTES
###########


# before request, redirct to https (unless localhost)
@app.before_request
def before_request():
    print("BEFORE REQUEST")
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
    return render_template(
        "index.html",
        todays_idx=get_todays_idx()
    )


if __name__ == '__main__':
    app.run()
    