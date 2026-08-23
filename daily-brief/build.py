#!/usr/bin/env python3
"""
Render the daily brief from content.json into a single self-contained HTML file.

  python3 build.py content.json /path/out/brief-YYYY-MM-DD.html

Three files, three jobs:
  config.json   your details      -- vault name, source URLs, palette. Edit once.
  content.json  today's content   -- written fresh by the run. See content.schema.md.
  shell.html    the page          -- structure and CSS. Rarely needs touching.

Never paste the font base64 into a prompt or read fraunces-600.b64 into context;
this script substitutes it from disk.
"""
import datetime, html, json, pathlib, re, sys, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
SEED_BASE = "https://claude.ai/new?q="
SEED_TAIL = "&surface=cowork&composer=mini"
# The day's painting is served straight from the National Gallery IIIF endpoint.
NGA_IIIF = "https://api.nga.gov/iiif/%s/full/!1600,1600/0/default.jpg"

# Fallbacks for anything config.json does not set. config.json wins; these keep a
# missing or partial config from breaking the build.
DEFAULT_THEME = {
    'paper': '#F4F2F0', 'card': '#FBFAF9', 'ink': '#1A1818', 'ink_soft': '#6B6560',
    'line': '#B0A091', 'rule': '#DDD8D3', 'accent': '#B4342A', 'accent_hover': '#93281F',
    'serif': "'Fraunces', Georgia, serif",
    'sans': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
}
THEME_VAR = {'paper': '--paper', 'card': '--card', 'ink': '--ink', 'ink_soft': '--ink2',
             'line': '--ink3', 'rule': '--rule', 'accent': '--red', 'accent_hover': '--redh',
             'serif': '--serif', 'sans': '--sans'}
DEFAULT_FOOTER_LEAD = 'Made for you by <b>Claude</b> using <i>your</i>'
DEFAULT_APPLY_NOTE = ('Apply the above: edit the referenced files in the {vault} vault, update or '
                      'comment on the tickets named, and tell me what you changed. '
                      'Ask before anything irreversible.')


def load_config():
    """config.json sits beside this script and is optional."""
    f = HERE / 'config.json'
    if not f.exists():
        return {}
    cfg = json.loads(f.read_text())
    return {k: v for k, v in cfg.items() if not k.startswith('_')}


def nga_painting(date):
    """The day's painting from the bundled National Gallery shortlist.

    Rotation is by ordinal date rather than a hash of it, so the list is walked in
    order and nothing repeats until it has been all the way round. Returns a
    (url, credit lines) pair, or None if nga-paintings.json is missing or empty.
    """
    f = HERE / 'nga-paintings.json'
    if not f.exists():
        return None
    lst = (json.loads(f.read_text()) or {}).get('paintings') or []
    if not lst:
        return None
    p = lst[datetime.date.fromisoformat(date).toordinal() % len(lst)]
    # Three short lines, not one long one: the credit sits beside the standfirst and
    # a wide credit squeezes it. The images are CC0, so this is courtesy, not duty.
    return (NGA_IIIF % p['uuid'],
            [p['artist'], p['title'], '%s \u00b7 National Gallery of Art' % p['year']])


def theme_css(theme):
    """Palette declarations for shell.html's :root. Config over DEFAULT_THEME."""
    merged = dict(DEFAULT_THEME)
    merged.update({k: v for k, v in (theme or {}).items() if v})
    return ''.join('%s:%s;' % (THEME_VAR[k], merged[k]) for k in THEME_VAR if k in merged)

