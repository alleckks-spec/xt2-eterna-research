"""Backport the existing PR471 per-bank recorded callback issue mechanism.

Only task-issue recording/polling is enabled. The already-qualified X-T2
listing/status/open-handle derivatives remain. No donor addresses, timing,
GPIO gates, timeout/retry policy, DMA or new queue/runtime are introduced.
Private upstream derivative output; original transformer is publication-safe.
"""
import hashlib
import json
from pathlib import Path
from build_modular_candidate import ROOT,sha
BASE=ROOT/'wb-usb-date-build-unverified'
INPUTS=ROOT/'cardio-task-issue-inputs'
UPSTREAM=ROOT/'cardio-task-issue-upstream-inputs/cardio.c'


def prepare():
 receipt=json.loads((BASE/'preparation.json').read_text())
 assert sha((BASE/'mods.elf').read_bytes())=='18d06d6afe79b67dba7d9fae33ed0586d5d941a4ec40122502b8bc5d85f331d0'
 source=ROOT/'full-storage-guard-inputs/cardio.c';assert sha(source.read_bytes())==receipt['source_sha256'][str(source)]
 raw=UPSTREAM.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='231d78c80ca3e503ce4f28032bcc62a7602932e8'
 upstream=raw.decode();start=upstream.index('#ifdef XPP_CARDIO_TASK_ISSUE\n');end=upstream.index('BANKED1(cb_close_read)',start)
 task_block=upstream[start:end]
 original=source.read_text();begin=original.index('#define BANKED1(name)');end=original.index('BANKED1(cb_close_read)',begin)
 text=original[:begin]+'/* PR471 task-issue only: callbacks record; existing cardio polls run bodies. */\n#define XPP_CARDIO_TASK_ISSUE 1\n'+task_block+original[end:]
 for anchor in ['int x70_cardio_card_ready(void)\n{','int x70_cardio_busy(void)\n{']:
  assert text.count(anchor)==1;text=text.replace(anchor,anchor+'\n    issue_recorded();')
 INPUTS.mkdir(exist_ok=True);path=INPUTS/'cardio.c';path.write_text(text)
 # Preserve target-qualified listing and status reference headers, byte-for-byte.
 for name in ['xt2_cardio_status_reference.h','xt2_cardio_listing_reference.h']:
  (INPUTS/name).write_bytes((source.parent/name).read_bytes())
 result=dict(scope=__doc__,upstream_commit='2e2aa8af51526f81ec22036502b02881507dcd00',upstream_blob='231d78c80ca3e503ce4f28032bcc62a7602932e8',
  upstream_sha256=sha(raw),parent_source=str(source),parent_source_sha256=sha(source.read_bytes()),
  source_sha256=sha(path.read_bytes()),generator_sha256=sha(Path(__file__).read_bytes()),recorded_callback_issue=True,
  timeout_retry_implemented=False,hardware_verified=False)
 (INPUTS/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
 return path,result


if __name__=='__main__':prepare()
