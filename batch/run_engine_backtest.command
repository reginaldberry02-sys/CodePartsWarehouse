# Block A — batch/run_engine_backtest.command
#!/bin/bash
set -euo pipefail

REPO_ROOT=""
ENGINE_CMD='echo "SET ENGINE_CMD" && exit 1'
LOG_DIR_NAME="logs_engine_backtest"

ts() { date "+%Y-%m-%d_%H-%M-%S"; }

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

main() {
  root="$(detect_repo_root)"
  [[ -z "$root" ]] && { echo "ERROR: repo root not found"; exit 1; }

  cd "$root"
  mkdir -p "$LOG_DIR_NAME"

  log_file="$LOG_DIR_NAME/engine_backtest_$(ts).log"
  bash -lc "$ENGINE_CMD" 2>&1 | tee "$log_file"
}

main "$@"
