"""Canonical stock symbols shared by ingestion and orchestration."""


def normalize_symbol(symbol: str | None) -> str:
    """Use one business key for API requests, storage, state, and quality checks."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Missing stock symbol: expected a non-empty string.")
    return symbol.strip().upper()
