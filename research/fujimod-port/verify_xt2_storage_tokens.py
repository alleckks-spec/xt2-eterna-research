"""Bounded native X-T2 open-token exhaustion, using an existing component assay.

AI-assisted original checker. Execute the real allocator/release routines after
existing native constructors and semaphore configuration. This does not run the
open worker on mounted FAT, invent a successful open callback or test hardware.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]
sys.path[:0]=[str(WORKSPACE/'scripts'),str(ROOT)]
from verify_cardio_native_worker import Assay


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,default=WORKSPACE/'firmware/research/xt2-stock-sd-unverified/ffboot.bin')
    parser.add_argument('--component',type=Path,default=ROOT/'cardio-status-component-unverified/component.elf')
    parser.add_argument('--output',type=Path,default=ROOT/'minimal-storage-check-unverified/tokens.json')
    args=parser.parse_args()
    stock=args.stock.read_bytes()
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    component=args.component.read_bytes()
    build=json.loads(args.component.with_name('build.json').read_text())
    assert sha(component)==build['elf_sha256']
    m=Assay(stock,component)
    assert m.word(0x9c3548)==0 and m.word(0x9c225c)==0
    allocated=[m.call(0x968638) for _ in range(16)]
    assert allocated==list(range(1,17))
    assert list(int.from_bytes(m.u.mem_read(0x9c221c+4*i,4),'little') for i in range(16))==allocated
    exhausted=m.call(0x968638)
    assert exhausted==0
    m.call(0x968764,allocated[3])
    assert m.word(0x9c221c+12)==0
    reused=m.call(0x968638)
    assert reused!=0 and reused not in allocated and m.word(0x9c221c+12)==reused
    assert not m.clock.errors and m.clock.elapsed_ticks==0
    result=dict(scope=__doc__,status='PASS: native sixteen-token exhaustion and release',
        allocated=allocated,exhaustion_result=exhausted,reallocated=reused,
        allocator='0x968638',release='0x968764',native_semaphore_configuration=len(m.semaphore_configuration),
        actual_scheduler=False,mounted_FAT_open=False,open_success_zero_callback_reproduced=False,
        existing_assay_boundary='Native constructor/semaphore bootstrap entry and scratch call stacks; no MMIO time advancement or internal API success stubs.',
        component_sha256=sha(component),stock_sha256=sha(stock),
        checker_sha256=sha(Path(__file__).read_bytes()),assay_sha256=sha(Path(sys.modules[Assay.__module__].__file__).read_bytes()),
        hardware_verified=False)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','exhaustion_result','reallocated')}))


if __name__=='__main__':
    main()
