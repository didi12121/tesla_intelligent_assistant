from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def now() -> datetime:
    return datetime.now()


def compute_expires_at(expires_in: Optional[int]) -> Optional[datetime]:
    if not expires_in:
        return None
    return now() + timedelta(seconds=int(expires_in))


def to_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, DATETIME_FMT)
    raise TypeError(f"Unsupported datetime value type: {type(value)}")
