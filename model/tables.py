from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    user_id = Column(Integer)
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