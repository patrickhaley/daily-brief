# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **template** for a self-building morning briefing. There is no app and no server: a scheduled
Claude task reads the reader's connected sources plus two local Markdown files, writes a
`content.json`, and `build.py` renders it into one self-contained dated HTML file.

The repository ships only generic, fictional content. Everything account-specific lives in
`daily-brief/config.json` (gitignored; `config.json.example` is the shareable copy).

## Commands

Python 3, standard library only. No dependencies, no build step, no test suite.

```sh
cd daily-brief

# render the fully-exercised example (the smoke test for any change to build.py or shell.html)
python3 build.py examples/content-example.json /tmp/brief.html && open /tmp/brief.html

# render the smallest valid content.json — catches missing-key regressions
python3 build.py examples/content-example-minimal.json /tmp/brief-min.html
```

`build.py` raises `SystemExit: unfilled slots: [...]` if any `{{SLOT}}` or `__TOKEN__` survives
substitution, so a successful render is the pass condition. The example hero URL deliberately
404s — falling back to the blurred wash is correct, not a bug.

## Architecture

### Three files, three jobs

| File | Lifetime | Owner |
|---|---|---|
| `config.json` | edited once | the reader — vault name, timezone, source URLs, palette |
| `content.json` | written fresh every morning | the scheduled run; contract in `content.schema.md` |
| `shell.html` | rarely touched | the design — all CSS and all browser JS |

`build.py` is pure substitution: it reads `shell.html`, replaces `{{SLOT}}` placeholders and
`__G_*__` / `__FONT_B64__` tokens, and writes one file. Adding a slot to `shell.html` without
adding it to the `slots` dict in `build()` is a hard failure, by design.

**Precedence:** `content.json` wins over `config.json`, which wins over the `DEFAULT_*` constants
in `build.py` — see `pick()` in `build()`. An explicit `null` in `content.json` falls through to
`config.json` rather than meaning "unset".

### Where behaviour is defined, and where it is not

`task-prompt.md` is eight lines and says little more than "read `SPEC.md` and follow it". That is
deliberate: the run must not re-derive the design every morning. So:

- **Run behaviour, switches, and the rules that stop the brief being wrong → `SPEC.md`.**
  Edit this, not the task prompt.
- **The shape of `content.json` → `content.schema.md`.**
- **Layout, palette, browser behaviour → `shell.html` + `theme` in `config.json`.**

`SPEC.md` describes a two-phase run: Phase 1 syncs the reader's tasks and delegated Markdown
files, Phase 2 builds the page. Phase 1 is the only thing in the whole run permitted to write
outside the output folder; every other source is read-only.

### Adding a source

Three coordinated edits: an entry in `SRC` in `build.py` (label, glyph key, fallback URL), a
matching 24×24 SVG in `GLYPH`, and a line in `SPEC.md` saying what to gather from it. The new key
is then usable in `srcs`, `glyphs` and `sources_used`. Sources with no sensible default
(`jira`, `intercom`) are `None` in `SRC` and render as an unlinked chip.

`footer_sources()` collapses `tasks` + `delegated` into one reader-facing name, and the footer is
generated from `sources_used` alone — never a fixed list, so a dead source disappears from it
automatically.

### Sections are data

`build.py` renders whatever `sections` contains, in the order given, with the labels given. Only
the masthead, Push your work forward, Your day, and Send back are fixed. Do not hard-code a
section name in `build.py`.

## Invariants worth knowing before editing

**Everything gathered is hostile.** Two separate escaping layers, and both matter:

- Server-side: `e()` (`html.escape`) on every item field, `safe_url()` restricting image URLs to
  `http(s)`, and `jslit()` — which is `json.dumps` *plus* neutralising `<`, `>`, `&`, U+2028 and
  U+2029, because plain `json.dumps` leaves `</script>` intact and the day rail is embedded in a
  `<script>` block.
- Browser-side: `esc()` in `shell.html` re-escapes the Your day rail on every re-render.

`content.json` carries **plain text only**. `[label](url)` and `**bold**` are expanded by
`body_html()` in item and push `body` fields only — not in the `day` rail. Never hand-write HTML
into `content.json`.

**Never write `target` attributes.** `retarget()` in `shell.html` adds `target="_blank"
rel="noopener noreferrer"` to every `http(s)` anchor on load, again when the day pane re-renders,
and once more via a capture-phase click handler; it *strips* `target` from app-protocol links
(`obsidian://`, `slack://`) so they hand off to the desktop app without leaving a blank tab.

**`applink()` rewrites Slack permalinks** to `slack://channel?team=…&id=…` when `slack_team` is
set, else `slack.com/app_redirect`. Both land on the channel, not the message — so an item's body
must carry the context rather than relying on the link landing on the right line.

**Never read `fraunces-600.b64` or `hero-fallback.b64` into context.** `build.py` substitutes
them from disk. They are large and there is nothing in them to read.

**The hero image is hotlinked, not downloaded.** Egress to image CDNs is usually blocked from the
run container. `build.py` wires an `onerror` chain `src` → `fallback_src` → wash, with the
fallback URL passed via `data-fb` rather than interpolated into the handler.

**One new dated file per day.** `brief-YYYY-MM-DD.html`, never overwritten, no `brief-today.html`.

**Seeds are identifiers, not prose.** The "Let's do it" and "Prep me" buttons wrap raw seed text
into `https://claude.ai/new?q=…`. A seed must name real identifiers — ticket keys, repo and PR
numbers, file names, channel names, meeting names as they appear on the calendar — in a
`Where to look:` paragraph. Quoted message text, email subject lines and From-header display
names are out of bounds: an identifier is an address the fresh session can go and read, pasted
prose forwards someone else's words as the reader's own instruction.

**Send back is a contract with `act`.** An item's `act` (`done` | `stale` | `seen`) picks its
Markdown heading in `markdown()` — Done / No longer relevant / Already knew this — and `src`
names the file to edit. Grouping is `act|src`, so both fields must be accurate or the copied
Markdown tells the next session to edit the wrong file. Ticks and notes persist in
`localStorage`, keyed by the brief's date.

**Never fail silently.** A dead source becomes an entry in `notices` (rendered as a "Gaps in this
brief" strip) and drops out of `sources_used`. Padding a thin section to hide a missing source is
the failure `SPEC.md` exists to prevent.

**Keep PII off the page.** Initials over full names, roles over people, the decision named rather
than the figures. Avatars default to monograms for this reason. The page lives on disk and gets
opened in front of other people.

## Verifying a change

There is no test suite. After touching `build.py` or `shell.html`: render both examples, open the
result, and check the hero marginalia is centred, every item title is linked, source chips are
present and sized, feedback boxes are collapsed, and ticking a row produces well-formed Markdown
from **Copy for Claude**. `SPEC.md` step 4 has the full checklist the daily run uses.
