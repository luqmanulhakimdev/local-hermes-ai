"""Regression evaluation comparing baseline vs current metrics with thresholds."""

from dataclasses import dataclass

VALID_REGRESSION_STATUSES = {"improved", "unchanged", "regressed", "unknown"}


@dataclass(frozen=True)
class MetricComparison:
    metric_name: str
    baseline: float | None
    current: float | None
    delta: float | None
    status: str

    def __post_init__(self):
        if self.status not in VALID_REGRESSION_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")


@dataclass(frozen=True)
class RegressionComparisonReport:
    comparisons: tuple[MetricComparison, ...]
    allowed_drop: float
    overall_status: str  # "PASS", "REGRESSION", "WARNING"

    @property
    def improved_count(self) -> int:
        return sum(1 for c in self.comparisons if c.status == "improved")

    @property
    def unchanged_count(self) -> int:
        return sum(1 for c in self.comparisons if c.status == "unchanged")

    @property
    def regressed_count(self) -> int:
        return sum(1 for c in self.comparisons if c.status == "regressed")

    @property
    def unknown_count(self) -> int:
        return sum(1 for c in self.comparisons if c.status == "unknown")


def compare_regression(
    baseline: dict[str, float | None],
    current: dict[str, float | None],
    allowed_drop: float = 0.02,
) -> RegressionComparisonReport:
    """Compare baseline and current evaluation metrics using explicit drop thresholds."""
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        raise TypeError("baseline and current must be dictionaries")
    if isinstance(allowed_drop, bool) or not isinstance(allowed_drop, (int, float)) or allowed_drop < 0:
        raise ValueError("allowed_drop must be a non-negative number")

    all_metrics = sorted(set(baseline.keys()) | set(current.keys()))
    comparisons: list[MetricComparison] = []

    for name in all_metrics:
        base_val = baseline.get(name)
        curr_val = current.get(name)

        if base_val is None or curr_val is None:
            comparisons.append(
                MetricComparison(
                    metric_name=name,
                    baseline=base_val,
                    current=curr_val,
                    delta=None,
                    status="unknown",
                )
            )
            continue

        delta = round(float(curr_val) - float(base_val), 6)
        if delta < -allowed_drop:
            status = "regressed"
        elif delta > allowed_drop:
            status = "improved"
        else:
            status = "unchanged"

        comparisons.append(
            MetricComparison(
                metric_name=name,
                baseline=float(base_val),
                current=float(curr_val),
                delta=delta,
                status=status,
            )
        )

    has_regression = any(c.status == "regressed" for c in comparisons)
    has_unknown = any(c.status == "unknown" for c in comparisons)

    if has_regression:
        overall = "REGRESSION"
    elif has_unknown:
        overall = "WARNING"
    else:
        overall = "PASS"

    return RegressionComparisonReport(
        comparisons=tuple(comparisons),
        allowed_drop=float(allowed_drop),
        overall_status=overall,
    )
