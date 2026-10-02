#!/usr/bin/env python3
"""Print an inclusive UTC freshness lookback window as ISO dates.

This helper turns a lookback in days into a start/end UTC date range that
weekly radar notes and discovery records can cite. Default lookback is 30
days, matching the repository's last30days discovery window.

The module is intended as a small CLI and importable calculator. It does
not read repository files, call cloud APIs, or mutate any state.
"""

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class FreshnessWindow:
    """UTC calendar dates covering a lookback window."""

    start: dt.date
    end: dt.date
    lookback_days: int

    def inclusive_day_count(self) -> int:
        return (self.end - self.start).days + 1

    def as_iso_range(self) -> str:
        return f"{self.start.isoformat()}/{self.end.isoformat()}"


def utc_today(now: dt.datetime | None = None) -> dt.date:
    """Return today's date in UTC.

    When ``now`` is supplied it must be timezone-aware so callers cannot
    accidentally mix naive local clocks with UTC output.
    """

    moment = now or dt.datetime.now(dt.timezone.utc)
    if moment.tzinfo is None:
        raise ValueError("now must be timezone-aware when provided")
    return moment.astimezone(dt.timezone.utc).date()


def window_for(
    lookback_days: int = 30,
    *,
    end: dt.date | None = None,
    now: dt.datetime | None = None,
) -> FreshnessWindow:
    """Build a lookback window ending on ``end`` or today's UTC date.

    ``lookback_days`` is the number of days before the end date, so a
    default of 30 yields ``start = end - 30 days``. Both dates are
    calendar dates in UTC and are printed as ISO-8601 dates.
    """

    if lookback_days < 1:
        raise ValueError("lookback_days must be at least 1")
    end_date = end or utc_today(now)
    start_date = end_date - dt.timedelta(days=lookback_days)
    if start_date > end_date:
        raise ValueError("start date must not be after end date")
    return FreshnessWindow(
        start=start_date,
        end=end_date,
        lookback_days=lookback_days,
    )


def format_window(window: FreshnessWindow, *, verbose: bool = False) -> str:
    """Render the window as ``start=`` / ``end=`` ISO date lines."""

    lines = [
        f"start={window.start.isoformat()}",
        f"end={window.end.isoformat()}",
    ]
    if verbose:
        lines.extend(
            [
                f"lookback_days={window.lookback_days}",
                f"inclusive_days={window.inclusive_day_count()}",
                f"range={window.as_iso_range()}",
            ]
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print the UTC start and end ISO dates for a freshness "
            "lookback window. Default lookback is 30 days."
        )
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback window in days (default: 30). Must be at least 1.",
    )
    parser.add_argument(
        "--end",
        type=dt.date.fromisoformat,
        default=None,
        metavar="YYYY-MM-DD",
        help="Inclusive UTC end date (default: today's UTC date).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print lookback_days, inclusive day count, and ISO range.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        window = window_for(args.days, end=args.end)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(format_window(window, verbose=args.verbose))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
