REQUIRED_STOCK_FIELDS = {
    "symbol",
    "ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


def validate_stock_row_schema(row: dict) -> None:
    """Validate required stock row fields before loading."""
    missing_fields = REQUIRED_STOCK_FIELDS - set(row)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing required stock fields: {missing}")