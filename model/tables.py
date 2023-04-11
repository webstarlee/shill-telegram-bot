from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    username = Column(String(200))
    user_id = Column(String(200))
    chat_id = Column(String(200))
    token = Column(String(200))
    url = Column(String(200))
    token_symbol = Column(String(200))
    marketcap = Column(String(200))
    ath_value = Column(String(200))
    status = Column(String(200), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Project %r>" % self.username

class Pair(Base):
    __tablename__ = "pairs"

    id = Column(Integer, primary_key=True)
    token = Column(String(200))
    symbol = Column(String(200))
    pair_url = Column(String(200))
    marketcap = Column(String(200))
    coin_market_id = Column(Integer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Pair %r>" % self.token

class Leaderboard(Base):
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True)
    type = Column(String(200))
    chat_id = Column(String(200))
    message_id = Column(String(200))
    text = Column(Text)

    def __repr__(self):
        return "<Leaderboard %r>" % self.type

class Advertise(Base):
    __tablename__ = "advertises"

    id = Column(Integer, primary_key=True)
    username = Column(String(200), nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    text = Column(String(200), nullable=True)
    url = Column(String(200), nullable=True)
    paid= Column(Boolean, default=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Advertise %r>" % self.username

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    hash = Column(String(200), nullable=False)
    username = Column(String(200), nullable=False)
    advertise_id = Column(Integer, nullable=False)
    address = Column(String(200), nullable=False)
    symbol = Column(String(200), nullable=False)
    quantity= Column(String(200), nullable=False)
    paid= Column(Boolean, default=False)
    complete= Column(Boolean, default=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Invoice %r>" % self.username

class Warn(Base):
    __tablename__ = "warns"

    id = Column(Integer, primary_key=True)
    username = Column(String(200), nullable=False)
    user_id = Column(String(200), nullable=False)
    chat_id = Column(String(200), nullable=False)
    count = Column(Integer, nullable=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Warn %r>" % self.username

class Ban(Base):
    __tablename__ = "bans"

    id = Column(Integer, primary_key=True)
    username = Column(String(200), nullable=False)
    user_id = Column(String(200), nullable=False)
    chat_id = Column(String(200), nullable=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Ban %r>" % self.username