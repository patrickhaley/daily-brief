# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **template** for a self-building morning briefing. There is no app and no server: a scheduled
Claude task reads the reader's connected sources plus two local Markdown files, writes a
`content.json`, and `build.py` renders it into one self-contained dated HTML file.

The repository ships only generic, fictional content. Everything account-specific lives in
`daily-brief/config.json` (gitignored; `config.json.example` is the shareable copy).

## Secrets and personal information never get committed

This is a public-facing template, and the hard rule is that **nothing identifying and no
credential ever reaches a commit**. `config.json` is the one place real details belong, and it is
gitignored.

### Enforced, not just documented

`scripts/scan-secrets.py` blocks it mechanically. Two git hooks run it:

| Hook | Scans |
|---|---|
| `.githooks/pre-commit` | the staged changes |
| `.githooks/pre-push` | every commit in the range being pushed |

`pre-push` is the one that matters, because it catches a commit made with `--no-verify`, or on
another machine, before it ever leaves the laptop.

**The hooks are inert until git is pointed at them, and cloning does not do it.** `core.hooksPath`
is local config, so it is per-clone and untracked — a fresh clone, or a second machine, has the
hook files and none of the enforcement. Check before relying on it, and offer to fix it if the
answer is empty:

```sh
git config core.hooksPath                  # must print .githooks
git config core.hooksPath .githooks        # if it does not
python3 scripts/scan-secrets.py --all      # audit everything already tracked
```

Do not treat the hooks' existence as proof they are active, and do not disable them to get a
commit through. If one blocks you, the finding is the problem, not the hook.

It detects private key blocks, AWS / Slack / GitHub / Google / Anthropic / OpenAI / Stripe /
Atlassian tokens, JWTs, `user:pass@` URLs, secrets in query strings, `Authorization:` headers,
anything assigned to a key named like `password` / `api_key` / `client_secret`, home-directory
paths, and email addresses.

It also **learns the reader's own identifiers** by diffing `config.json` against
`config.json.example`: any hostname or id-shaped token in the real config but not the shipped
template is account-specific by definition, so it gets flagged wherever it appears. That needs no
list-keeping — filling in `config.json` is what teaches it.

Only *added* lines are scanned in diff modes, so existing history never blocks unrelated work. A
deliberate placeholder is exempted with the marker `allowlist-secret` in a comment on the same
line — sparingly, and never on a real value.

The hooks are a backstop, not permission to stop reading diffs. They match patterns; they cannot
recognise an organisation's name or a colleague's, so the judgement below is still yours.

### Never in a tracked file

- API keys, tokens, passwords, passphrases, private keys, connection strings, session cookies
- Usernames, personal or colleague names, email addresses, and email domains
- Employer or organisation domains, and any source URL carrying them — issue-tracker sites,
  support-inbox app ids, dashboards, repo hosts
- Slack team ids, workspace names, channel ids
- Vault names, and absolute paths containing a username or home directory
- Real ticket keys, avatar URLs, or meeting names lifted from an actual calendar

The credential filename patterns in `.gitignore` (`.env`, `*.pem`, `*.key`, `secrets.json`, …)
stop the common cases earlier still. **Never paste a credential into a source file to "test"
it** — the hooks will refuse the commit, and the value is compromised the moment it is written.

### What is tracked, and therefore must stay fictional

`config.json.example`, everything in `examples/`, and everything in `templates/` **are tracked**.
Follow the placeholders already in use rather than inventing a new convention, and prefer an
obviously fake domain over a plausible one.

The ignore rules protect named patterns only — a *new* file gets no protection unless you add it.
So read the diff as well as trusting the hook.

If something identifying has already been committed, deleting it in a later commit is not a fix —
say so plainly, because the history still carries it, and a pushed credential must be rotated
rather than merely removed.

This is stricter than the on-page PII rule further down: the page keeps personal detail minimal
for the reader's sake, while the repository carries none at all.

## Commands

Python 3, standard library only. No dependencies, no build step, no test suite.

```sh
cd daily-brief

# render the fully-exercised example (the smoke test for any change to build.py or shell.html)
python3 build.py examples/content-example.json /tmp/brief.html && open /tmp/brief.html

# render the smallest valid content.json — catches missing-key regressions
python3 build.py examples/content-example-minimal.json /tmp/brief-min.html
```

`build.py` refuses to write a page with an unsubstituted placeholder left in it, so a successful
render is the pass condition. The example hero URL deliberately 404s — falling back to the
blurred wash is correct, not a bug.

## Architecture

### Three files, three jobs

