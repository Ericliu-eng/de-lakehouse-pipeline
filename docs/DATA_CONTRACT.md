# Market Data Contract

## Purpose

This contract defines the boundary between the Alpha Vantage daily-series
payload, typed staging rows, and the `market_bars` warehouse table. It documents
current behavior; it does not replace executable validation.

## Source Payload

The staging path expects:

- `Meta Data`.`2. Symbol`: non-empty ticker symbol;
- `Meta Data`.`5. Time Zone`: an IANA time-zone name; defaults to
  `US/Eastern` when absent;
- `Time Series (Daily)`: a mapping keyed by `YYYY-MM-DD`;
- each daily record: `1. open`, `2. high`, `3. low`, `4. close`, and
  `5. volume`.

An absent or blank symbol fails explicitly. Missing price/volume keys, invalid
dates, invalid time zones, and values that cannot be converted to their target
types also fail during staging.

## Canonical Market-Bar Row

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `ts` | timezone-aware timestamp | yes | Source date localized to the payload time zone |
| `symbol` | text | yes | Trimmed and uppercased |
| `open` | numeric | yes at staging | Convertible to `float` |
| `high` | numeric | yes at staging | Convertible to `float` |
| `low` | numeric | yes at staging | Convertible to `float` |
| `close` | numeric | yes at staging | Convertible to `float`; warehouse gate requires non-negative |
| `volume` | integer | yes at staging | Convertible to `int`; warehouse gate requires non-negative |
| `source` | text | yes | Defaults to `alpha_vantage` |

The warehouse business key is `(ts, symbol)`. Loads use upsert semantics, so a
repeat of the same business key updates the existing row instead of appending a
duplicate.

## Staging Schema Validation

The production staging path validates the canonical row before constructing a
`StagedMarketBar`. Missing or null required fields fail before database access.

## Quality and Publication

Before marts are rebuilt, the orchestrated quality gate checks non-null keys,
business-key uniqueness, non-negative close and volume, and freshness for the
active `(source, symbol)` partition.

## Compatibility Policy

- Adding an optional source field is backward-compatible.
- Adding a required field, changing a field type, changing normalization, or
  changing the business key is breaking and requires a migration plus tests.
- Source payloads remain in raw storage so transformations can be replayed.
- Unknown upstream fields may be retained in raw JSON but are ignored by the
  current typed staging model.
