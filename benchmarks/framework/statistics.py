"""
Statistical Analysis Module
============================
Provides rigorous statistical utilities for multi-run benchmark analysis.
Follows standard reporting conventions used in systems benchmarking papers.
"""

import math
from typing import List, Dict, Any, Optional, Tuple


def mean(values: List[float]) -> float:
    """Arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: List[float]) -> float:
    """Median value."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]


def std_dev(values: List[float]) -> float:
    """Sample standard deviation (Bessel's correction)."""
    n = len(values)
    if n < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (n - 1)
    return math.sqrt(variance)


def coefficient_of_variation(values: List[float]) -> float:
    """Coefficient of variation (CV) as a percentage.

    CV < 5% indicates high measurement stability.
    CV > 10% suggests environmental noise or non-determinism.
    """
    m = mean(values)
    if m == 0.0:
        return 0.0
    return (std_dev(values) / abs(m)) * 100.0


def confidence_interval_95(values: List[float]) -> Tuple[float, float]:
    """95% confidence interval using the t-distribution approximation.

    For n >= 30, uses z=1.96. For smaller samples, uses a lookup table
    for common t-critical values.
    """
    n = len(values)
    if n < 2:
        m = mean(values)
        return (m, m)

    m = mean(values)
    se = std_dev(values) / math.sqrt(n)

    # t-critical values for 95% CI (two-tailed)
    t_table = {
        2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776,
        6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306,
        10: 2.262, 15: 2.145, 20: 2.093, 25: 2.064,
        30: 2.045,
    }

    if n >= 30:
        t_crit = 1.96
    else:
        # Find closest entry in the table
        closest_n = min(t_table.keys(), key=lambda k: abs(k - n))
        t_crit = t_table[closest_n]

    margin = t_crit * se
    return (m - margin, m + margin)


