from datetime import datetime
from zoneinfo import ZoneInfo

def parse_alpha_vantage_daily(payload: dict) -> list[tuple]:
    meta = payload.get("Meta Data", {})
    symbol = meta.get("2. Symbol")
    tz_name = meta.get("5. Time Zone", "US/Eastern")

    series = payload.get("Time Series (Daily)", {})
    rows = []

    for dt_str, values in series.items():
        ts = datetime.strptime(dt_str, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo(tz_name)
        )

        row = (
            ts,
            symbol,
            float(values["1. open"]),
            float(values["2. high"]),
            float(values["3. low"]),
            float(values["4. close"]),
            int(values["5. volume"]),
        )
        rows.append(row)

    return rows