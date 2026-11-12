"""Read-only Raspberry Pi network inspection and change planning CLI."""
import argparse
import json
from pathlib import Path
from .network import NetworkManager, NetworkError, plan_changes


def main():
    parser = argparse.ArgumentParser(description='CIVI Raspberry Pi network inspection (does not apply settings)')
    parser.add_argument('--interface', default='eth0')
    parser.add_argument('--plan', type=Path, help='JSON settings to validate and preview; never applied')
    args = parser.parse_args()
    try:
        state = NetworkManager().snapshot(args.interface)
        output = plan_changes(state, json.loads(args.plan.read_text(encoding='utf-8'))) if args.plan else state
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (NetworkError, ValueError, OSError) as error:
        parser.exit(1, f'CIVI Pi: {error}\n')


if __name__ == '__main__':
    main()
