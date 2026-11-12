#!/usr/bin/env bash
# Manually open the attached Pi display. No service or GPIO configuration.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec .venv/bin/python -m civi.pi.panel --config config.toml
