"""Apply the qualified X-T2 message extent to the pinned local X-T20 post source.

Original AI-assisted adapter. Generated post.c is a private upstream derivative,
not a public source release. No dispatcher, event-code or callback acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    data=args.source.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob=='8de17ec8f98fd55fdfc9df04f074c161573d9390'
    text=data.decode()
    needle='unsigned char payload[0x2c];'
    assert text.count(needle)==1
    header=Path(__file__).with_name('xt2_ui_post_message_reference.h')
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/header.name).write_bytes(header.read_bytes())
    text='''/* X-T2 4.41 message-extent adaptation; original queue algorithm below.
 * Runtime dispatch registration, event-code collision and UI lifecycle OPEN. */
#include "xt2_ui_post_message_reference.h"
'''+text.replace(needle,'unsigned char payload[XT2_UI_POST_PAYLOAD_BYTES];')
    text+='\n_Static_assert(sizeof(struct ui_message) == XT2_UI_POST_PACKET_BYTES, "X-T2 post extent");\n'
    (args.output/'post.c').write_text(text)
    report=dict(scope=__doc__,source_git_blob=blob,source_sha256=sha(data),
        reference_header_sha256=sha(header.read_bytes()),output_sha256=sha(text.encode()),
        generator_sha256=sha(Path(__file__).read_bytes()),payload_bytes=68,packet_bytes=76,
        queue_algorithm_changed=False,runtime_qualified=False,hardware_verified=False)
    (args.output/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(source_git_blob=blob,payload_bytes=68,packet_bytes=76,runtime_qualified=False)))


if __name__=='__main__':main()
