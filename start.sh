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

launcher=("$python")
needs_authbind=$("$python" -c 'from pathlib import Path; from civi.config import load; c=load("config.toml"); p=Path("/proc/sys/net/ipv4/ip_unprivileged_port_start"); threshold=int(p.read_text()) if p.exists() else 0; print(int(any(port < threshold for port in [c["scpi_port"], c["web_port"], *c["web_extra_ports"]])))')
if [[ "$needs_authbind" == 1 ]]; then
    if ! command -v authbind >/dev/null 2>&1; then
        echo "Privileged port configured. Install/configure authbind; see docs/RPI_HTTPS.md. Run CIVI as your normal user." >&2
        exit 1
    fi
    launcher=(authbind --deep "$python")
    echo "Using authbind for configured privileged ports (CIVI stays under your user)."
fi

password_env=$("$python" -c 'import tomllib; print(tomllib.load(open("config.toml", "rb"))["password_env"])')
if [[ ! "$password_env" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
    echo "Invalid password_env in config.toml." >&2
    exit 1
fi
if "$python" -c 'from civi.config import load; from civi.auth import has_saved_password; import sys; sys.exit(0 if has_saved_password(load("config.toml")) else 1)'; then
    echo "Using saved Web credentials. The environment password is overridden."
elif [[ -z "${!password_env:-}" ]]; then
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
exec "${launcher[@]}" -m civi --config config.toml
