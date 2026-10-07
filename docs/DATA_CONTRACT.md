# Market Data Contract

## Purpose

This contract defines the boundary between Alpha Vantage and Tiingo source
payloads, typed staging rows, and the `market_bars` warehouse table. It documents
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

Tiingo history expects a list of records with `date`, `open`, `high`, `low`,
`close`, and `volume`, plus the requested symbol. Its UTC-midnight date label
is preserved as a calendar date and localized to US/Eastern midnight, matching
the daily warehouse grain. Both sources load unadjusted OHLCV.

## Canonical Market-Bar Row

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `ts` | timezone-aware timestamp | yes | Localized source trading date; no later than the current New York market date |
| `symbol` | text | yes | Trimmed and uppercased |
| `open` | numeric | yes at staging | Finite, non-negative; between low and high |
| `high` | numeric | yes at staging | Finite, non-negative; at least low, open, and close |
| `low` | numeric | yes at staging | Finite, non-negative; at most high, open, and close |
| `close` | numeric | yes at staging | Finite, non-negative; between low and high |
| `volume` | integer | yes at staging | Integral value from 0 through 2^63 - 1; no truncation |
| `source` | text | yes | `alpha_vantage` or `tiingo` on the supported paths |

The warehouse business key is `(ts, symbol)`. Daily writes use upserts after
watermark filtering. Routine reruns skip existing timestamps; the default
date-range backfill fills missing dates. Tiingo history uses insert-only
semantics and does not overwrite existing daily rows. None of these commands
currently forces correction of existing historical prices.

## Staging Schema Validation

The production staging path validates the canonical row before constructing a
`StagedMarketBar`. Missing/null fields, NaN/Infinity, negative or inconsistent
OHLC prices, fractional/overflow volume, and future dates fail before database
access and therefore cannot advance the watermark.

## Quality and Publication

Before marts are built, both the manual CLI and orchestrated paths check
warehouse keys and OHLCV integrity, including data written outside staging.
Daily orchestration additionally requires 0–14 day freshness for the active
`(source, symbol)` partition. Historical manual publication does not impose a
freshness requirement. The supported execution model is serial local runs.

## Compatibility Policy

- Adding an optional source field is backward-compatible.
- Adding a required field, changing a field type, changing normalization, or
  changing the business key is breaking and requires a migration plus tests.
- Source payloads remain in raw storage so transformations can be replayed.
- Unknown upstream fields may be retained in raw JSON but are ignored by the
  current typed staging model.
