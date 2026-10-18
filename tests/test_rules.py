from datetime import date
from pathlib import Path

from rblint.parse import parse
from rblint.rules import lint

RUNBOOKS = Path(__file__).resolve().parents[1] / "runbooks"
GOOD = """---
service: api
scenario: x
tier: 1
rto: 1h
owner: oncall
last_tested: 2026-10-01
---
## When to use
Now.
## Decision
IC.
## Steps
1. Do the thing.
   Expect: it is done.
## Verify
Check.
## Rollback
Undo.
"""


def write(tmp_path, text):
    p = tmp_path / "rb.md"
    p.write_text(text)
    return parse(p)


def test_good_runbook_passes(tmp_path):
    assert lint(write(tmp_path, GOOD), date(2026, 11, 1)) == []


def test_missing_rollback_and_expect(tmp_path):
    text = GOOD.replace("## Rollback\nUndo.\n", "").replace("   Expect: it is done.\n", "")
    msgs = [f.message for f in lint(write(tmp_path, text), date(2026, 11, 1))]
    assert any("Rollback" in m for m in msgs) and any("Expect" in m for m in msgs)


def test_stale_by_tier(tmp_path):
    findings = lint(write(tmp_path, GOOD), date(2027, 3, 1))  # 151 days after test, tier 1 = 90
    assert any(f.level == "error" and "90 days" in f.message for f in findings)


def test_rto_looser_than_bia(tmp_path):
    findings = lint(write(tmp_path, GOOD.replace("rto: 1h", "rto: 4h")), date(2026, 11, 1), {"api": "1h"})
    assert any("BIA" in f.message for f in findings)


def test_included_runbooks_are_structurally_valid():
    for p in RUNBOOKS.glob("*.md"):
        if p.name == "INDEX.md":
            continue
        structural = [f for f in lint(parse(p), date(2026, 10, 18)) if "tested" not in f.message]
        assert structural == [], (p.name, structural)
