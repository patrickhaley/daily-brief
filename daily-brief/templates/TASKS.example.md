# Tasks

The file the brief syncs into and reads back out of. Plain Markdown on purpose — every tool can
read it, nothing can lock you out of it, and you can edit it faster than any app.

Three things the brief depends on:

- **Date-stamped headings.** "Gone quiet" is computed from how long an item has sat untouched, so
  every item needs a date it was added.
- **Stable section names.** The sync writes back into these headings. Rename them if you like,
  but rename them once.
- **Two optional per-item fields, for new items going forward.** `verify:` names the record that
  would prove the item closed — a ticket key, an email thread subject, a file path. An item
  carrying one gets checked against it every run; one without gets reported as unverifiable
  rather than silently carried forward. `promised:` is the date a commitment named, when it named
  one — it is what catches a slipping commitment on the day it slips, not days later. Neither
  field is retrofitted onto existing items; add them only to what you write from here on.

---

## Now

<!-- Live commitments. Something is blocked on you, or a window closes soon. -->

- [ ] Send the three validation hand-off notes — added 2026-03-10 — `PLAT-2456`
- [ ] Confirm the duplicate matching criteria before rollout — added 2026-03-09 — `PLAT-2612`
- [ ] Send the rollout partner the validation exit criteria — added 2026-03-12 — promised: 2026-03-14 — verify: sent email thread, subject "Validation exit criteria" — `PLAT-2456`

## Waiting on a date

<!-- Real, but not actionable until something else lands. Note what unblocks it. -->

- [ ] Reporting production URL — blocked on staging sync, `DATA-412` — added 2026-03-04

## Someday

<!-- Not committed to anyone. The brief leaves this alone unless it goes stale in "Now". -->

- [ ] Write up the auth migration as a runbook — added 2026-02-18

---

Closed items live in the archive file next to this one (`TASKS-archive.md` in your vault,
`TASKS-archive.example.md` here), not in this file. Check there before treating something as
still outstanding — a long "Done" list in the active file is exactly how a stale item survives
unnoticed.
