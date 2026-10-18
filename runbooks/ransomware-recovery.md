---
service: corporate-it
scenario: Ransomware on servers or endpoints
tier: 1
rto: 1d
owner: security-oncall
last_tested: 2026-07-02
---
## When to use
Files are being encrypted or a ransom note is found on any company system.

## Decision
The incident commander and CISO. Legal must be involved before any contact with the attacker. Restoring before the backups are proven clean risks reinfection, so step 3 gates everything after it.

## Steps
1. Isolate: disable affected hosts' network ports in the EDR console (network containment), and block outbound traffic from affected VLANs at the firewall.
   Expect: hosts show "contained" in the EDR console; no new encryption alerts after 10 minutes.
2. Preserve evidence: snapshot affected VM disks before rebuilding anything.
   Expect: snapshot IDs recorded in the incident ticket.
3. Verify backup integrity: confirm the last backup predates the earliest intrusion indicator, and that backups are immutable (object lock) and unmodified.
   Expect: backup timestamp and immutability status recorded; security lead signs off.
4. Rebuild from known-good images, not by cleaning infected hosts.
   Expect: rebuilt hosts pass the EDR full scan.
5. Restore data from the verified backup and rotate every credential used on the affected systems.
   Expect: restore verification passes; password and key rotation completed for all listed accounts.

## Verify
- No encryption or C2 alerts for 24 hours after restore.
- Business owners confirm critical systems are usable.

## Rollback
Not applicable once isolation starts: containment is never undone until forensics clears the hosts. If a restored system shows indicators again, re-isolate it and return to step 3 with an older backup.
