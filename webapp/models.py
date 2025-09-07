'''Language class and database tables'''
import json

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base, db_session
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
    user_id = Column(String(50), primary_key=True)
    name = Column(String(50))
    email = Column(String(120), unique=True)

    results = relationship("Result", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, user_id=user_id, name=None, email=None):
        self.user_id = user_id
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<User {self.name!r}>'

    def get_id(self):
        """Return the user's primary key as a string.
        Overrides default get_id() of UserMixin class"""
        return str(self.user_id)

    @classmethod
    def get_user(cls, user_id):
        """Return a User instance by unique ID or None if not found."""
        user = db_session.query(cls).filter(cls.user_id == user_id).first()
        logger.debug(user)
        return user

    @classmethod
    def create_user(cls, user_id, name, email):
        """Create a new user"""
        user = cls.get_user(user_id)
        if not user:
            user = cls(user_id, name, email)
            db_session.add(user)
            db_session.commit()
        return user


class Result(Base):
    '''Stores game results'''
    __tablename__ = 'results'
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    game_date_idx = Column(Integer, nullable=False)

    # Using string for num_attempts because that is what the javascript used originally
    num_attempts = Column(String(1), default="0", nullable=False)

    tiles = Column(String(200),
                    default='''[
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""]
                    ]''',
                    nullable=False)
    tile_classes = Column(String(1200),
                        default='''
                        [
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"]
                        ]''',
                        nullable=False)
    game_over = Column(Boolean, default=False, nullable=False)
    game_lost = Column(Boolean, default=False, nullable=False)
    game_won = Column(Boolean, default=False, nullable=False)

    # relationship to user
    user = relationship("User", back_populates="results")

    def __init__(self, user_id):
        self.user_id = user_id
        self.game_date_idx = get_todays_idx()
        self.num_attempts = "0"
        # stringified because that is how sqlite likes it
        self.tiles = [
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""],
                        ["", "", "", "", ""]
                        ]
        self.tile_classes = [
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"],
                            ["border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300", "border-2 border-neutral-300"]
                            ]
        self.game_over = False
        self.game_lost = False
        self.game_won = False

    def __repr__(self):
        return f'<Result {self.result_id!r}>'

    def to_dict(self):
        """Turns Result to dictionary"""
        return {
            "result_id": self.result_id,
            "user_id": self.user_id,
            "game_date_idx": self.game_date_idx,
            "num_attempts": self.num_attempts,
            "tiles": self.tiles,
            "tile_classes": self.tile_classes,
            "game_over": self.game_over,
            "game_lost": self.game_lost,
            "game_won": self.game_won,
        }

    @classmethod
    def get_result(cls, user_id):
        """Get board for user. Always pulls todays result"""
        game_date_idx = get_todays_idx()
        result =  db_session.query(cls).filter(cls.user_id == user_id).filter(cls.game_date_idx == game_date_idx).first()

        if not result:
            result = cls.create_result(user_id)

        logger.debug("get-result tiles pre-loads: %s", result.tiles)
        logger.debug("get-result tile_classes pre-loads: %s", result.tile_classes)
        logger.debug("get-result result_id: %s", result.result_id)
        logger.debug("get-result game_over: %s", result.game_over)
        logger.debug("get-result game_lost: %s", result.game_lost)
        logger.debug("get-result game_won: %s", result.game_won)
        # logger.debug("get-result emoji_board: %s", result.emoji_board)
        logger.debug("get-result attempts: %s", result.num_attempts)

        result.tiles = json.loads(result.tiles)
        result.tile_classes = json.loads(result.tile_classes)

        logger.debug("get-result tiles post-loads: %s", result.tiles)
        logger.debug("get-result tile_classes post-loads: %s", result.tile_classes)

        return result

    @classmethod
    def update_result(cls, user_id, num_attempts, tiles, tile_classes, game_over, game_lost, game_won):
        """Update result with new board, result, etc"""
        result = cls.get_result(user_id)

        logger.debug("update-result: %s", result.result_id)
        logger.debug("update-result: %s", result.game_over)
        logger.debug("update-result: %s", result.game_lost)
        logger.debug("update-result: %s", result.game_won)

        if result:
            result.num_attempts = num_attempts
            result.tiles = json.dumps(tiles)
            result.tile_classes = json.dumps(tile_classes)
            result.game_over = game_over
            result.game_lost = game_lost
            result.game_won = game_won

            db_session.commit()

        return result

    @classmethod
    def create_result(cls, user_id):
        """Create a new result. Used after first attempt is submitted"""
        result = cls(user_id)
        result.tiles = json.dumps(result.tiles)
        result.tile_classes = json.dumps(result.tile_classes)
        db_session.add(result)
        db_session.commit()
        return result
