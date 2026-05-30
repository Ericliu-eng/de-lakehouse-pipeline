from __future__ import annotations

from datetime import datetime
from typing import Sequence

MarketBarRow = tuple[datetime, str, float, float, float, float, int]


def filter_new_rows(
    rows: Sequence[MarketBarRow],
    last_watermark: datetime | None,
) -> list[MarketBarRow]:
    if last_watermark is None:
        return list(rows)

    return [row for row in rows if row[0] > last_watermark]


def get_max_timestamp(rows: Sequence[MarketBarRow]) -> datetime | None:
    if not rows:
        return None
    return max(row[0] for row in rows)
