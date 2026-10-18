# DR Runbook Library

Disaster recovery runbooks that stay usable. Each runbook is Markdown with a metadata header, and a linter (run in CI) rejects the things that make runbooks fail at 3am: no owner, no rollback section, steps with no way to tell they worked, or a last test date older than the service's tier allows.

```
runbooks/*.md ──► rblint ──► CI fails on: missing metadata · no Verify/Rollback · step without an expected result
                    │                     · stale (last_tested beyond tier policy) · RTO looser than the BIA target
                    └──► INDEX.md: every runbook by tier, owner, RTO, last tested, days until stale
```

## Runbook format

```markdown
---
service: payments-api
scenario: Primary region unavailable
tier: 1                 # 1 = test every 90 days, 2 = 180, 3 = 365
rto: 1h
owner: payments-oncall
last_tested: 2026-09-14
---
## When to use
## Decision            ← who can authorise this, and what they need to know first
## Steps               ← numbered; each step says what you should see ("Expect: ...")
## Verify
## Rollback
```

## Usage

```bash
pip install -e ".[dev]"
rblint runbooks/                    # lint; exit 1 on errors
rblint runbooks/ --index INDEX.md   # also regenerate the index
```

## Included runbooks

| Runbook | Scenario |
|---|---|
| `payments-region-failover.md` | Primary cloud region down: promote the secondary database, shift DNS |
| `postgres-point-in-time-restore.md` | Bad migration or deletion: restore to a timestamp alongside, then cut over |
| `ransomware-recovery.md` | Encrypted hosts: isolate, verify backup integrity, rebuild clean, restore |

## Layout

```
rblint/parse.py   front matter + section parsing
rblint/rules.py   lint rules (pure functions → list of findings)
rblint/cli.py     lint + index generation
runbooks/         the library
.github/workflows/lint.yml
```