# ---------------------------------------------------------------- source icons
# fill and stroke read the palette, so a rebrand carries through to the source icons
_S = 'xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="var(--ink)"'
GLYPH = {
 'jira':  f'<svg {_S}><path d="M12 1.5 2.8 10.7a1 1 0 0 0 0 1.4l3 3L12 8.9l6.2 6.2 3-3a1 1 0 0 0 0-1.4L12 1.5z"/><path d="M12 11.9l-5.4 5.4 3.2 3.2a3 3 0 0 0 4.4 0l3.2-3.2L12 11.9z" opacity=".45"/></svg>',
 'slack': f'<svg {_S}><path d="M9.6 2.4 8.9 7H4.6l-.4 2.4h4.4l-.6 4.2H3.6L3.2 16h4.4l-.7 4.4 2.4.4.7-4.8h4.2l-.7 4.4 2.4.4.7-4.8h4.4l.4-2.4h-4.4l.6-4.2h4.4l.4-2.4h-4.4l.7-4.4L17 2.2l-.7 4.8h-4.2l.7-4.4-2.4-.4-.8 4.8zM10.7 9.4h4.2l-.6 4.2h-4.2l.6-4.2z"/></svg>',
 'github':f'<svg {_S}><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.85-2.35 4.7-4.58 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/></svg>',
 'gmail': f'<svg {_S}><path d="M2 6.5A2.5 2.5 0 0 1 4.5 4h15A2.5 2.5 0 0 1 22 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 2 17.5v-11zm2.2-.3L12 12.4l7.8-6.2H4.2zM4 8.3v9.2h16V8.3l-8 6.4-8-6.4z"/></svg>',
 'cal':   f'<svg {_S}><path d="M7 2v2H5.5A2.5 2.5 0 0 0 3 6.5v13A2.5 2.5 0 0 0 5.5 22h13a2.5 2.5 0 0 0 2.5-2.5v-13A2.5 2.5 0 0 0 18.5 4H17V2h-2v2H9V2H7zM5 10h14v9.5a.5.5 0 0 1-.5.5h-13a.5.5 0 0 1-.5-.5V10zm2 2v2h2v-2H7zm4 0v2h2v-2h-2zm4 0v2h2v-2h-2zM7 16v2h2v-2H7zm4 0v2h2v-2h-2z"/></svg>',
 'intercom': f'<svg {_S}><path d="M4.5 2A2.5 2.5 0 0 0 2 4.5v15A2.5 2.5 0 0 0 4.5 22h15a2.5 2.5 0 0 0 2.5-2.5v-15A2.5 2.5 0 0 0 19.5 2h-15zM6 6.5a1 1 0 0 1 2 0v7a1 1 0 0 1-2 0v-7zm3.5-1a1 1 0 0 1 2 0v9a1 1 0 0 1-2 0v-9zm3.5 1a1 1 0 0 1 2 0v7a1 1 0 0 1-2 0v-7zM16.5 8a1 1 0 0 1 2 0v4a1 1 0 0 1-2 0V8zM5.6 17.3a1 1 0 0 1 1.4-.2 8.4 8.4 0 0 0 10 0 1 1 0 1 1 1.2 1.6 10.4 10.4 0 0 1-12.4 0 1 1 0 0 1-.2-1.4z"/></svg>',
 'obsidian': f'<svg {_S}><path d="M12.6 1.9 5.1 7.6 3.4 15l5.2 7.1 8.6-1.5 3.4-9.2-8-9.5z"/><g fill="none" stroke="var(--paper)" stroke-width="1.05"><path d="M12.6 2.6 10 10.3l-6.4 4.4M10 10.3l7.1 10.2M10 10.3l10.3.9"/></g></svg>',
 'drive': f'<svg {_S}><path d="M8.4 2h7.2l6.4 11.1h-7.2L8.4 2zM7.1 3.6 13.5 14.7 9.9 21 3.5 9.9 7.1 3.6zM11.2 15.9h11.6L19.2 22H7.6l3.6-6.1z"/></svg>',
 'gchat': f'<svg {_S}><path d="M3.4 3h17.2A1.4 1.4 0 0 1 22 4.4v11.2a1.4 1.4 0 0 1-1.4 1.4H8.9L4.1 21.6A.7.7 0 0 1 3 21V4.4A1.4 1.4 0 0 1 3.4 3zm3.2 4.6a1.1 1.1 0 0 0 0 2.2h10.8a1.1 1.1 0 0 0 0-2.2H6.6zm0 4a1.1 1.1 0 0 0 0 2.2h7a1.1 1.1 0 0 0 0-2.2h-7z"/></svg>',
 'circleback': f'<svg {_S}><path d="M12 2a10 10 0 1 0 9.5 13.1 1.2 1.2 0 0 0-2.3-.7A7.6 7.6 0 1 1 12 4.4c2 0 3.9.8 5.3 2.1l-2.1 2.1h5.6V3l-1.8 1.8A10 10 0 0 0 12 2z"/><circle cx="12" cy="12" r="2.6"/></svg>',
}
# short label + default deep link for each source
# label + glyph + fallback deep link for each source. Override any href under
# "sources" in config.json. The two that are account-specific -- your Jira site and
# your Intercom app id -- have no sensible default, so they start as None: set them
# in config.json or the chip renders as plain text with no link.
SRC = {
 'tasks':     ('TASKS.md',      'obsidian', 'obsidian://open?vault={vault}&file={tasks}'),
 'delegated': ('DELEGATED.md',  'obsidian', 'obsidian://open?vault={vault}&file={delegated}'),
 'jira':      ('Jira',          'jira',     None),
 'gmail':     ('Gmail',         'gmail',    'https://mail.google.com/mail/u/0/#inbox'),
 'intercom':  ('Intercom',      'intercom', None),
 'slack':     ('Slack',         'slack',    'slack://open'),
 'github':    ('GitHub',        'github',   'https://github.com/pulls/review-requested'),
 'cal':       ('Calendar',      'cal',      'https://calendar.google.com/calendar/r/day/{y}/{m}/{d}'),
 'drive':     ('Drive',         'drive',    'https://drive.google.com/drive/recent'),
 'gchat':     ('Google Chat',   'gchat',    'https://chat.google.com/'),
 'circleback':('Circleback',    'circleback','https://app.circleback.ai/meetings'),
}

