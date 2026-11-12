#!/usr/bin/env bash
# Web password only: local console, no LAN helper or sudo needed.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec .venv/bin/python -m civi.pi.password --config config.toml
