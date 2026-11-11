"""Execute native recall/edit WB copies to their first journal boundary.

Reuses the initialized native UI fixture on an exact ordinary artifact. Raw
custom records and selected slots are explicit valid-field/canary inputs.
No journal transport success or hardware apply is supplied. Tail preservation
on these paths is not a global spare-byte ownership claim.
"""
import argparse
import hashlib
import json
import struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_INVALID
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
import verify_full_storage_guard as common

ROOT = Path(__file__).resolve().parent
BASE = 0x11937bc
SHADOW_DELTA = 0x1724


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'save-data-menu-native-build-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'wb-lifecycle-check-unverified/recall-edit.json')
    parser.add_argument('--complete', action='store_true')
    args = parser.parse_args()
    common.BUILD = args.build
    (u, symbols, call, api, clock, init, exceptions), setup = common.fixture_machine(True)
    stock = (ROOT.parents[1] / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    audit_path = ROOT / 'wb-build-unverified/binding-audit-corrected.json'
    audit = json.loads(audit_path.read_text())
    bindings = audit['bindings']
    assert bindings['custom_slot_records'] == BASE and bindings['wb'] == 0x1cf
    reds = {int(key): value for key, value in audit['red_properties_by_setting_code'].items()}
    assert set(reds) == set(range(12))
    before_cpu = u.context_save()
    journal, faults, recent = [], [], deque(maxlen=48)
    pending_cache, cache_roundtrips = [], []
    bank_copies = []
    writes, tail_reads = [], []
    active = False
    case = {}
    def at_journal(uc, address, size, data):
        pointer = uc.reg_read(UC_ARM_REG_R0)
        descriptor = list(struct.unpack('<3I', uc.mem_read(pointer, 12)))
        journal.append(descriptor)
        if args.complete:
            source, length, offset = descriptor
            pending_cache.append((bytes(uc.mem_read(source, length)), offset))
        else:
            uc.emu_stop()
    def cache_return(uc, address, size, data):
        if not active or not args.complete:
            return
        expected, offset = pending_cache.pop()
        assert uc.reg_read(UC_ARM_REG_R0) == 0
        actual = bytes(uc.mem_read(0x122064c + offset, len(expected)))
        assert actual == expected
        cache_roundtrips.append(dict(offset=offset, bytes=len(expected), sha256=sha(expected),
            native_return=0, cache_bytes_equal=True))
    u.hook_add(UC_HOOK_CODE, at_journal, begin=0xcf8b74, end=0xcf8b74)
    u.hook_add(UC_HOOK_CODE, cache_return, begin=0xcf8b90, end=0xcf8b90)
    def copy_entry(uc, address, size, data):
        if active:
            values = [uc.reg_read(reg) for reg in [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2]]
            if values == [0x1193fa0, 0x119287c, 0x1724]:
                bank_copies.append(dict(destination=values[0], source=values[1], bytes=values[2],
                    caller_return=hex(uc.reg_read(UC_ARM_REG_LR))))
    u.hook_add(UC_HOOK_CODE, copy_entry, begin=0xcf2bbc, end=0xcf2bbc)
    u.hook_add(UC_HOOK_CODE, lambda uc, address, size, data: recent.append(hex(address)))
    def invalid(uc, access, address, size, value, data):
        faults.append(dict(pc=hex(uc.reg_read(UC_ARM_REG_PC)), address=hex(address), size=size,
            access=access, case=case.copy()))
        return False
    u.hook_add(UC_HOOK_MEM_INVALID, invalid)
    def write(uc, access, address, size, value, data):
        if active:
            writes.append((uc.reg_read(UC_ARM_REG_PC), address, size))
    def read(uc, access, address, size, value, data):
        if active and any(BASE + delta + index * 256 + 0x84 <= address < BASE + delta + (index + 1) * 256
                          for delta in [0, SHADOW_DELTA] for index in range(7)):
            tail_reads.append((uc.reg_read(UC_ARM_REG_PC), address, size))
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.hook_add(UC_HOOK_MEM_READ, read)
    records = []
    record_count = 7 if args.complete else 8
    for operation, entry in [('recall', bindings['custom_recall']), ('edit', bindings['custom_edit_load'])]:
        for slot in range(7):
            for mode in range(12):
                case = dict(operation=operation, raw_slot=slot, wb_setting_code=mode)
                u.context_restore(before_cpu)
                for index in range(record_count):
                    image = bytearray(stock[0xf7f12c + (index % 7) * 256:0xf7f12c + (index % 7 + 1) * 256])
                    image[0x2d] = 0  # Valid stock PROVIA, independent of volatile extra films.
                    image[0x66:0x80] = (('Slot ' + str(index)).encode() + b'\0').ljust(26, b'\0')
                    image[0x84:] = bytes((index * 29 + offset) % 256 for offset in range(124))
                    u.mem_write(BASE + index * 256, bytes(image))
                    shadow = bytearray(image)
                    shadow[0x84:] = bytes((index * 31 + offset + 71) % 256 for offset in range(124))
                    u.mem_write(BASE + SHADOW_DELTA + index * 256, bytes(shadow))
                call(bindings['backup_set_explicit_context_body'], 0x1cf, mode, 0, slot, task=True)
                assert call(bindings['backup_get'], 0x1cf, 0, 0, slot, task=True) == mode
                # Distinct ordinary/live per-mode values are native property
                # inputs, not pair bytes invented inside the custom record.
                red, blue = (mode + 2) % 19, (mode * 2 + 3) % 19
                for prop, value in [(reds[mode], red), (reds[mode] + 13, blue)]:
                    call(bindings['backup_set_explicit_context_body'], prop, value, 0, 7, task=True)
                    assert call(bindings['backup_get'], prop, 0, 0, 7, task=True) == value
                before = {delta: bytes(u.mem_read(BASE + delta, record_count * 256)) for delta in [0, SHADOW_DELTA]}
                u.mem_write(bindings['ui_info'] + bindings['selected_slot_offset'], bytes([slot]))
                journal.clear(); writes.clear(); tail_reads.clear(); recent.clear(); cache_roundtrips.clear(); bank_copies.clear()
                returned = None
                active = True
                try:
                    returned = call(entry, *([slot] if operation == 'recall' else []), task=True)
                except AssertionError:
                    assert not args.complete, (case, list(recent), faults)
                    assert u.reg_read(UC_ARM_REG_PC) == 0xcf8b74, (case, list(recent), faults)
                finally:
                    active = False
                assert journal and (args.complete or u.reg_read(UC_ARM_REG_PC) == 0xcf8b74), (case, journal, list(recent))
                assert journal[0] == [0x119288c, 0xe74, 0x10], (case, journal)
                if args.complete:
                    assert len(cache_roundtrips) == len(journal) and not pending_cache
                for delta in [0, SHADOW_DELTA]:
                    actual_records = bytes(u.mem_read(BASE + delta, record_count * 256))
                    if args.complete and operation == 'edit' and delta == SHADOW_DELTA:
                        assert bank_copies and actual_records == before[0], (case, bank_copies)
                        continue
                    if actual_records != before[delta]:
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        args.output.with_name('recall-edit-complete-discovery.json').write_text(json.dumps(dict(
                            status='NOT PASS', case=case, delta=delta,
                            differences=[dict(index=index // 256, offset=hex(index % 256), before=old, after=new)
                                for index, (old, new) in enumerate(zip(before[delta], actual_records)) if old != new],
                            stores=[dict(pc=hex(pc), address=hex(address), bytes=size) for pc, address, size in writes
                                if BASE + delta <= address < BASE + delta + record_count * 256]), indent=2) + '\n')
                    assert actual_records == before[delta], (case, delta)
                if args.complete and operation == 'edit':
                    assert bank_copies
                    assert all(0xcf2bbc <= pc < 0xcf2da0 and BASE <= address < BASE + 7 * 256
                        for pc, address, size in tail_reads), (case, tail_reads)
                else:
                    assert not tail_reads, (case, tail_reads)
                restored_mode = call(bindings['backup_get'], 0x1cf, 0, 0, 7, task=True)
                restored_pair = [call(bindings['backup_get'], prop, 0, 0, 7, task=True)
                    for prop in [reds[mode], reds[mode] + 13]]
                assert restored_mode == mode and restored_pair == [red, blue], (case, restored_mode, restored_pair)
                records.append(dict(**case, journal_descriptor=journal[0], copied_wb_mode=restored_mode,
                    ordinary_pair_unchanged=restored_pair, primary_records_unchanged=True,
                    shadow_outcome='native full-bank snapshot' if bank_copies else 'unchanged',
                    full_bank_copies=list(bank_copies), tail84_plus_copy_reads=len(tail_reads), tail84_plus_other_reads=0,
                    cpu_store_events=len(writes),
                    record_sha256=sha(before[0][slot * 256:(slot + 1) * 256]), stopped_before_transport=not args.complete,
                    complete_native_call_return=returned, native_cache_roundtrips=list(cache_roundtrips)))
    assert not faults
    report = dict(scope=__doc__, status='PASS', cases=records,
        elf_sha256=sha((args.build / 'mods.elf').read_bytes()), stock_sha256=sha(stock),
        checker_sha256=sha(Path(__file__).read_bytes()), binding_audit_sha256=sha(audit_path.read_bytes()),
        setup=setup, init_calls=init, native_vfp_exceptions=exceptions,
        primary_and_shadow_custom_records_checked=record_count,
        native_journal_cache_api_executed=args.complete, complete_native_call=args.complete,
        physical_journal_io_verified=False, hardware_apply_verified=False,
        spare_tail_qualified=False, wb_hook_installed=False, hardware_verified=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', cases=len(records), elf=report['elf_sha256'])))


if __name__ == '__main__':
    main()
