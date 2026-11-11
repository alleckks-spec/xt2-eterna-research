"""Native custom-record SAVE film serialization on the exact common artifact.

Select through the native property hook, then execute the original SAVE doorway
to its first journal submission. Stop before the journal transport; no successful
NAND write, custom-slot recall, independent per-slot extra choice or camera claim.
Current UI/mode, selected raw slot index and neighboring-record canaries are
explicit fixtures. Uses the existing native UI machine and native SAVE body.
"""
import argparse
import hashlib
import json
import struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_INVALID
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0
import verify_full_storage_guard as common

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'save-data-menu-native-build-unverified')
    p.add_argument('--output', type=Path, default=ROOT/'custom-slot-records7-check-unverified/verification.json')
    a = p.parse_args()
    common.BUILD = a.build
    (u, symbols, call, api, clock, init, exceptions), setup = common.fixture_machine(True)
    word = lambda address: struct.unpack('<I', u.mem_read(address, 4))[0]
    stock = (ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    base = 0x11937bc
    # Primary slot layout and film offset are qualified by the prior native
    # scalar-offset audit. Shadow base is not assumed or written here.
    qualified = json.loads((ROOT/'wb-build-unverified/scalar-offset-audit.json').read_text())
    film_rows = [r for r in qualified['rows'] if '0x1fc' in r['properties']]
    assert len(film_rows) == 1 and film_rows[0]['slot_relative_offset'] == '0x2d'
    before_cpu = u.context_save()
    cases = []
    journal = []
    faults = []
    recent = deque(maxlen=48)
    u.hook_add(UC_HOOK_CODE, lambda uc, address, size, data: recent.append(hex(address)))
    def invalid(uc, access, address, size, value, data):
        faults.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)), address=hex(address),
                           bytes=size, access=access, selected_key=key, raw_slot=slot,
                           lr=hex(uc.reg_read(UC_ARM_REG_LR))))
        return False
    u.hook_add(UC_HOOK_MEM_INVALID, invalid)
    def stop(uc, address, size, data):
        pointer = uc.reg_read(UC_ARM_REG_R0)
        journal.append(list(struct.unpack('<3I', uc.mem_read(pointer, 12))))
        uc.emu_stop()
    hook = None
    try:
        for key in [0, 32, 33, 34, 35, 36, 37]:
            for slot in range(7):
                u.context_restore(before_cpu)
                # Do not create a successful settings state: this is the same
                # declared REC/current-settings boundary as the native SAVE assay.
                u.mem_write(symbols['ui_mode'], b'\x03')
                call(0x154b700, 0x1fc, key, task=True)
                assert word(symbols['film_choice_key']) == key
                assert call(0xb510b8, 0x1fc, 0, task=True) == 0
                # There are seven native custom records. The following block
                # is native UI/backup state, not an eighth record fixture.
                for index in range(7):
                    image = bytearray(stock[0xf7f12c+index*256:0xf7f12c+(index+1)*256])
                    assert len(image) == 256
                    image[0x2d] = 3  # A valid stock film, distinct from PROVIA0.
                    u.mem_write(base+index*256, bytes(image))
                before = bytes(u.mem_read(base, 7*256))
                u.mem_write(0x120d8a0+0xee93, bytes([slot]))
                outer_sp = u.reg_read(UC_ARM_REG_SP)
                u.reg_write(UC_ARM_REG_LR, 0x800f000)
                journal.clear()
                hook = u.hook_add(UC_HOOK_CODE, stop, begin=0xcf8b74, end=0xcf8b74)
                try:
                    u.emu_start(0x1543e20, 0x800f000, count=1_000_000)
                except Exception:
                    a.output.parent.mkdir(parents=True, exist_ok=True)
                    a.output.with_name('discovery.json').write_text(json.dumps(dict(
                        status='NOT PASS', faults=faults, completed_cases=cases,
                        pc=hex(u.reg_read(UC_ARM_REG_PC)), recent=list(recent), setup=setup), indent=2)+'\n')
                    raise
                u.hook_del(hook)
                hook = None
                assert u.reg_read(UC_ARM_REG_PC) == 0xcf8b74 and len(journal) == 1
                record = base+slot*256
                assert journal[0] == [record+4, 256, 0xf44+(slot << 8)], (key, slot, journal[0], hex(record))
                after = bytes(u.mem_read(base, 7*256))
                assert after[slot*256+0x2d] == 0
                for index in range(7):
                    if index != slot:
                        assert after[index*256:(index+1)*256] == before[index*256:(index+1)*256]
                assert word(symbols['film_choice_key']) == key
                cases.append(dict(selected_key=key, raw_custom_slot=slot,
                    native_film_byte=0, journal_descriptor=journal[0],
                    record_sha256=sha(after[slot*256:(slot+1)*256]),
                    neighboring_primary_records_unchanged=True,
                    stopped_before_transport=True, borrowed_outer_sp=hex(outer_sp)))
    finally:
        if hook is not None:
            u.hook_del(hook)
    report = dict(scope=__doc__, status='PASS', cases=cases,
        elf_sha256=sha((a.build/'mods.elf').read_bytes()),
        stock_sha256=sha(stock), checker_sha256=sha(Path(__file__).read_bytes()),
        setup=setup, init_calls=init, native_vfp_exceptions=exceptions,
        raw_slot_indices=list(range(7)), ui_label_mapping_qualified=False,
        custom_record_count=7, following_ui_block_initialized=False,
        film_scalar_audit_sha256=sha((ROOT/'wb-build-unverified/scalar-offset-audit.json').read_bytes()),
        actual_journal_transport=False, independent_extra_choice_per_slot=False,
        hardware_verified=False)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(status='PASS', cases=len(cases), elf=report['elf_sha256'])))


if __name__ == '__main__':
    main()
