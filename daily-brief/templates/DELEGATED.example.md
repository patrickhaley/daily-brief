# Delegated

Things you handed to someone else and want back. This is the file behind the **Owed to you**
section, and it is the one that earns its keep — nothing else you own knows what you are waiting
for.

Every row needs all five columns. An item without an owner and a chase date is not delegated, it
is just forgotten, and the brief will say so.

Give each row a stable id (`D1`, `D2`, …). The brief cites those ids, and the Markdown you copy
back names them, so they need to survive edits.

---

## Open

| id | What | Owner | Handed over | Chase by | State |
|---|---|---|---|---|---|
| D1 | Accounting validation pass, `PLAT-2456` | Priya | 2026-02-24 | 2026-03-02 | sent, no reply yet |
| D2 | Contacts validation pass, `PLAT-2457` | *unassigned* | — | 2026-03-02 | **not yet handed over** |
| D3 | Contact merge validation, `PLAT-858` | Marco | 2026-02-24 | 2026-03-06 | blocked on staging sync, `DATA-412` |
| D4 | Deployment hardening sign-off, `PLAT-2458` | *unassigned* | — | 2026-03-02 | **not yet handed over** |

Three states the brief looks for, and what it does with each:

- **A chase date in the past** → Owed to you, with the age.
- **"not yet handed over"** → Owed to you, and framed as your problem, not theirs. This is the
  one people find uncomfortable and it is the point of the file.
- **Blocked** → Owed to you, naming the blocker, because chasing the owner will not move it.

## Returned / closed

| id | What | Owner | Returned | Note |
|---|---|---|---|---|
| D0 | Q4 usage numbers for the board pack | Lena | 2026-02-20 | came back complete, no follow-up needed |
