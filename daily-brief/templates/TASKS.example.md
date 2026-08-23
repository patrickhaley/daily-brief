# Tasks

The file the brief syncs into and reads back out of. Plain Markdown on purpose — every tool can
read it, nothing can lock you out of it, and you can edit it faster than any app.

Two things the brief depends on:

- **Date-stamped headings.** "Gone quiet" is computed from how long an item has sat untouched, so
  every item needs a date it was added.
- **Stable section names.** The sync writes back into these headings. Rename them if you like,
  but rename them once.

---

## Now

<!-- Live commitments. Something is blocked on you, or a window closes soon. -->

- [ ] Send the three validation hand-off notes — added 2026-03-10 — `PLAT-2456`
- [ ] Confirm the duplicate matching criteria before rollout — added 2026-03-09 — `PLAT-2612`

## Waiting on a date

<!-- Real, but not actionable until something else lands. Note what unblocks it. -->

- [ ] Reporting production URL — blocked on staging sync, `DATA-412` — added 2026-03-04

## Someday

<!-- Not committed to anyone. The brief leaves this alone unless it goes stale in "Now". -->

- [ ] Write up the auth migration as a runbook — added 2026-02-18

## Done

<!-- The sync moves items here only when a source proves it closed: a ticket status, a sent
     reply, an action item marked done, a signed file. Never on your say-so alone. -->

- [x] Approve the Support Specialist offer — closed 2026-03-11 — email sent
