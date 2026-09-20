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
    missing_fields = {
    field_name
    for field_name in REQUIRED_STOCK_FIELDS
    if field_name not in row or row[field_name] is None
}

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing required stock fields: {missing}")