def remove_outliers_iqr(values: List[float], factor: float = 1.5) -> List[float]:
    """Removes statistical outliers using the Interquartile Range (IQR) method.

    Args:
        values: Raw measurement list.
        factor: IQR multiplier (1.5 = standard, 3.0 = extreme only).

    Returns:
        List with outliers removed. Never returns empty for non-empty input.
    """
    if len(values) < 4:
        return list(values)

    s = sorted(values)
    n = len(s)
    q1 = s[n // 4]
    q3 = s[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr

    filtered = [x for x in values if lower <= x <= upper]
    # Safety: never discard everything
    return filtered if filtered else list(values)


def mann_whitney_u(sample_a: List[float], sample_b: List[float]) -> Dict[str, Any]:
    """Simplified Mann-Whitney U test for two independent samples.

    Tests whether the two distributions differ significantly.
    Uses the normal approximation for n >= 8.

    Returns:
        dict with keys: u_statistic, z_score, p_value_approx, significant_at_05
    """
    na, nb = len(sample_a), len(sample_b)
    if na < 2 or nb < 2:
        return {"u_statistic": None, "z_score": None,
                "p_value_approx": None, "significant_at_05": False,
                "error": "Insufficient samples (need at least 2 per group)"}

    # Combine, rank, and split
    combined = [(val, "a") for val in sample_a] + [(val, "b") for val in sample_b]
    combined.sort(key=lambda x: x[0])

    # Assign ranks with tie handling (average rank)
    ranks: List[float] = []
    i = 0
    n = len(combined)
    while i < n:
        j = i + 1
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for _ in range(i, j):
            ranks.append(avg_rank)
        i = j

    # Sum ranks for group A
    rank_sum_a = sum(r for r, (_, grp) in zip(ranks, combined) if grp == "a")

    u_a = rank_sum_a - na * (na + 1) / 2.0
    u_b = na * nb - u_a
    u = min(u_a, u_b)

    # Normal approximation
    mu = na * nb / 2.0
    sigma = math.sqrt(na * nb * (na + nb + 1) / 12.0)

    if sigma == 0:
        return {"u_statistic": u, "z_score": 0.0,
                "p_value_approx": 1.0, "significant_at_05": False}

    z = (u - mu) / sigma

    # Two-tailed p-value approximation using the complementary error function
    p_value = math.erfc(abs(z) / math.sqrt(2))

    return {
        "u_statistic": u,
        "z_score": round(z, 4),
        "p_value_approx": round(p_value, 6),
        "significant_at_05": p_value < 0.05,
    }


class BenchmarkStatistics:
    """Aggregates multi-run measurements and produces a statistical summary.

    Usage::

        stats = BenchmarkStatistics("polars_pipeline")
        stats.add_run(duration=0.10, carbon_gco2=0.0004, energy_wh=0.0001, avg_cpu=6.7)
        stats.add_run(duration=0.11, carbon_gco2=0.0004, energy_wh=0.0001, avg_cpu=6.5)
        summary = stats.summarize()
    """

    def __init__(self, label: str):
        self.label = label
        self._durations: List[float] = []
        self._carbons: List[float] = []
        self._energies: List[float] = []
        self._cpu_usages: List[float] = []
        self._custom: Dict[str, List[float]] = {}

    def add_run(self, duration: float, carbon_gco2: float,
                energy_wh: float = 0.0, avg_cpu: float = 0.0,
                **extra_metrics: float) -> None:
        """Records metrics from a single benchmark run."""
        self._durations.append(duration)
        self._carbons.append(carbon_gco2)
        self._energies.append(energy_wh)
        self._cpu_usages.append(avg_cpu)
        for key, val in extra_metrics.items():
            self._custom.setdefault(key, []).append(val)

    @property
    def run_count(self) -> int:
        return len(self._durations)

    def _summarize_metric(self, values: List[float]) -> Dict[str, Any]:
        """Produces a full statistical summary for a single metric."""
        clean = remove_outliers_iqr(values)
        ci = confidence_interval_95(clean)
        return {
            "raw_count": len(values),
            "clean_count": len(clean),
            "outliers_removed": len(values) - len(clean),
            "mean": round(mean(clean), 10),
            "median": round(median(clean), 10),
            "std_dev": round(std_dev(clean), 10),
            "cv_pct": round(coefficient_of_variation(clean), 4),
            "ci_95_lower": round(ci[0], 10),
            "ci_95_upper": round(ci[1], 10),
            "min": round(min(clean), 10) if clean else 0,
            "max": round(max(clean), 10) if clean else 0,
        }

    def summarize(self) -> Dict[str, Any]:
        """Returns a complete statistical summary of all recorded runs."""
        result: Dict[str, Any] = {
            "label": self.label,
            "runs": self.run_count,
            "duration_s": self._summarize_metric(self._durations),
            "carbon_gco2": self._summarize_metric(self._carbons),
            "energy_wh": self._summarize_metric(self._energies),
            "avg_cpu_pct": self._summarize_metric(self._cpu_usages),
        }
        for key, vals in self._custom.items():
            result[key] = self._summarize_metric(vals)
        return result

    def compare(self, other: "BenchmarkStatistics") -> Dict[str, Any]:
        """Compares this benchmark against another using Mann-Whitney U test.

        Returns a dictionary with speedup ratios, carbon savings,
        and statistical significance results.
        """
        self_dur = remove_outliers_iqr(self._durations)
        other_dur = remove_outliers_iqr(other._durations)
        self_carbon = remove_outliers_iqr(self._carbons)
        other_carbon = remove_outliers_iqr(other._carbons)

        dur_mean_self = mean(self_dur)
        dur_mean_other = mean(other_dur)
        carbon_mean_self = mean(self_carbon)
        carbon_mean_other = mean(other_carbon)

        speedup = dur_mean_self / dur_mean_other if dur_mean_other > 0 else float("inf")
        carbon_reduction = (
            (carbon_mean_self - carbon_mean_other) / carbon_mean_self * 100
            if carbon_mean_self > 0 else 0.0
        )

        return {
            "baseline": self.label,
            "challenger": other.label,
            "speedup_ratio": round(speedup, 4),
            "carbon_reduction_pct": round(carbon_reduction, 2),
            "carbon_saved_per_run_gco2": round(carbon_mean_self - carbon_mean_other, 10),
            "duration_test": mann_whitney_u(self_dur, other_dur),
            "carbon_test": mann_whitney_u(self_carbon, other_carbon),
        }
