#!/usr/bin/env bash
# Shared git reconcile for Mac scripts — avoids "Need to specify how to reconcile" pull errors.
# Uses fetch + rebase (never bare `git pull`).
set -euo pipefail

mac_git_reconcile() {
  local branch="${1:-$(git branch --show-current)}"
  if [[ -z "$branch" || "$branch" == "HEAD" ]]; then
    branch="${OGZ_GIT_BRANCH:-cursor/cloud-agent-1782842649010-84hv4}"
  fi

  echo "  git fetch origin $branch"
  git fetch origin "$branch"

  if ! git show-ref --verify --quiet "refs/heads/$branch"; then
    if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
      echo "  creating local branch $branch from origin"
      git checkout -B "$branch" "origin/$branch"
    else
      echo "WARN: branch $branch not found on origin"
      return 1
    fi
  elif [[ "$(git branch --show-current)" != "$branch" ]]; then
    echo "  checkout $branch"
    git checkout "$branch"
  fi

  echo "  git rebase origin/$branch"
  git rebase "origin/$branch"
}