SLACK_ARCHIVE = re.compile(r'^https://([\w-]+)\.slack\.com/archives/([A-Z0-9]+)(?:/p(\d+))?', re.I)

def applink(url, ctx):
    """Point a link at the desktop app where one exists.

    Slack is the only connected source with a useful custom scheme. With a team id we can
    deep-link straight to the channel; without one, slack.com/app_redirect still hands off
    to the installed app. Set link_mode to "web" in content.json to keep browser URLs.
    Jira, Gmail, Calendar, Chat, Intercom, GitHub and Circleback have no desktop app worth
    routing to, so they stay as https.
    """
    if not url or ctx.get('link_mode') == 'web':
        return url
    m = SLACK_ARCHIVE.match(url)
    if m:
        channel = m.group(2)
        team = ctx.get('slack_team')
        if team:
            return 'slack://channel?team=%s&id=%s' % (team, channel)
        return 'https://slack.com/app_redirect?channel=%s' % channel
    return url

def e(s):
    """Escape gathered text. Everything from a tool result goes through this."""
    return html.escape(str(s or ''), quote=True)

def seed(text):
    return SEED_BASE + urllib.parse.quote(text or '', safe='') + SEED_TAIL

def jslit(obj):
    """A JSON value safe to embed in a <script> block.

    json.dumps alone is not enough: it leaves "</script>" intact, so any gathered
    string reaching the day rail could close the script element and inject markup.
    Neutralise the HTML-significant characters and the two line separators that are
    newlines to a JS parser but not to JSON.
    """
    return (json.dumps(obj, ensure_ascii=False)
            .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))

def safe_url(url):
    """Image URLs are http(s) only. Anything else is dropped, and the wash shows."""
    return url if re.match(r'^https?://', str(url or ''), re.I) else ''

