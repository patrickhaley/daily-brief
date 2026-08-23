# content.json schema

Written fresh each morning, consumed by `build.py`. Plain text everywhere; `build.py` escapes
it. In `body` fields only, `[label](url)` becomes a link and `**bold**` becomes bold.

Anything also present in `config.json` — `vault`, `link_mode`, `slack_team`, `sources` — is
optional here and only worth setting when a single day needs to differ. `config.json` is the
place for your permanent settings.

```jsonc
{
  "date": "2026-03-12",              // drives the localStorage key and the Calendar chip
  "vault": "PersonalOS",             // optional; defaults to config.json
  "link_mode": "app",                // optional; "app" routes Slack at the desktop app, "web" keeps URLs
  "slack_team": null,                // optional; "T…" if known, deep-links Slack to the channel
  "title": "The Thursday Brief — 12 Mar 2026",   // browser tab
  "masthead": "Thursday Brief",       // rendered after the italic "The"
  "marg_left": "12 MAR 2026",         // rotated, left of the hero
  "marg_right": "07:00 AM",           // rotated, right of the hero
  "standfirst": "…",                  // ~25 words, italic serif under the hero
  "credit": ["line one", "line two"], // mono, right of the standfirst

  "hero": {
    "src": "https://…_min.webp",     // omit to fall back to svg / wash
    "fallback_src": "https://….png", // swapped in by onerror
    "svg": "<svg …>",                // used when src is absent (HERO=drawing)
    "nga": true,                     // optional; false drops the painting fallback (HERO=off)
    "bg_tint": "#3A4942",            // behind the wash
    "bg_b64": "…"                    // optional; defaults to hero-fallback.b64
  },

  "push": {
    "title": "…",
    "body": "… [PLAT-2456](https://…) …",
    "seed": "raw seed text, build.py wraps it",
    "srcs": ["delegated", "jira"],
    "feedback_hint": "placeholder for the feedback box"
  },

  "sections": [                      // rendered in this order, above Your day
    {
      "label": "Top to-dos",
      "sub": "Tick when done",
      "srcs": ["tasks", "gmail", "intercom"],
      "feedback_hint": "…",
      "items": [                     // [] renders "Nothing here today." Never pad.
        {
          "id": "t1",                // unique on the page; the localStorage key
          "act": "done",             // done | stale | seen — sets the Markdown heading
          "src": "TASKS.md",         // the file or system to edit when ticked
          "ref": "DATA-412",         // ticket key or line ref; dropped if it repeats the title
          "title": "≤10 words, the reader's words",
          "href": "https://… or obsidian://…",
          "tag": "34 days",          // small italic qualifier after the title
          "glyphs": ["cal", "jira"],
          "avatars": [{"i": "PN", "tint": false, "url": "https://…"}],
          "body": "25–30 words."
        }
      ]
    }
  ],

  "sources_used": ["cal","gmail","gchat","jira","github","circleback","tasks"],
  // only what this run actually read. drives the footer line. never a fixed list.

  "notices": [                       // dead sources and admitted gaps. renders above the footer.
    "**Slack** could not be reached, so mentions and DMs are not represented."
  ],

  "day_srcs": ["cal"],
  "day": [                           // the Your day rail, in time order
    {
      "t": "8:30a",                  // rail label; also "all day" / "tomorrow"
      "n": "Platform Standup",       // rail name
      "soft": false,                 // true = lighter weight (tentative, personal, context)
      "who": [{"i": "PN", "tint": false, "url": "https://…"}],
      "h": "Platform Standup — 8:30 to 9:00 AM",   // pane heading
      "p": "~25 words.",
      "seed": "raw seed text, or null for no Prep me button"
    }
  ]
}
```

**Source keys** for `srcs`, `glyphs` and `sources_used`: `tasks`, `delegated` (both vault deep
links, and both collapse to one name in the footer), `jira`, `gmail`, `gchat`, `intercom`,
`slack`, `github`, `cal`, `drive`, `circleback`. To add your own source, add an entry to `SRC`
in `build.py` (label, glyph key, fallback URL) and a matching glyph to `GLYPH`.

**Links**: pass ordinary web URLs. `build.py` rewrites Slack permalinks to open the desktop app,
and adds `target="_blank"` to every web link at render time. Never write `target` yourself.

**The `day` rail is plain text.** `t`, `n`, `h`, `p` and avatar initials are escaped when the
page inserts them, so HTML written into them renders literally rather than as markup — this is
deliberate, because these fields carry calendar titles and meeting names straight from gathered
content. `[label](url)` link syntax works in item `body` fields only, not here. Image URLs
(`hero.src`, `hero.fallback_src`, `avatars[].url`) must be `http(s)`; anything else is dropped
and the monogram or the wash shows instead.

**The hero degrades in four steps**: `hero.src`, then `hero.fallback_src`, then a painting from
`nga-paintings.json`, then the wash. Only the first two are yours to write. `build.py` picks the
painting by date and writes its own credit over `credit` when it shows, so do not describe a
painting you have not seen. `"nga": false` removes that step; `hero.svg` replaces the whole chain.

**Avatars**: pass `i` (initials) always, and `url` only where the source actually returns a real
avatar image — some do, most do not. Without a URL the monogram renders. `tint: true` gives the
darker tone, useful for telling two people apart. Initials are deliberately the default: they
keep faces and full names off a file that lives on disk.

**Sections are yours.** `build.py` renders whatever `sections` contains, in order, with the
labels you give. Rename them, reorder them, drop the ones you do not want, add your own. The
only fixed parts of the page are the masthead, Push your work forward, Your day, and Send back.

## Minimum viable content.json

Everything else is optional:

```json
{
  "date": "2026-03-13",
  "title": "The Friday Brief",
  "masthead": "Friday Brief",
  "marg_left": "13 MAR 2026",
  "marg_right": "07:00 AM",
  "standfirst": "One line on the shape of the day.",
  "hero": {},
  "push": {"title": "…", "body": "…", "seed": "…"},
  "sections": [],
  "day": []
}
```

See `examples/content-example.json` for a filled-in day that exercises every field, and
`examples/content-example-minimal.json` for the smallest useful one.
