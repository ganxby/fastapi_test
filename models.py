from sqlalchemy import Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True)
    password = Column(String)
    position = Column(String)


class Storage(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class LogBase(Base):
    __tablename__ = "log_event"

    id = Column(Integer, primary_key=True, index=True)
    event = Column(String)
    timestamp = Column(String)