# ---------------------------------------------------------------- components
def srcs(keys, ctx):
    if not keys:
        return ''
    out = []
    for k in keys:
        if k not in SRC:
            continue
        label, glyph, default = SRC[k]
        href = ctx['sources'].get(k, default)   # an explicit null means "no URL"
        if k == 'slack' and ctx.get('slack_team'):
            href = 'slack://open?team=%s' % ctx['slack_team']
        if not href:
            # No URL configured for this source. Show the chip, do not fake a link.
            out.append(f'<span>{GLYPH[glyph]}{label}</span>')
            continue
        href = href.format(vault=ctx['vault'], y=ctx['y'], m=ctx['m'], d=ctx['d'],
                           tasks=ctx['tasks'], delegated=ctx['delegated'])
        out.append(f'<a href="{e(applink(href, ctx))}">{GLYPH[glyph]}{label}</a>')
    return '<span class="srcs">' + ''.join(out) + '</span>'

def avatar(a):
    tint = ' b' if a.get('tint') else ''
    url = safe_url(a.get('url'))
    img = f'<img src="{e(url)}" alt="" onerror="this.remove()">' if url else ''
    return f'<span class="ava{tint}" data-i="{e(a.get("i",""))}">{img}</span>'

def glyphs(keys):
    if not keys:
        return ''
    return '<span class="glyphs">' + ''.join(GLYPH[k] for k in keys if k in GLYPH) + '</span>'

def title_html(it, ctx):
    t = e(it['title'])
    if it.get('href'):
        t = f'<a href="{e(applink(it["href"], ctx))}">{t}</a>'
    tag = f' <span class="tag">{e(it["tag"])}</span>' if it.get('tag') else ''
    return t + tag + glyphs(it.get('glyphs')) + ''.join(avatar(a) for a in it.get('avatars', []))

def body_html(it, ctx=None):
    """Body text with [label](url) turned into links. Text is escaped first."""
    ctx = ctx or {}
    txt = e(it.get('body', ''))
    txt = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|obsidian://[^)\s]+|slack://[^)\s]+)\)',
                 lambda m: f'<a href="{applink(m.group(2), ctx)}">{m.group(1)}</a>', txt)
    txt = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', txt)
    return txt

def row(it, ctx):
    return (f'<div class="row" data-id="{e(it["id"])}" data-act="{e(it["act"])}" '
            f'data-src="{e(it["src"])}" data-ref="{e(it.get("ref",""))}">'
            '<input class="chk" type="checkbox" aria-label="tick">'
            f'<div><p class="it-title">{title_html(it, ctx)}</p>'
            f'<p class="it-body">{body_html(it, ctx)}</p></div></div>')

def feedback(sec, placeholder):
    return (f'<div class="fb" data-sec="{e(sec)}">'
            '<span class="fbt"><span class="pm">+</span>Add feedback</span>'
            f'<textarea placeholder="{e(placeholder)}"></textarea></div>')

def section(s, ctx):
    label = (f'<div class="slabel">{e(s["label"])}'
             f'<span class="sub">{e(s.get("sub",""))}</span>{srcs(s.get("srcs"), ctx)}</div>')
    rows = ''.join(row(i, ctx) for i in s.get('items', []))
    if not s.get('items'):
        rows = '<p class="it-body" style="padding-bottom:6px">Nothing here today.</p>'
    fb = feedback(s['label'], s.get('feedback_hint', 'Anything I got wrong, or should have caught.'))
    return f'  <section>\n    {label}\n    <div>{rows}{fb}</div>\n  </section>\n'

def notices(items):
    """Sources that could not be reached, and anything else the run needs to admit."""
    if not items:
        return ''
    return ('<div class="notices"><p class="h">Gaps in this brief</p>'
            + ''.join('<p>%s</p>' % body_html({'body': n}) for n in items)
            + '</div>')

