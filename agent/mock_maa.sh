#!/usr/bin/env bash
# Lightweight mock of maa-cli for local/CI simulations.
# It prints predictable logs and can optionally fail when MOCK_MAA_FAIL=1.
set -euo pipefail

printf '[mock-maa] %s\n' "$(date --iso-8601=seconds)"
printf '[mock-maa] args: %s\n' "$*"

if [[ ${MOCK_MAA_FAIL:-0} -eq 1 ]]; then
  echo "[mock-maa] forced failure via MOCK_MAA_FAIL=1" >&2
  exit 42
fi

action=${1:-}
case "$action" in
  run)
    routine=${2:-daily}
    printf '[mock-maa] executing run %s\n' "$routine"
    ;;
  fight)
    stage=${2:-unknown}
    printf '[mock-maa] fighting stage %s\n' "$stage"
    ;;
  "")
    echo "[mock-maa] no subcommand provided"
    ;;
  *)
    printf '[mock-maa] unknown subcommand %s\n' "$action"
    ;;
 esac

printf '[mock-maa] completed successfully\n'
