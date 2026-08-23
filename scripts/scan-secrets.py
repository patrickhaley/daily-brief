#!/usr/bin/env python3
"""
Block credentials and identifying details from reaching a commit or a push.

  scan-secrets.py                 scan staged changes            (pre-commit)
  scan-secrets.py --range A..B    scan the commits in a range     (pre-push)
  scan-secrets.py --all           scan every tracked file         (audit)
  scan-secrets.py FILE [FILE...]  scan specific files

Exit 0 clean, 1 on a finding, 2 on a usage error. Python 3, standard library only.

Only ADDED lines are scanned in diff modes, so existing history never blocks a
commit that does not touch it.

A deliberate placeholder — a fictional example, a documented pattern — is exempted by
putting the marker  allowlist-secret  in a comment on the same line. Use it sparingly
and never on a real value.
"""
import argparse, pathlib, re, subprocess, sys, urllib.parse

# Files whose contents are noise to a pattern scanner, or which legitimately contain
# the patterns themselves. Matched against the repo-relative path.
SKIP = (
    re.compile(r'\.b64$'),                    # embedded font / image blobs: base64 noise
    re.compile(r'^scripts/scan-secrets\.py$'),  # this file is nothing but patterns
    re.compile(r'^\.githooks/'),              # the hooks quote the marker
)

ALLOW_MARKER = 'allowlist-secret'

