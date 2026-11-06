"""
EcoTrace Summary Exporters

Render the session-level dictionary returned by ``EcoTrace.get_summary()``
as human-readable reports. Values are formatted for display only; the
summary dictionary itself is never modified or rounded.
"""

import html
import re
from typing import Any, List, Optional, Tuple

MISSING = "N/A"

ENERGY_DECIMALS = 10
DURATION_DECIMALS = 4
CARBON_DECIMALS = 8


def _format_metric(value: Optional[float], decimals: int, unit: str) -> str:
    """Format a numeric metric with fixed decimals and a unit.

    ``None`` becomes ``"N/A"``; zero is a real measurement and is kept.
    """
    if value is None:
        return MISSING
    return f"{value:.{decimals}f} {unit}"


def _format_text(value: Any) -> str:
    """Return user-provided text, or ``"N/A"`` when missing or empty."""
    if value is None or value == "":
        return MISSING
    return str(value)


def _summary_rows(summary: dict) -> List[Tuple[str, str]]:
    """Build the (label, display value) rows shared by all summary formats.

    Values are unescaped; each output format applies its own escaping.
    """
    return [
        ("Run Label", _format_text(summary.get("run_label"))),
        ("Total Energy", _format_metric(
            summary.get("total_energy_kwh"), ENERGY_DECIMALS, "kWh")),
        ("Duration", _format_metric(
            summary.get("duration_s"), DURATION_DECIMALS, "s")),
        ("Total Carbon", _format_metric(
            summary.get("total_carbon_gco2"), CARBON_DECIMALS, "gCO₂eq")),
    ]


def _escape_markdown_cell(text: str) -> str:
    r"""Make text safe to place inside a single Markdown table cell.

    Backslashes are escaped before pipes; otherwise an input ``\|`` would
    become ``\\|``, which Markdown reads as a literal backslash followed by
    a column break. Line breaks become spaces because a table row must stay
    on one line.
    """
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    return re.sub(r"\r\n|\r|\n", " ", text)


def to_markdown(summary: dict) -> str:
    """Render an EcoTrace session summary as a two-column Markdown table.

    Args:
        summary: The dictionary returned by ``EcoTrace.get_summary()``.
            Missing or ``None`` values are shown as ``"N/A"``.

    Returns:
        str: A Markdown table with ``Metric`` and ``Value`` columns.

    Example:
        >>> print(to_markdown(eco.get_summary()))  # doctest: +SKIP
        | Metric | Value |
        | --- | --- |
        | Run Label | nightly-run |
        | Total Energy | 0.0000001427 kWh |
        | Duration | 0.1093 s |
        | Total Carbon | 0.00005479 gCO₂eq |
    """
    lines = ["| Metric | Value |", "| --- | --- |"]
    for label, value in _summary_rows(summary):
        lines.append(f"| {label} | {_escape_markdown_cell(value)} |")
    return "\n".join(lines) + "\n"


def to_html(summary: dict) -> str:
    """Render an EcoTrace session summary as a self-contained HTML card.

    The card is an HTML fragment (no ``<html>`` or ``<head>``) with no
    scripts, stylesheets or other external resources, so it can be embedded
    in a notebook, dashboard or email. Style it via the ``ecotrace-summary``
    class.

    Args:
        summary: The dictionary returned by ``EcoTrace.get_summary()``.
            Missing or ``None`` values are shown as ``"N/A"``.

    Returns:
        str: A ``<div class="ecotrace-summary">`` containing a table with a
        ``<th>`` label and ``<td>`` value per row. All text is HTML-escaped.
    """
    lines = [
        '<div class="ecotrace-summary">',
        "  <table>",
        "    <caption>EcoTrace Session Summary</caption>",
    ]
    for label, value in _summary_rows(summary):
        lines.append(
            f'    <tr><th scope="row">{html.escape(label)}</th>'
            f"<td>{html.escape(value)}</td></tr>"
        )
    lines += ["  </table>", "</div>"]
    return "\n".join(lines) + "\n"
