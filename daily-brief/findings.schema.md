# findings.json schema

Written fresh each morning by the Phase 1 subagent, at `{paths.briefs}/findings-YYYY-MM-DD.json`.
Read once, by Phase 2 in the orchestrating session, to build `content.json` without re-deriving
research the subagent already did. Never rendered, never shown to the reader.

Plain text everywhere, same rule as `content.json`: nothing here is HTML, and `[label](url)` /
`**bold**` are not expanded — Phase 2 does that when it writes the real item body.

```jsonc
{
  "date": "2026-03-12",

  "candidates": [                       // over-inclusive; Phase 2 selects, re-verifies, writes body copy
    {
      "for_section": "gone_quiet",      // hint only: push | top_todos | new_updates | owed_to_you | gone_quiet
      "title": "≤10 words, the reader's words",
      "ref": "PLAT-2456",               // ticket key or line ref, as content.schema.md's item.ref
      "href": "https://… or obsidian://…",
      "tag": "34 days",
      "glyphs": ["jira"],
      "verify": "PLAT-2456 status",     // the record checked, or still owed checking — never invented
      "promised": "2026-03-01",         // optional; only when a dated commitment was named
      "rationale": "one line: why this qualifies, and what was cross-referenced to confirm it"
    }
  ],

  "day_candidates": [                   // same shape as content.schema.md's day rail; Phase 2 may use as-is
    {
      "t": "8:30a",
      "n": "Platform Standup",
      "soft": false,
      "h": "Platform Standup — 8:30 to 9:00 AM",
      "p": "~25 words.",
      "seed": "raw seed text, or null"
    }
  ],

  "source_health": [                    // what Phase 1 tried, so Phase 2 never re-probes a source
    {
      "source": "slack",
      "status": "ok",                   // ok | degraded | dead
      "tried": "what it was meant to cover",
      "failure": null,                  // auth | timeout | empty | permission | null
      "control_query": "PLAT-2456",     // the known-good query run before declaring it dead, if any
      "control_result": "ok"            // ok | failed | not_run
    }
  ],

  "notes": [                            // free-text things Phase 2 should know that don't fit above
    "the meeting-notes reconciliation pass found no glaring item to promote this morning"
  ]
}
```

**`candidates[].verify` and `.rationale` exist so Phase 2 does not re-open a ticket or thread the
subagent already opened.** Verify before you list in `SPEC.md` still applies to what makes the
final page — Phase 2 starts from the subagent's finding rather than from nothing, it does not
skip verification because the finding exists.

**`source_health` is the only place a control-query result survives.** `content.json`'s
`notices` field is derived from this, in Phase 2's own words, once selection is done — do not
copy this array into `content.json` verbatim.
