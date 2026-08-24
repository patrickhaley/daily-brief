# The scheduled task prompt

Paste this into the scheduled task. It stays short on purpose: the design and the rules live in
`SPEC.md`, so the task never has to re-derive them and the brief cannot drift when you change
your mind about a section.

Replace the one path if your vault is laid out differently. If your harness does not resolve
vault-relative paths reliably, make it absolute — the run should never spend a step working out
where the package lives.

```
Read Routines/daily-brief/SPEC.md in my vault first and follow it exactly. It is
the source of truth for this task and it supersedes anything you might assume from
the task's name. Read content.schema.md and findings.schema.md in the same folder
before writing anything.

Delegate Phase 1 to a subagent per SPEC.md, then do Phase 2 yourself in this
session once it returns.

Write content.json against content.schema.md, render it with build.py, screenshot
the result and look at the image before you deliver it.

Save it as a new dated file. Never overwrite a previous brief.

Then push me a notification naming the file and the sharpest item in it, and reply
with two or three sentences: the filename, the sharpest item, and anything a dead
source or the sync could not confirm.

Nobody is watching when this fires, so do not ask questions. Where the spec leaves
a judgment call, make it, and note the call in your reply.
```

## Schedule

Weekdays, early enough to finish before you start. The run takes a while and reads a lot, so
give it a head start — a 7:00 AM slot for a 8:00 AM start is about right.

Set the timezone in `config.json` as well as on the task itself; the brief reads the calendar in
the reader's timezone and the two disagreeing is a confusing bug to chase.

## Opening it automatically

The brief is worth more when you do not have to go and get it. Add the output folder's newest
file to your login items, or point a startup tab at it. A brief you have to remember to open is a
brief you read twice a week.

On macOS, a login item that opens the newest brief:

```sh
open "$(ls -t ~/Documents/PersonalOS/Work/Briefs/brief-*.html | head -1)"
```
