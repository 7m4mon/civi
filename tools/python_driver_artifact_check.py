"""Check client wheel/sdist contents and metadata; not an IVI conformance test."""

import argparse
import ast
import hashlib
import json
from email.parser import BytesParser
from pathlib import Path
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'drivers/civi-ic7300'
SOURCE = PACKAGE / 'src/civi_ic7300'
INTRODUCTION = '___Introduction to CiviIc7300___.md'


def check(wheel, sdist=None):
    project = tomllib.loads((PACKAGE / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    required = {p.name for p in SOURCE.iterdir() if p.suffix in ('.py', '.md', '.json')}
    required.add('py.typed')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        missing = required - {n.removeprefix('civi_ic7300/') for n in names if n.startswith('civi_ic7300/')}
        if missing:
            raise ValueError('Wheel missing: ' + ', '.join(sorted(missing)))
        metadata_names = [n for n in names if n.endswith('.dist-info/METADATA')]
        if len(metadata_names) != 1:
            raise ValueError('Expected exactly one wheel metadata record')
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        if metadata['Name'] != project['name'] or metadata['Version'] != project['version']:
            raise ValueError('Wheel name/version disagrees with pyproject.toml')
        if metadata['Requires-Python'] != project['requires-python']:
            raise ValueError('Wrong Python requirement')
        keywords = {s.strip() for s in metadata.get('Keywords', '').split(',')}
        if not {'CIVI Project', 'CIVI/IC-7300'} <= keywords:
            raise ValueError('Instrument identity missing from wheel keywords')
        if metadata.get_all('Requires-Dist'):
            raise ValueError('Unexpected third-party runtime dependency')
        init = ast.parse(archive.read('civi_ic7300/__init__.py').decode('utf-8'))
        versions = [ast.literal_eval(node.value) for node in init.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets)]
        if versions != [project['version']]:
            raise ValueError('Import version disagrees with wheel metadata')
        if archive.read('civi_ic7300/py.typed'):
            raise ValueError('py.typed must be empty')
        compliance = archive.read('civi_ic7300/COMPLIANCE.md').decode('utf-8').replace('\r\n', '\n').strip()
        readme = archive.read('civi_ic7300/README.md').decode('utf-8').replace('\r\n', '\n')
        description = metadata.get_payload(decode=True).decode('utf-8').replace('\r\n', '\n')
        if compliance not in readme or compliance not in description:
            raise ValueError('Compliance text missing from package/distribution README')
        if INTRODUCTION not in required:
            raise ValueError('Draft introduction filename missing')
        if 'Not IVI-conformant; not registered.' not in compliance:
            raise ValueError('Experimental compliance status missing')
        public = json.loads(archive.read('civi_ic7300/public-api.json'))
        if public['client_version'] != project['version'] or not public['classes']:
            raise ValueError('Public help version/content mismatch')
        notice = archive.read('civi_ic7300/IVI_NOTICE.md').decode('utf-8').replace('\r\n', '\n')
        notice_body = notice.split('\n\n', 1)[1].split('\n\nSource:', 1)[0]
        provenance = json.loads(archive.read('civi_ic7300/notice-source.json'))
        reference = archive.read('civi_ic7300/REFERENCE.md').decode('utf-8').replace('\r\n', '\n')
        if hashlib.sha256(notice_body.encode()).hexdigest() != provenance['notice_sha256'] or notice_body not in reference:
            raise ValueError('Notice integrity/visibility mismatch')
        if 'EVIDENCE.md' not in reference:
            raise ValueError('Verification scope missing from help')
        if sdist is not None:
            with tarfile.open(sdist, 'r:gz') as source:
                for filename in required:
                    entries = [n for n in source.getnames() if n.endswith('/src/civi_ic7300/' + filename)]
                    if len(entries) != 1:
                        raise ValueError('Source distribution missing/duplicate file: ' + filename)
                    member = source.extractfile(entries[0])
                    if member is None or member.read() != archive.read('civi_ic7300/' + filename):
                        raise ValueError('Source/wheel file mismatch: ' + filename)
    return project['version'], len(required)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wheel', type=Path)
    parser.add_argument('--sdist', type=Path)
    args = parser.parse_args()
    version, count = check(args.wheel, args.sdist)
    print(f'Client {version}: {count} package files, metadata and embedded compliance OK; IVI conformity not evaluated')


if __name__ == '__main__':
    main()
