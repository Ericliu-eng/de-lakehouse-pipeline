"""Compare close prices where two sources cover the same trading day."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

DEFAULT_TOLERANCE_PCT = 0.5


@dataclass(frozen=True)
class CloseReconciliation:
    overlap_days: int
    mismatched_days: int
    max_diff_pct: float | None
    tolerance_pct: float

    @property
    def passed(self) -> bool:
        return self.mismatched_days == 0


def reconcile_close_prices(
    candidate: dict[datetime, float],
    existing: dict[datetime, float],
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
) -> CloseReconciliation:
    """Measure how far ``candidate`` closes drift from ``existing`` closes on shared days."""
    diffs = [
        abs(candidate[ts] - existing[ts]) / existing[ts] * 100
        for ts in candidate.keys() & existing.keys()
        if existing[ts]
    ]
    return CloseReconciliation(
        overlap_days=len(diffs),
        mismatched_days=sum(diff > tolerance_pct for diff in diffs),
        max_diff_pct=round(max(diffs), 4) if diffs else None,
        tolerance_pct=tolerance_pct,
    )
