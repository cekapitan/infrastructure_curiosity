#!/bin/sh

set -eu

umask 077

readonly SAFE_PATH="/Users/codyes18/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
readonly REPO_ROOT="/Users/codyes18/workspace/github.com/cekapitan/infrastructure_curiosity"
readonly PROMPT_PATH="$REPO_ROOT/automation/WEEKLY_PROMPT.md"
readonly LOCK_DIR="${TMPDIR:-/tmp}/infrastructure-curiosity-weekly.lock"
readonly RUN_PARENT="/Users/codyes18/workspace/worktrees"
readonly RUN_PATH="$RUN_PARENT/infrastructure_curiosity-weekly"
readonly TRUST_OVERRIDE='projects."/Users/codyes18/workspace/worktrees/infrastructure_curiosity-weekly".trust_level="trusted"'

PATH="$SAFE_PATH"
export PATH

run_dir=""
completed=0

cleanup() {
  if [ "$completed" -eq 1 ] && [ -n "$run_dir" ]; then
    git -C "$REPO_ROOT" worktree remove --force "$run_dir" >/dev/null 2>&1 || true
  elif [ -n "$run_dir" ]; then
    printf '%s\n' "Weekly run failed; preserved worktree for inspection: $run_dir" >&2
  fi
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}

trap cleanup EXIT HUP INT TERM

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  printf '%s\n' "A weekly infrastructure-curiosity run is already active: $LOCK_DIR" >&2
  exit 1
fi

if [ ! -f "$PROMPT_PATH" ] || [ ! -x "$REPO_ROOT/.codex/bin/publish-weekly-pr" ]; then
  printf '%s\n' "The weekly prompt or trusted publisher is missing." >&2
  exit 1
fi

if [ "$(git -C "$REPO_ROOT" branch --show-current)" != "main" ]; then
  printf '%s\n' "The primary checkout must be on main before a scheduled run." >&2
  exit 1
fi

if [ -n "$(git -C "$REPO_ROOT" status --porcelain=v1)" ]; then
  printf '%s\n' "The primary checkout has uncommitted changes; refusing to schedule over them." >&2
  exit 1
fi

git -C "$REPO_ROOT" fetch --prune origin main
git -C "$REPO_ROOT" merge --ff-only origin/main

if [ -e "$RUN_PATH" ]; then
  printf '%s\n' "The fixed weekly worktree already exists; inspect the prior failed run: $RUN_PATH" >&2
  exit 1
fi
mkdir -p "$RUN_PARENT"
run_dir="$RUN_PATH"
git -C "$REPO_ROOT" worktree add --detach "$run_dir" origin/main

/usr/bin/env -i \
  HOME="$HOME" \
  USER="${USER:-}" \
  LOGNAME="${LOGNAME:-${USER:-}}" \
  PATH="$SAFE_PATH" \
  TMPDIR="${TMPDIR:-/tmp}" \
  LANG="${LANG:-en_US.UTF-8}" \
  LC_ALL="${LC_ALL:-}" \
  CODEX_HOME="${CODEX_HOME:-$HOME/.codex}" \
  codex exec \
    --ephemeral \
    --cd "$run_dir" \
    --sandbox workspace-write \
    --config 'approval_policy="never"' \
    --config 'sandbox_workspace_write.network_access=true' \
    --config "$TRUST_OVERRIDE" \
    --search \
    --color never \
    - <"$PROMPT_PATH"

if [ -n "$(git -C "$run_dir" status --porcelain=v1)" ]; then
  printf '%s\n' "Codex exited with unpublished changes; preserving the worktree." >&2
  exit 1
fi

published_branch="$(git -C "$run_dir" branch --show-current)"
case "$published_branch" in
  "")
    printf '%s\n' "The weekly run did not publish its required dated brief." >&2
    exit 1
    ;;
  automation/infrastructure-curiosity-*)
    gh pr view "$published_branch" \
      --repo cekapitan/infrastructure_curiosity \
      --json url,state \
      --jq 'select(.state == "OPEN" or .state == "MERGED") | .url' >/dev/null || {
        printf '%s\n' "The weekly branch exists without a visible pull request." >&2
        exit 1
      }
    ;;
  *)
    printf '%s\n' "The weekly run ended on an unexpected branch: $published_branch" >&2
    exit 1
    ;;
esac

completed=1
