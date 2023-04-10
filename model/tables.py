from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
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
    status = Column(String, default="active")
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

class Advertise(Base):
    __tablename__ = "advertises"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    text = Column(String, nullable=True)
    url = Column(String, nullable=True)
    paid= Column(Boolean, default=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Advertise %r>" % self.username

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    hash = Column(String, nullable=False)
    username = Column(String, nullable=False)
    advertise_id = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    quantity= Column(String, nullable=False)
    paid= Column(Boolean, default=False)
    complete= Column(Boolean, default=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Invoice %r>" % self.username

class Warn(Base):
    __tablename__ = "warns"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Warn %r>" % self.username