| File | Lifetime | Owner |
|---|---|---|
| `config.json` | edited once | the reader — vault name, timezone, source URLs, palette |
| `content.json` | written fresh every morning | the scheduled run; contract in `content.schema.md` |
| `shell.html` | rarely touched | the design — all CSS and all browser JS |

`build.py` is pure substitution: it reads `shell.html`, replaces the `{{SLOT}}` and `__TOKEN__`
placeholders, and writes one file. Adding a placeholder to `shell.html` without adding it to the
`slots` dict in `build()` is a hard failure, by design.

**Precedence:** `content.json` wins over `config.json`, which wins over the `DEFAULT_*` constants
in `build.py` — see `pick()` in `build()`. An explicit `null` in `content.json` falls through to
`config.json` rather than meaning "unset".

### Where behaviour is defined, and where it is not

`task-prompt.md` is deliberately short and says little more than "read `SPEC.md` and follow it",
so the run never re-derives the design and the brief cannot drift when a section changes. So:

- **Run behaviour, switches, and the rules that stop the brief being wrong → `SPEC.md`.**
  Edit this, not the task prompt.
- **The shape of `content.json` → `content.schema.md`.**
- **Layout, palette, browser behaviour → `shell.html` + `theme` in `config.json`.**

`SPEC.md` describes a two-phase run: Phase 1 syncs the reader's tasks and delegated Markdown
files, Phase 2 builds the page. Phase 1 is the only thing in the whole run permitted to write
outside the output folder; every other source is read-only.

### Adding a source

Three coordinated edits: an entry in `SRC` in `build.py` (label, glyph key, fallback URL), a
matching glyph in `GLYPH`, and a line in `SPEC.md` saying what to gather from it. The new key is
then usable in `srcs`, `glyphs` and `sources_used`. A source with no sensible default URL is
`None` in `SRC` and renders as an unlinked chip — never invent a default that encodes someone's
account.

`footer_sources()` collapses `tasks` + `delegated` into one reader-facing name, and the footer is
generated from `sources_used` alone — never a fixed list, so a dead source drops out of it
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

**Never write `target` attributes.** `retarget()` in `shell.html` owns this: it adds
`target="_blank" rel="noopener noreferrer"` to `http(s)` anchors on load, on every day-pane
re-render, and via a capture-phase click handler so script-added links are covered. It *strips*
`target` from app-protocol links (`obsidian://`, `slack://`) so they hand off to the desktop app
without leaving a blank tab behind.

**`applink()` rewrites Slack permalinks** to a `slack://` deep link when `slack_team` is set, and
to an app-redirect URL otherwise. Both land on the channel, not the message — so an item's body
must carry the context rather than relying on the link landing on the right line.

**Never read `fraunces-600.b64` or `hero-fallback.b64` into context.** `build.py` substitutes
them from disk. They are large and there is nothing in them to read.

**The hero image is hotlinked, not downloaded.** Egress to image CDNs is usually blocked from the
run container. `build.py` wires an `onerror` chain `src` → `fallback_src` → wash, with the
fallback URL passed via `data-fb` rather than interpolated into the handler.

**One new dated file per day.** `brief-YYYY-MM-DD.html`, never overwritten, no `brief-today.html`.

**Seeds are identifiers, not prose.** The "Let's do it" and "Prep me" buttons wrap raw seed text
into a `claude.ai/new?q=…` link. A seed must name real identifiers — ticket keys, repo and PR
numbers, file names, channel names, meeting names as they appear on the calendar — in a
`Where to look:` paragraph. Quoted message text, email subject lines and From-header display
names are out of bounds: an identifier is an address the fresh session can go and read, while
pasted prose forwards someone else's words as the reader's own instruction.

**Send back is a contract with `act`.** An item's `act` (`done` | `stale` | `seen`) picks its
heading in `markdown()`, and `src` names the file to edit. Grouping is `act|src`, so both fields
must be accurate or the copied Markdown tells the next session to edit the wrong file. Ticks and
notes persist in `localStorage`, keyed by the brief's date.

**Never fail silently.** A dead source becomes an entry in `notices` (rendered as a "Gaps in this
brief" strip) and drops out of `sources_used`. Padding a thin section to hide a missing source is
the failure `SPEC.md` exists to prevent.

**Keep PII off the page too.** Initials over full names, roles over people, the decision named
rather than the figures. Avatars default to monograms for this reason. The page lives on disk and
gets opened in front of other people.

## Verifying a change

There is no test suite. After touching `build.py` or `shell.html`, render both examples and open
the result: the hero marginalia centred, every item title linked, source chips present and sized,
feedback boxes collapsed, and ticking a row producing well-formed Markdown from **Copy for
Claude**. The delivery checklist in `SPEC.md` is the fuller version the daily run uses.
