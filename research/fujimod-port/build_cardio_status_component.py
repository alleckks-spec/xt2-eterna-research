"""Reuse the existing component builder with only the status adapter extended.

AI-assisted original glue. Needs the published base listing builder/adapter,
private pinned sources, Clang and LLD. Not an ordinary SD build or camera claim.
Compare against the frozen prior listing component, not --original.
"""
import hashlib
import json
import sys
from pathlib import Path
import build_cardio_listing_component as base
from prepare_cardio_status import prepare


def main():
    base.prepare=prepare
    base.main()
    # The reused builder pins its own dependencies. Pin this extension too.
    output=Path(sys.argv[sys.argv.index('--output')+1]).resolve()
    report=json.loads((output/'build.json').read_text())
    paths=[Path(__file__),Path(__file__).with_name('prepare_cardio_status.py'),
           Path(__file__).with_name('xt2_cardio_status_reference.h')]
    report['extension_dependencies']={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
