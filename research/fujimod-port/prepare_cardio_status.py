"""Extend the frozen X-T2 listing adaptation with native error preservation.

AI-assisted original adapter; generated C remains a private upstream derivative.
Reuse the existing transport/bank/hold adaptation and job result API. Only the
native end/no-match code becomes successful completion; other errors survive.
"""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_cardio_listing import prepare as prepare_listing


def sha(b):return hashlib.sha256(b).hexdigest()


def prepare(source,output,original=False):
    assert not original,'Compare with the frozen listing component; do not use --original here.'
    path=prepare_listing(source,output,False);out=path.parent
    parent=(out/'preparation.json').read_bytes();text=path.read_text()
    scope=text.index('enum { FIND_FIRST = XT2_FIND_FIRST')
    start=text.index('static void cb_list_body(int bank, int status)\n{',scope)
    end=text.index('\n#endif',start);body=text[start:end]
    status_branch=body.index('if (status != 0)')
    position=body.index('x70_cardio_finish(job, 0);',status_branch)
    assert position<body.index('return;',status_branch)
    body=body[:position]+body[position:].replace('x70_cardio_finish(job, 0);',
        'x70_cardio_finish(job, xt2_listing_result(status));',1)
    old='if (storage_media_ready(0) != 0 || send_find(FIND_NEXT, &find_next, sizeof find_next) != 0)'
    assert body.count(old)==1
    body=body.replace(old,'if ((status = storage_media_ready(0)) != 0 ||\n        (status = send_find(FIND_NEXT, &find_next, sizeof find_next)) != 0)')
    old='x70_cardio_finish(job, 0);      /* keep what was listed */'
    assert body.count(old)==1
    body=body.replace(old,'x70_cardio_finish(job, status);')
    text=text[:start]+body+text[end:]
    header=Path(__file__).with_name('xt2_cardio_status_reference.h')
    (out/header.name).write_bytes(header.read_bytes())
    text='#include "xt2_cardio_status_reference.h"\n'+text;path.write_text(text)
    report=dict(scope=__doc__,parent_preparation_sha256=sha(parent),parent_preparation=json.loads(parent),
        generator_sha256=sha(Path(__file__).read_bytes()),header_sha256=sha(header.read_bytes()),
        output_sha256=sha(text.encode()),hardware_verified=False)
    (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(prepare(a.source,a.output))


if __name__=='__main__':main()
