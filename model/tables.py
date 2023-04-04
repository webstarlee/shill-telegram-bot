from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    user_id = Column(Integer)
    chat_id = Column(String)
    token = Column(String)
    url = Column(String)
    token_symbol = Column(String)
    marketcap = Column(String)
    ath_value = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Project %r>" % self.username

class Pair(Base):
    __tablename__ = "pairs"

    id = Column(Integer, primary_key=True)
    token = Column(String)
    symbol = Column(String)
    pair_url = Column(String)
    marketcap = Column(String)
    coin_market_id = Column(Integer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Pair %r>" % self.token

class Leaderboard(Base):
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    chat_id = Column(String)
    message_id = Column(String)
    text = Column(Text)

    def __repr__(self):
        return "<Leaderboard %r>" % self.type