def footer_sources(keys, ctx):
    """Only the sources this run actually read. Never a fixed list."""
    names, vault = [], False
    for k in keys:
        if k in ('tasks', 'delegated'):
            vault = True
        elif k in SRC:
            names.append(SRC[k][0])
    if vault:
        # the two markdown files read as one source to a reader
        names.append(ctx.get('vault_label', 'vault'))
    if not names:
        return e(ctx.get('vault_label', 'vault'))
    if len(names) == 1:
        return e(names[0])
    return e(', '.join(names[:-1])) + ' <i>and</i> ' + e(names[-1])

def push_body(p, ctx):
    return ('<div class="pushbody">'
            f'<p class="title">{e(p["title"])}</p>'
            f'<p>{body_html(p, ctx)}</p>'
            + feedback('Push your work forward',
                       p.get('feedback_hint', 'Wrong call? Different owner? Say so and I will redo the hand-off.'))
            + '</div>')

def js_data(content):
    """Avatar registry + the Your day rail, as JS literals."""
    A, seen = {}, {}
    def key(a):
        k = (a.get('i', '') or 'x').lower()
        seen[k] = a
        return k
    day = []
    for d in content['day']:
        who = [key(a) for a in d.get('who', [])]
        day.append({'t': d['t'], 'n': d['n'], 'soft': bool(d.get('soft')),
                    'who': who, 'h': d['h'], 'p': d['p'], 'seed': d.get('seed')})
    for k, a in seen.items():
        A[k] = [a.get('i', ''), 'b' if a.get('tint') else '', safe_url(a.get('url'))]
    return 'const A = ' + jslit(A) + ';\nconst DAY = ' + jslit(day) + ';'

