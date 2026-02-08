"""Pydantic schemas for request / response validation."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Shifts ─────────────────────────────────────────────────────

class ShiftOut(BaseModel):
    date: str = Field(..., examples=["2026-02-09"])
    type: str = Field(..., examples=["day8"])
    start: str = Field(..., examples=["07:00"])
    end: str = Field(..., examples=["15:00"])


class ShiftUpdate(BaseModel):
    type: str = Field(..., examples=["night12"])


# ── History ────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    id: int
    timestamp: str
    date: str
    change: Optional[str] = None
    patch: Optional[str] = None


# ── Next shift (HA) ───────────────────────────────────────────

class NextShift(BaseModel):
    date: str = Field(..., examples=["2026-02-09"])
    datetime: str = Field(..., examples=["2026-02-09T07:00"])
    type: str = Field(..., examples=["day8"])
    start: str = Field(..., examples=["07:00"])
    end: str = Field(..., examples=["15:00"])


# ── Generic ───────────────────────────────────────────────────

class MessageOut(BaseModel):
    message: str


class UndoOut(BaseModel):
    message: str
    restored_date: Optional[str] = None
