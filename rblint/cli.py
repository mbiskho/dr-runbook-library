from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from .parse import parse
from .rules import days_until_stale, lint


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rblint")
    ap.add_argument("folder", type=Path)
    ap.add_argument("--index", type=Path, help="write a Markdown index here")
    ap.add_argument("--bia", type=Path, help="targets.csv from the BIA toolkit (system, required_rto, ...)")
    a = ap.parse_args(argv)

    bia = None
    if a.bia:
        with a.bia.open() as fh:
            bia = {r["system"]: r["required_rto"] for r in csv.DictReader(fh) if r["required_rto"]}

    today = date.today()
    books = [parse(p) for p in sorted(a.folder.glob("*.md"))]
    errors = 0
    for rb in books:
        for f in lint(rb, today, bia):
            errors += f.level == "error"
            print(f"{f.level.upper():7} {f.path}: {f.message}")
    print(f"\n{len(books)} runbooks, {errors} errors")

    if a.index:
        rows = ["# DR runbook index", "", "| Tier | Service | Scenario | RTO | Owner | Last tested | Days until stale |",
                "|---|---|---|---|---|---|---|"]
        for rb in sorted(books, key=lambda r: (r.meta.get("tier", 9), r.meta.get("service", ""))):
            m, d = rb.meta, days_until_stale(rb, today)
            stale = "?" if d is None else (f"**overdue {-d}**" if d < 0 else str(d))
            rows.append(f"| {m.get('tier', '?')} | {m.get('service', '?')} | [{m.get('scenario', rb.path.stem)}]({rb.path.name}) "
                        f"| {m.get('rto', '?')} | {m.get('owner', '?')} | {m.get('last_tested', 'never')} | {stale} |")
        a.index.write_text("\n".join(rows) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
