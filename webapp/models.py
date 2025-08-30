from flask_login import UserMixin
from sqlalchemy import Column, Integer, String
from database import Base
from utils import (
    get_todays_idx,
    load_language_config,
    load_characters,
    load_keyboard,
    load_words,
    load_words_supplement,
    logger
)

class Language:
    '''Holds the attributes of a language'''

    def __init__(self):
        # self.language_code = language_code
        self.characters = load_characters()
        self.word_list = load_words(self.characters)
        self.word_list_supplement = load_words_supplement(self.characters)
        # self.word_list_supplement = language_codes_5words_supplements[language_code]
        self.todays_idx = get_todays_idx()
        self.daily_word = self.word_list[self.todays_idx % len(self.word_list)]
        self.config = load_language_config()

        self.keyboard = load_keyboard()
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


class User(UserMixin, Base):
    '''Holds the attributes for a User'''
    __tablename__ = 'users'
    id = Column(String(50), primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    game_state = Column(String(120), unique=True)
    game_results = Column(String(120), unique=True)

    def __init__(self, id=id, name=None, email=None, game_state=None, game_results=None):
        self.id = id
        self.name = name
        self.email = email
        self.game_state = game_state
        self.game_results = game_results

    def __repr__(self):
        return f'<User {self.name!r}>'
    
    @classmethod
    def get_by_id(cls, db_session, id):
        """Return a User instance by unique ID or None if not found."""
        user = db_session.query(cls).filter(cls.id == id).first()
        logger.debug(user)
        return user

    @classmethod
    def create_user(cls, db_session, id, name, email):
        """Create a new user"""
        user = cls.get_by_id(db_session, id)
        if not user:
            user = cls(id, name, email, '', '')
            db_session.add(user)
            db_session.commit()
        return user

