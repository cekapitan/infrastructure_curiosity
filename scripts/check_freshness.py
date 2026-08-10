#!/usr/bin/env python3
"""Fail when the newest weekly brief is older than the configured threshold."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def newest_brief(weekly_dir: Path) -> dt.date:
    dates: list[dt.date] = []
    for path in weekly_dir.glob("*.md"):
        match = DATE_FILE.fullmatch(path.name)
        if match:
            dates.append(dt.date.fromisoformat(match.group(1)))
    if not dates:
        raise ValueError(f"no dated weekly briefs found in {weekly_dir}")
    return max(dates)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-days", type=int, default=8)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument(
        "--weekly-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "weekly",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_age_days < 0:
        raise SystemExit("--max-age-days must not be negative")
    try:
        newest = newest_brief(args.weekly_dir)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    age = (args.today - newest).days
    if age < 0:
        raise SystemExit(f"newest weekly brief is future-dated: {newest.isoformat()}")
    if age > args.max_age_days:
        raise SystemExit(
            f"weekly brief is stale: newest={newest.isoformat()} age={age} days "
            f"limit={args.max_age_days} days"
        )
    print(f"weekly brief is current: newest={newest.isoformat()} age={age} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
