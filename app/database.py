"""SQLModel persistence: no textual SQL or client-controlled owner fields."""
from contextlib import contextmanager
from functools import lru_cache
from uuid import uuid4
from sqlmodel import Field, Session, SQLModel, create_engine, select
from app.config import database_path


class User(SQLModel, table=True):
    __tablename__ = "users"
    username: str = Field(primary_key=True)
    password_hash: str
    active: bool = True


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner: str = Field(foreign_key="users.username", index=True)
    destination: str
    status: str = "requested"


@lru_cache(maxsize=8)
def engine_for(path: str):
    return create_engine("sqlite:///" + path, connect_args={"check_same_thread": False, "timeout": 5},
                         hide_parameters=True)


@contextmanager
def connect():
    with Session(engine_for(database_path())) as session:
        yield session


def initialize():
    SQLModel.metadata.create_all(engine_for(database_path()))


def find_user(username: str):
    with connect() as session:
        return session.exec(select(User).where(User.username == username)).first()


def add_user(username: str, hashed: str):
    with connect() as session:
        session.add(User(username=username, password_hash=hashed))
        session.commit()