# ---------------------------------------------------------------- main
def build(content, cfg=None):
    """content.json wins over config.json, so a run can override any setting for a day."""
    cfg = cfg if cfg is not None else load_config()
    paths = cfg.get('paths') or {}
    def pick(k, default):
        # content.json wins, but an explicit null there falls through to config.json
        v = content.get(k)
        if v is None:
            v = cfg.get(k)
        return default if v is None else v

    ctx = {'vault': pick('vault', 'PersonalOS'),
           'vault_label': pick('vault_label', 'vault'),
           'slack_team': pick('slack_team', None),
           'link_mode': pick('link_mode', 'app'),
           'sources': dict(cfg.get('sources') or {}, **(content.get('sources') or {})),
           'tasks': paths.get('tasks', 'TASKS.md'),
           'delegated': paths.get('delegated', 'DELEGATED.md')}
    y, m, d = content['date'].split('-')
    ctx.update(y=int(y), m=int(m), d=int(d))

    shell = (HERE / 'shell.html').read_text()
    font = (HERE / 'fraunces-600.b64').read_text().strip()

    hero = content.get('hero') or {}
    hero_src = safe_url(hero.get('src'))
    credit = content.get('credit', [])
    # A painting from the National Gallery shortlist backs up the generated image, and
    # stands in for it on a morning that produced none. "nga": false opts out, which is
    # what HERO=off sets, so "off" still means the neutral wash and nothing else.
    nga = nga_painting(content['date']) if hero.get('nga', True) else None

    hero_class = ''
    if not hero_src and hero.get('svg'):
        # HERO=drawing: the line drawing is the intent, not a hole to fill, so the
        # painting stays out of its way and the wash sits behind it as before.
        hero_img = hero['svg']
    elif hero_src or nga:
        if not hero_src:
            # Nothing was generated today, so the painting is the hero rather than a
            # fallback -- and it owns the credit line and the heavier scrim, which
            # build.py sets here instead of leaving them to the handler below.
            hero_src, credit = nga[0], nga[1]
            nga = None
            hero_class = ' art'
        # Each candidate rides in a data attribute rather than being interpolated into
        # the handler, so a hostile value cannot break out of the JS string. The handler
        # walks data-fb1, data-fb2, ... and removes the image once they run out, which
        # uncovers the wash. A candidate with a data-cN takes the credit line with it.
        chain = [(u, None) for u in [safe_url(hero.get('fallback_src'))] if u]
        if nga:
            chain.append(nga)
        attrs = ''
        for i, (url, lines) in enumerate(chain, 1):
            attrs += f'data-fb{i}="{e(url)}" '
            if lines:
                # a candidate with a credit is a painting, so it brings the scrim with it
                attrs += f'data-c{i}="{e(chr(10).join(lines))}" '
        hero_img = (f'<img src="{e(hero_src)}" alt="Painted scene for today\'s brief" {attrs}'
                    'onerror="var d=this.dataset,n=(+d.n||0)+1,u=d[\'fb\'+n],c=d[\'c\'+n];'
                    'd.n=n;if(!u){this.remove();return}this.src=u;if(!c)return;'
                    'this.parentNode.classList.add(\'art\');'
                    'var p=document.querySelector(\'.credit\');if(p)p.textContent=c">')
    else:
        hero_img = ''
    wash = hero.get('bg_b64')
    if not wash:
        wf = HERE / 'hero-fallback.b64'
        wash = wf.read_text().strip() if wf.exists() else ''
    tint = hero.get('bg_tint', '#3A4942')
    bg = f'{tint} url(data:image/jpeg;base64,{wash})' if wash else tint

    slots = {
      '{{TITLE}}':       e(content['title']),
      '{{MARG_L}}':      e(content['marg_left']),
      '{{MARG_R}}':      e(content['marg_right']),
      '{{MASTHEAD}}':    e(content['masthead']),
      '{{HERO_BG_CSS}}': bg,
      '{{HERO_IMG}}':    hero_img,
      '{{HERO_CLASS}}':  hero_class,
      '{{STANDFIRST}}':  e(content['standfirst']),
      '{{CREDIT}}':      '<br>'.join(e(l) for l in credit),
      '{{PUSH_BODY}}':   push_body(content['push'], ctx),
      '{{PUSH_SRCS}}':   srcs(content['push'].get('srcs', ['delegated','jira']), ctx),
      '{{PUSH_SEED}}':   jslit(seed(content['push'].get('seed', ''))),
      '{{SECTIONS}}':    ''.join(section(s, ctx) for s in content['sections']),
      '{{DAY_SRCS}}':    srcs(content.get('day_srcs', ['cal']), ctx),
      '{{JS_DATA}}':     js_data(content),
      '{{DATE}}':        content['date'],
      '{{THEME_VARS}}':  theme_css(cfg.get('theme')),
      '{{FOOTER_LEAD}}': cfg.get('footer_lead', DEFAULT_FOOTER_LEAD),
      '{{APPLY_NOTE}}':  jslit(
          cfg.get('apply_note', DEFAULT_APPLY_NOTE).format(vault=ctx['vault'])),
      '{{NOTICES}}':     notices(content.get('notices', [])),
      '{{FOOTER_SOURCES}}': footer_sources(content.get('sources_used') or [], ctx),
    }
    for k, v in slots.items():
        shell = shell.replace(k, v)
    shell = shell.replace('__FONT_B64__', font)
    alias = {'obsidian': 'OBS', 'circleback': 'CB'}
    for k, v in GLYPH.items():
        shell = shell.replace('__G_%s__' % k.upper(), v)
        if k in alias:
            shell = shell.replace('__G_%s__' % alias[k], v)

    leftover = re.findall(r'\{\{[A-Z_]+\}\}|__[A-Z0-9_]+__', shell)
    if leftover:
        raise SystemExit('unfilled slots: %s' % sorted(set(leftover)))
    return shell

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    html_out = build(json.loads(src.read_text()))
    out.write_text(html_out)
    print('wrote %s (%d bytes)' % (out, len(html_out)))
