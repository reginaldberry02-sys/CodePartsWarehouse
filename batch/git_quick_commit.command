# Block B — batch/git_quick_commit.command
#!/bin/bash
set -euo pipefail

REPO_ROOT=""
AUTO_PUSH="yes"

detect_repo_root() {
  if [[ -n "$REPO_ROOT" ]]; then
    echo "$REPO_ROOT"
    return
  fi

  local cur
  cur="$(cd "$(dirname "$0")" && pwd)"

  while [[ "$cur" != "/" ]]; do
    if [[ -d "$cur/.git" ]]; then
      echo "$cur"
      return
    fi
    cur="$(dirname "$cur")"
  done

  echo ""
}

prompt() {
  read -r -p "$1 [$2]: " val
  echo "${val:-$2}"
}

main() {
  root="$(detect_repo_root)"
  [[ -z "$root" ]] && { echo "ERROR: repo root not found"; exit 1; }

  cd "$root"

  git status -sb
  git diff --stat || true

  go="$(prompt "git add -A?" yes)"
  [[ "$go" != "yes" ]] && exit 0

  git add -A
  git diff --cached --stat || true

  msg="$(prompt "commit message" "batch update")"
  git commit -m "$msg"

  if [[ "$AUTO_PUSH" == "yes" ]]; then
    push="$(prompt "git push?" yes)"
    [[ "$push" == "yes" ]] && git push
  fi
}

main "$@"
