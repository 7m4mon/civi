#!/usr/bin/env bash
# Local keyboard/display recovery only; no service or automatic startup.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec .venv/bin/python -m civi.pi.lci --config config.toml
