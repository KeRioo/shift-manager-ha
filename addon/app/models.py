"""SQLAlchemy models for Work Schedule."""

from sqlalchemy import Column, Text, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Shift(Base):
    """Single work-day entry."""

    __tablename__ = "shifts"

    date = Column(Text, primary_key=True, comment="YYYY-MM-DD")
    type = Column(Text, nullable=False, comment="day8 | day12 | night12")
    start = Column(Text, nullable=False, comment="HH:MM")
    end = Column(Text, nullable=False, comment="HH:MM")

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "type": self.type,
            "start": self.start,
            "end": self.end,
        }


class History(Base):
    """Audit / diff log entry."""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Text, nullable=False, comment="ISO-8601")
    date = Column(Text, nullable=False, comment="affected date")
    patch = Column(Text, nullable=False, comment="JSON Patch string")
    description = Column(Text, nullable=True, comment="human-readable change")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "date": self.date,
            "patch": self.patch,
            "description": self.description,
        }


class Meta(Base):
    """Key-value store for internal metadata."""

    __tablename__ = "meta"

    key = Column(Text, primary_key=True)
    value = Column(Text, nullable=True)
