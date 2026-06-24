#!/usr/bin/env bash
# Push the current branch to BOTH remotes:
#   - origin  -> GauntletAI labs (https://labs.gauntletai.com/michaelhabermas/agent-tax)
#   - github  -> GitHub mirror   (https://github.com/MichaelHabermas/agent-tax)  [Render deploys from here]
#
# Usage:
#   scripts/push-all.sh                # push current branch to both
#   scripts/push-all.sh --tags         # forward extra args to each git push
#   scripts/push-all.sh --force-with-lease
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTES=(origin github)

echo "Pushing branch '${BRANCH}' to: ${REMOTES[*]}"
echo

failed=()
for remote in "${REMOTES[@]}"; do
  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    echo "!! remote '${remote}' is not configured — skipping" >&2
    failed+=("$remote")
    continue
  fi
  echo "==> ${remote}  ($(git remote get-url "$remote"))"
  if git push "$remote" "$BRANCH" "$@"; then
    echo "    ok"
  else
    echo "!! push to '${remote}' failed" >&2
    failed+=("$remote")
  fi
  echo
done

if ((${#failed[@]})); then
  echo "Completed with failures: ${failed[*]}" >&2
  exit 1
fi
echo "Pushed to all remotes."
