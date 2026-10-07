from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import math
from zoneinfo import ZoneInfo


MARKET_TIME_ZONE = "America/New_York"
MAX_VOLUME = 2**63 - 1
PRICE_FIELDS = ("open", "high", "low", "close")

REQUIRED_STOCK_FIELDS = {
    "symbol",
    "ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


def market_today() -> date:
    return datetime.now(ZoneInfo(MARKET_TIME_ZONE)).date()


def parse_volume(value) -> int:
    """Accept integer values without truncation and within PostgreSQL BIGINT."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("volume must be a non-negative integer") from exc
    if (
        not number.is_finite()
        or number != number.to_integral_value()
        or not 0 <= number <= MAX_VOLUME
    ):
        raise ValueError("volume must be a non-negative integer within BIGINT range")
    return int(number)


def validate_stock_row_schema(row: dict, *, as_of: date | None = None) -> None:
    """Reject incomplete or invalid OHLCV before any warehouse write."""
    missing_fields = {
        field_name
        for field_name in REQUIRED_STOCK_FIELDS
        if field_name not in row or row[field_name] is None
    }

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing required stock fields: {missing}")

    timestamp = row["ts"]
    if not isinstance(timestamp, datetime):
        try:
            timestamp = datetime.fromisoformat(str(timestamp))
        except ValueError as exc:
            raise ValueError("ts must be a timezone-aware timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("ts must be a timezone-aware timestamp")
    if timestamp.date() > (as_of if as_of is not None else market_today()):
        raise ValueError("ts must not be a future trading date")

    prices = {}
    for field in PRICE_FIELDS:
        try:
            value = float(row[field])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field} must be a finite non-negative number") from exc
        if isinstance(row[field], bool) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{field} must be a finite non-negative number")
        prices[field] = value

    if not (
        prices["low"] <= prices["open"] <= prices["high"]
        and prices["low"] <= prices["close"] <= prices["high"]
    ):
        raise ValueError("OHLC prices must satisfy low <= open/close <= high")
    parse_volume(row["volume"])
