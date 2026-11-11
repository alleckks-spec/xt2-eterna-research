"""Negative/ABI controls for compiled cardio callbacks at a declared boundary.

The real library begin/claim/finish/callback-retirement code executes. A pending
open callback is supplied explicitly; no filesystem open or token allocation
success is claimed. Valid handles stop at the native wrapper entry, before I/O.
Original invalid handles execute the actual native wrapper until its trap loop.
Uses the existing native-worker assay, not a new runtime or SD model.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R1
from unicorn.unicorn_py3.unicorn import uclib
from verify_cardio_native_worker import Assay, RAM, JOB, RETURN, sha

ROOT = Path(__file__).resolve().parent


def verify(component, output):
    raw = component.read_bytes()
    build = json.loads(component.with_name('build.json').read_text())
    assert sha(raw) == build['elf_sha256']
    for path, digest in build['dependencies'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    original = build['original']
    stock = (ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    assert sha(stock) == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    m = Assay(stock, raw)
    u = m.u
    m.presence(True)
    u.mem_write(RAM+0x3000, b'X70MOD\0')
    u.mem_write(RAM+0x3100, b'TEST.JSN\0')
    snapshot = u.context_save()
    # Reset the exact fixture between independent original/fixed controls.
    allocated = []
    from elftools.elf.elffile import ELFFile
    import io
    for section in ELFFile(io.BytesIO(raw)).iter_sections():
        if section['sh_flags'] & 2 and section['sh_size']:
            allocated.append((section['sh_addr'], bytes(u.mem_read(section['sh_addr'], section['sh_size']))))
    cases = []
    for op, kind, entry in [(2, 'read', 0xced4b4), (3, 'write', 0xced504), (4, 'write_at', 0xced604)]:
        for status, handle, late in [(0, 0, False), (0, 0x10000000, False),
                (0, 0xffffffff, False), (5, 0, False), (0, 1, False),
                (0, 0x0fffffff, False), (0, 0, True), (0, 0x10000000, True)]:
            u.context_restore(snapshot)
            for address, data in allocated:
                u.mem_write(address, data)
            u.mem_write(JOB, bytes(256))
            assert m.api('x70_cardio_begin', JOB, op, RAM+0x3000, RAM+0x3100) == 0
            bank = m.api('x70_cardio_bank', JOB)
            assert 0 <= bank < 4
            u.mem_write(JOB+20, struct.pack('<I', 4))
            u.mem_write(JOB+40, struct.pack('<I', 64))
            u.mem_write(JOB+52, struct.pack('<I', RAM+0x5000))
            m.api('x70_callback_issued')
            assert m.api('x70_lifetime_live') == 1
            if late:
                m.api('x70_cardio_abandon', JOB)
            wrapper = 'cb_open_read' if op == 2 else 'cb_open_write'
            seen = []
            traps = {0xced4dc, 0xced52c, 0xced57c, 0xced630}
            boundaries = {0xced4b4, 0xced504, 0xced554, 0xced604}
            valid = 0 < handle < 0x10000000
            should_issue = status == 0 and (original or valid)
            def trace(uc, address, size, data):
                if address in boundaries:
                    seen.append(dict(pc=hex(address), handle=uc.reg_read(UC_ARM_REG_R1)))
                    if not original or valid:
                        uc.emu_stop()
                if address in traps:
                    seen.append(dict(trap=hex(address)))
                    uc.emu_stop()
            hook = u.hook_add(UC_HOOK_CODE, trace)
            stopped = False
            try:
                m.api(f'{wrapper}_{bank}', status, handle)
            except AssertionError:
                assert seen and u.reg_read(UC_ARM_REG_PC) != RETURN
                stopped = True
            finally:
                u.hook_del(hook)
            # Stale zero handles were already dropped by the original source.
            if late and handle == 0:
                should_issue = False
            assert bool(seen) == should_issue, (kind, status, handle, late, seen)
            if should_issue:
                assert stopped and seen[0]['handle'] == handle
                assert seen[0]['pc'] == hex(0xced554 if late else entry)
                if original and not valid:
                    assert any('trap' in x for x in seen), seen
            else:
                assert not stopped
                assert m.word(JOB) == 3 and m.word(m.symbols['x70_cardio_active']) == 0
                expected = -1 if late else status if status else -23
                assert m.word(JOB+8) == expected & 0xffffffff
                assert m.api('x70_lifetime_live') == 0
                assert m.api('x70_cardio_bank', JOB) == 0xffffffff
                assert m.api('x70_cardio_busy') == 0
                assert m.word(m.symbols['bank_state']+bank*4) == 0
            cases.append(dict(op=kind, callback_status=status, callback_handle=hex(handle),
                late=late, native_boundary=seen, completed_without_stub=not stopped))
    report = dict(scope=__doc__, status='PASS', original=original, cases=cases,
        elf_sha256=sha(raw), stock_sha256=sha(stock),
        checker_sha256=sha(Path(__file__).read_bytes()),
        harness_sha256=sha((ROOT/'verify_cardio_native_worker.py').read_bytes()),
        runtime=dict(path=str(Path(uclib._name).resolve()),
                     sha256=sha(Path(uclib._name).read_bytes())),
        fixture=dict(native_constructors=True, semaphore_configuration=True,
                     device_presence=True, scratch_call_stack=True,
                     host_cpacr_fpexc=True, task_scheduling=False),
        supplied_pending_open_callback=True, real_filesystem_success=False,
        internal_success_stubs=0, hardware_verified=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(status='PASS', original=original, cases=len(cases), elf=sha(raw))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--component', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    verify(a.component.resolve(), a.output.resolve())
