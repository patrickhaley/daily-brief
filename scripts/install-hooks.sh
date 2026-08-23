#!/bin/sh
# Point this clone at the secret-scanning hooks in .githooks/, then audit what is
# already tracked. Safe to re-run: it is idempotent, and re-running just re-audits.
#
#   ./scripts/install-hooks.sh
#
# Exit 0 when enforcement is on and the audit is clean, 1 when the audit finds
# something, 2 when the hooks could not be installed.
set -eu

fail() { printf '%s\n' "$1" >&2; exit 2; }

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail \
  "Not inside a git repository. Run this from your clone of the repo — the copy of
daily-brief/ in your vault is not one, and needs no hooks."

[ -d "$root/.githooks" ] || fail "No .githooks/ directory in $root."

# Relative on purpose: it resolves against each working tree, so one run covers this
# clone and every worktree of it. A separate clone needs its own run.
git config core.hooksPath .githooks

# An export or a zip download loses the executable bit, and a hook that cannot be
# executed fails silently — the same failure mode wearing a different hat.
chmod +x "$root"/.githooks/* 2>/dev/null || true

# Verify rather than assume. Nothing above is allowed to be taken on trust.
configured=$(git config core.hooksPath || true)
[ "$configured" = ".githooks" ] || fail \
  "core.hooksPath is '$configured', expected '.githooks'."

for hook in pre-commit pre-push; do
  [ -f "$root/.githooks/$hook" ] || fail "Missing hook: .githooks/$hook"
  [ -x "$root/.githooks/$hook" ] || fail "Not executable: .githooks/$hook"
done

printf 'Hooks installed: pre-commit and pre-push now scan every commit and push.\n'
printf 'Auditing tracked files...\n'

if python3 "$root/scripts/scan-secrets.py" --all; then
  printf 'Clean. Nothing identifying in the tracked files.\n'
else
  status=$?
  printf 'Audit found something above — fix it before your next commit.\n' >&2
  exit $status
fi
