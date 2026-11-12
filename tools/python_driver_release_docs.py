"""Synchronize draft introduction and inline compliance documents (no hardware I/O)."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'drivers/civi-ic7300'
SOURCE = PACKAGE / 'src/civi_ic7300'
BEGIN = '<!-- BEGIN GENERATED COMPLIANCE -->'
END = '<!-- END GENERATED COMPLIANCE -->'
INTRODUCTION = '___Introduction to CiviIc7300___.md'


def render():
    compliance = (SOURCE / 'COMPLIANCE.md').read_text(encoding='utf-8').rstrip()
    outputs = {SOURCE / INTRODUCTION: (SOURCE / 'Introduction.md').read_text(encoding='utf-8')}
    for path in (PACKAGE / 'README.md', SOURCE / 'README.md'):
        text = path.read_text(encoding='utf-8')
        if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
            raise ValueError(f'Invalid compliance markers in {path}')
        if BEGIN in text:
            before, remaining = text.split(BEGIN)
            _, after = remaining.split(END)
            text = before.rstrip() + '\n\n' + BEGIN + '\n\n' + compliance + '\n\n' + END + after
        else:
            text = text.rstrip() + '\n\n' + BEGIN + '\n\n' + compliance + '\n\n' + END + '\n'
        outputs[path] = text
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for path, expected in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(expected, encoding='utf-8')
    if stale:
        raise SystemExit('Regenerate release docs: ' + ', '.join(stale))


if __name__ == '__main__':
    main()
