#!/usr/bin/env bash
# Manual desktop launch only. No autostart or service registration.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! .venv/bin/python -m civi.pi.desktop --config "$PWD/config.toml" "$@"; then
    if [[ -t 0 ]]; then read -r -p "CIVI launch failed. Press Enter to close." _; fi
    exit 1
fi
