"""Export the gateway menu schema for the independent client (no radio I/O)."""

import argparse
import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from civi import menus  # noqa: E402,F401
from civi.commands import CATALOG  # noqa: E402


def render():
    items = []
    for header, spec in CATALOG.items():
        if not header.startswith('RAD:MENU:'):
            continue
        sample = spec.codec.decode(spec.codec.encode(spec.codec.sample()))
        items.append({
            'number': int(header.rsplit(':', 1)[1]), 'header': header,
            'description': spec.description, 'access': spec.access,
            'permission': spec.guard, 'codec': dataclasses.asdict(spec.codec),
            'sample': sample,
        })
    assert len(items) == 216
    return json.dumps({'schema_version': 1, 'model': 'IC-7300', 'items': items},
                      ensure_ascii=False, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'drivers/civi-ic7300/src/civi_ic7300/menu-catalog.json'
    expected = render()
    if args.check:
        if not path.exists() or path.read_text(encoding='utf-8') != expected:
            raise SystemExit('Regenerate with python tools/python_driver_menu_catalog.py')
    else:
        path.write_text(expected, encoding='utf-8')
        print(f'Exported 216 menu definitions to {path.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
