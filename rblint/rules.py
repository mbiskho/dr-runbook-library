from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .parse import Runbook

REQUIRED_META = ["service", "scenario", "tier", "rto", "owner", "last_tested"]
REQUIRED_SECTIONS = ["when to use", "decision", "steps", "verify", "rollback"]
TEST_EVERY_DAYS = {1: 90, 2: 180, 3: 365}
STEP = re.compile(r"^\s*\d+\.\s+(.*)$", re.M)
RTO_HOURS = {"15m": 0.25, "30m": 0.5, "1h": 1, "4h": 4, "1d": 24, "3d": 72, "1w": 168}


@dataclass
class Finding:
    level: str   # error | warning
    path: str
    message: str


def lint(rb: Runbook, today: date, bia_rto: dict[str, str] | None = None) -> list[Finding]:
    f: list[Finding] = []
    err = lambda m: f.append(Finding("error", str(rb.path), m))     # noqa: E731
    warn = lambda m: f.append(Finding("warning", str(rb.path), m))  # noqa: E731

    for k in REQUIRED_META:
        if k not in rb.meta:
            err(f"missing front-matter field '{k}'")
    for s in REQUIRED_SECTIONS:
        if not rb.sections.get(s):
            err(f"missing or empty section '## {s.title()}'")

    steps = STEP.findall(rb.sections.get("steps", ""))
    if rb.sections.get("steps") and not steps:
        err("Steps must be a numbered list")
    # Each numbered step's block (until the next step) must say what success looks like.
    blocks = re.split(r"^\s*\d+\.\s+", rb.sections.get("steps", ""), flags=re.M)[1:]
    for i, block in enumerate(blocks, start=1):
        if "expect:" not in block.lower():
            err(f"step {i} has no 'Expect:' line: how does the operator know it worked?")

    tier, tested = rb.meta.get("tier"), rb.meta.get("last_tested")
    if tier not in TEST_EVERY_DAYS:
        err("tier must be 1, 2 or 3")
    elif isinstance(tested, date):
        age = (today - tested).days
        limit = TEST_EVERY_DAYS[tier]
        if age > limit:
            err(f"last tested {age} days ago; tier {tier} requires a test every {limit} days")
        elif age > limit - 14:
            warn(f"test due within {limit - age} days")
    elif tested is not None:
        err("last_tested must be a date (YYYY-MM-DD)")

    rto = str(rb.meta.get("rto", ""))
    if rto and rto not in RTO_HOURS:
        err(f"rto {rto!r} is not one of {list(RTO_HOURS)}")
    if bia_rto and rb.meta.get("service") in bia_rto and rto in RTO_HOURS:
        target = bia_rto[rb.meta["service"]]
        if RTO_HOURS[rto] > RTO_HOURS.get(target, 1e9):
            err(f"runbook RTO {rto} is looser than the BIA target {target} for {rb.meta['service']}")
    return f


def days_until_stale(rb: Runbook, today: date) -> int | None:
    tier, tested = rb.meta.get("tier"), rb.meta.get("last_tested")
    if tier in TEST_EVERY_DAYS and isinstance(tested, date):
        return TEST_EVERY_DAYS[tier] - (today - tested).days
    return None
