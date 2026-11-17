"""Read back the two installed SD files; never write to the card.

Usage: python3 CHECK-CARD.py /Volumes/NAME
Run the copy beside this package's SD-FILES.json.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('card_root', type=Path)
    args = parser.parse_args()
    records = json.loads(Path(__file__).with_name('SD-FILES.json').read_text())
    assert set(records) == {'ffboot.bin', 'ffsys.bin'}
    valid = True
    for name, expected in records.items():
        path = args.card_root/name
        if not path.is_file():
            print(f'FAIL {name}: missing file')
            valid = False
            continue
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                h.update(block)
        actual = h.hexdigest()
        ok = actual == expected['sha256'] and path.stat().st_size == expected['bytes']
        print(f'{"PASS" if ok else "FAIL"} {name}: {actual}')
        valid &= ok
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