# Ordered most-specific first, so the clearest name for a finding wins.
RULES = [
    ('private key block',   re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('AWS access key id',   re.compile(r'\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b')),
    ('Slack token',         re.compile(r'\bxox[abprse]-[0-9A-Za-z-]{10,}')),
    ('Slack webhook',       re.compile(r'https://hooks\.slack\.com/services/\S{20,}')),
    ('GitHub token',        re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b')),
    ('Google API key',      re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ('Anthropic API key',   re.compile(r'\bsk-ant-[A-Za-z0-9_-]{16,}')),
    ('Stripe key',          re.compile(r'\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}')),
    ('OpenAI API key',      re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9]{24,}\b')),
    ('Atlassian API token', re.compile(r'\bATATT3[A-Za-z0-9_=+-]{20,}')),
    ('JWT',                 re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}')),
    ('credential in URL',   re.compile(r'\b[a-z][a-z0-9+.-]*://[^/\s:@"\']+:[^/\s@"\']+@')),
    ('secret in URL query', re.compile(
        r'[?&](?:api[_-]?key|apikey|access[_-]?token|auth[_-]?token|token|secret'
        r'|password|passwd|pwd)=[^&\s"\'<>]+', re.I)),
    ('Authorization header', re.compile(
        r'authorization\s*["\']?\s*[:=]\s*["\']?\s*(?:bearer|basic|token)\s+\S+', re.I)),
    ('assigned secret',     re.compile(
        r'\b(?:api[_-]?key|apikey|secret(?:[_-]?key)?|access[_-]?token|auth[_-]?token'
        r'|refresh[_-]?token|client[_-]?secret|password|passwd|pwd|passphrase'
        r'|private[_-]?key|credentials?)\b\s*["\']?\s*[:=]\s*["\']?[^\s"\',}{]{8,}', re.I)),
    ('home directory path', re.compile(r'(?:/Users/|/home/|C:\\Users\\)[A-Za-z0-9._-]+')),
    ('email address',       re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')),
]



# ---------------------------------------------------------------- your own identifiers
# config.json is gitignored and holds the reader's real settings; config.json.example is
# the shipped template. Anything that appears in the first but not the second is, by
# definition, account-specific -- so we can flag it without anyone maintaining a list.
CFG      = 'daily-brief/config.json'
CFG_EX   = 'daily-brief/config.json.example'
HOSTISH  = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9-]+)+')
QUOTED   = re.compile(r'"(?:vault|vault_label|slack_team)"\s*:\s*"([^"]+)"')
# id-shaped: >=6 chars carrying both a letter and a digit. Catches an Intercom app id or a
# Slack team id sitting in a URL path, which HOSTISH cannot see. Words never match.
IDISH    = re.compile(r'\b(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{6,}\b')


def own_identifiers(root=''):
    """Literal strings that identify this reader, learned from their own config."""
    def read(rel):
        try:
            return (pathlib.Path(root) / rel).read_text()
        except OSError:
            return ''
    # percent-decode first, or "%20ORDER" and "%3DDone" read as id-shaped tokens
    mine = urllib.parse.unquote(read(CFG))
    shipped = urllib.parse.unquote(read(CFG_EX))
    if not mine:
        return []
    generic = (set(HOSTISH.findall(shipped)) | set(QUOTED.findall(shipped))
               | set(IDISH.findall(shipped)))
    found = (set(HOSTISH.findall(mine)) | set(QUOTED.findall(mine))
             | set(IDISH.findall(mine)))
    # a bare "build.py" or "config.json" also matches HOSTISH; drop anything too short
    # or with a known-code extension, and anything the template already ships.
    out = []
    for tok in found - generic:
        if len(tok) < 6 or tok.rsplit('.', 1)[-1].lower() in (
                'py', 'md', 'json', 'html', 'b64', 'js', 'css', 'txt', 'example'):
            continue
        if re.fullmatch(r'[0-9A-Fa-f]{6,8}', tok):
            continue                      # a hex colour from "theme", not an identifier
        out.append(tok)
    return sorted(out, key=len, reverse=True)


OWN = []


def skipped(path):
    return any(p.search(path) for p in SKIP)


def check(path, lineno, text, out):
    if ALLOW_MARKER in text:
        return
    hits = [('your own identifier (from config.json)', tok)
            for tok in OWN if tok in text]
    for name, rx in RULES:
        m = rx.search(text)
        if m:
            hits.append((name, m.group(0)))
    # Report every problem on the line, so one fix-and-rerun clears the line.
    seen = set()
    for name, found in hits:
        if found in seen:
            continue        # a value caught by two rules is still one problem
        seen.add(found)
        out.append((path, lineno, name, found[:57] + '...' if len(found) > 60 else found))


def git(*args):
    r = subprocess.run(('git',) + args, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise SystemExit(2)
    return r.stdout


def scan_diff(diff):
    """Added lines only. Parses unified diff with zero context."""
    out, path, lineno = [], None, 0
    for line in diff.splitlines():
        if line.startswith('+++ '):
            p = line[4:].strip()
            path = None if p == '/dev/null' else p[2:] if p.startswith('b/') else p
        elif line.startswith('@@'):
            m = re.search(r'\+(\d+)', line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith('+') and not line.startswith('+++'):
            if path and not skipped(path):
                check(path, lineno, line[1:], out)
            lineno += 1
    return out


def scan_files(paths):
    out = []
    for p in paths:
        if skipped(p):
            continue
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f, 1):
                    check(p, i, line.rstrip('\n'), out)
        except (IsADirectoryError, FileNotFoundError):
            continue
    return out


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('files', nargs='*')
    ap.add_argument('--range')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('-h', '--help', action='store_true')
    a = ap.parse_args()
    if a.help:
        print(__doc__)
        return 0

    global OWN
    OWN = own_identifiers(git('rev-parse', '--show-toplevel').strip())

    if a.range:
        findings = scan_diff(git('diff', '-U0', '--no-color', a.range))
        where = 'the commits being pushed'
    elif a.all:
        findings = scan_files(git('ls-files').split('\n'))
        where = 'the tracked files'
    elif a.files:
        findings = scan_files(a.files)
        where = 'those files'
    else:
        findings = scan_diff(git('diff', '--cached', '-U0', '--no-color'))
        where = 'the staged changes'

    if not findings:
        return 0

    print('\nBLOCKED: possible secrets or identifying details in %s.\n' % where,
          file=sys.stderr)
    for path, lineno, name, found in findings:
        print('  %s:%s  %s\n      %s' % (path, lineno, name, found), file=sys.stderr)
    print('\nMove real values into daily-brief/config.json, which is gitignored.'
          '\nIf a hit is a deliberate placeholder, add the marker "%s" to that line.'
          '\nThis check is a safety net, not permission: read the diff yourself too.\n'
          % ALLOW_MARKER, file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
