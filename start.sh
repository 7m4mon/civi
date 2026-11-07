#!/usr/bin/env bash
# Start CIVI in the foreground. No service or automatic startup is installed.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python=".venv/bin/python"

if [[ ! -x "$python" ]]; then
    echo "Missing .venv/bin/python. Create the virtual environment and install CIVI first." >&2
    exit 1
fi
if [[ ! -f config.toml ]]; then
    echo "Missing config.toml. Copy config.example.toml and configure it first." >&2
    exit 1
fi

password_env=$("$python" -c 'import tomllib; print(tomllib.load(open("config.toml", "rb"))["password_env"])')
if [[ ! "$password_env" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
    echo "Invalid password_env in config.toml." >&2
    exit 1
fi
if [[ -z "${!password_env:-}" ]]; then
    read -r -s -p "CIVI Web password (not Linux/sudo; at least 12 characters): " password
    printf '\n'
    if [[ ${#password} -lt 12 ]]; then
        echo "The password must contain at least 12 characters." >&2
        exit 1
    fi
    export "$password_env=$password"
    unset password
else
    echo "Using the existing CIVI Web password from environment variable $password_env."
fi

echo "Web login username: admin"
echo "Starting CIVI. Press Ctrl+C to stop."
exec "$python" -m civi --config config.toml
