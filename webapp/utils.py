import os 
import logging
import datetime
import json
import random

# data_dir = "data/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_characters():
    '''Load Chars from Chars File.'''
    characters = set()
    characters_file = os.path.join(DATA_DIR, "characters.txt")
    try:
        with open(characters_file, "r", encoding="utf-8") as f:
            characters = [line.strip() for line in f]
        return characters
    except FileNotFoundError as e:
        logger.debug("Could not load characters file: %s", e)
        return ("Could not load characters file: %s", e)


def load_words(characters):
    '''loads the words and does some basic QA'''
    words = []
    words_file = os.path.join(DATA_DIR, "words.txt")
    try:
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                words.append(line.strip())
    except FileNotFoundError as e:
        logger.debug("Could not load words file: %s", e)
        return ("Could not load words file: %s", e)

    try:
        # QA
        words = [word.lower() for word in words if word.isalpha()]
        logger.debug("Word list after isAlpha: %s", words)
        # remove words without correct characters
        words = [
            word
            for word in words
            if all(char in characters for char in word)
        ]
        logger.debug("Word list after character check: %s", words)

        # we don't want words in order, so we shuffle
        random.shuffle(words)
        logger.debug("Word list after shuffle: %s", words)

        return words
    except Exception as e:
        logger.debug("Unexpected error in load_words: %s", e)
        return ("Unexpected error when loading words: %s", e)


def load_helper_text():
    '''Load Help text'''
    lang_config_file = os.path.join(DATA_DIR, "language_config.json")
    try:
        with open(lang_config_file, "r", encoding="utf-8") as f:
            lang_config = json.load(f)
        return lang_config
    except FileNotFoundError as e:
        logger.debug("Could not open language config file: %s", e)
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
        logger.debug("Could not open word supplement file: %s", e)
        return ("Could not open word supplement file: %s", e)


def load_language_config():
    '''Load language configuration'''
    lang_config_file = os.path.join(DATA_DIR, "language_config.json")
    try:
        with open(lang_config_file, "r", encoding="utf-8") as f:
            lang_config = json.load(f)
        return lang_config
    except FileNotFoundError as e:
        logger.debug("Could not open language config file: %s", e)
        return ("Could not open language config file: %s", e)


def load_keyboard():
    '''Load keyboard'''
    keyboard_file = os.path.join(DATA_DIR, "keyboard.json")
    try:
        with open(keyboard_file, "r", encoding="utf-8") as f:
            kb = json.load(f)
        return kb
    except FileNotFoundError as e:
        logger.debug("Could not open keyboard file: %s", e)
        return ("Could not open keyboard file: %s", e)


def get_todays_idx():
    '''Get today's index'''
    try:
        n_days = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days
        idx = n_days - 18992 + 195  # need to go back to understand this part
        return idx
    except Exception as e:
        logger.debug("Unexpected error in get_todays_idx: %s", e)
        return ("Unexceted error in get_todays_idx: %s", e)


def get_google_provider_cfg():
    '''Get provider configuration from Google'''
    try:
        return requests.get(GOOGLE_DISCOVERY_URL, timeout=30).json()
    except Exception as e:
        return ("Failed to retrieve Google provider configuration: %s", e)
