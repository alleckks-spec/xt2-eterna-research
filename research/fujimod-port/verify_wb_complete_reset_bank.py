"""Complete native defaults/reset and bank lifetime with canonical seven records.

Native default-copy calls prepare valid ordinary custom fields. Canaries then
track only the seven custom-record tails. Native NV cache and bank operations
execute without a physical NAND or API success substitute.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR
from verify_wb_recall_edit_lifecycle import ROOT, BASE, SHADOW_DELTA, common, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'save-data-menu-native-build-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'wb-lifecycle-check-unverified/reset-bank-complete.json')
    args = parser.parse_args()
    audit = json.loads((ROOT / 'wb-build-unverified/binding-audit-corrected.json').read_text())
    binding = audit['bindings']; reds = {int(key): value for key, value in audit['red_properties_by_setting_code'].items()}
    cases = []
    for operation in ['defaults', 'reset_edit', 'bank_cancel']:
        for slot in (range(7) if operation != 'bank_cancel' else [0]):
            common.BUILD = args.build
            (u, symbols, call, api, clock, init, exceptions), setup = common.fixture_machine(True)
            for index in range(7):
                u.mem_write(BASE + index * 256, bytes(256))
                # The actual native defaults getter/copy/journal initializes
                # each record. Do not treat the ROM default payload as the
                # in-RAM record layout or overwrite a nonexistent eighth slot.
                call(0xbf5244, index, index, 1, task=True)
            for index in range(7):
                for delta, salt in [(0, 23), (SHADOW_DELTA, 83)]:
                    u.mem_write(BASE + delta + index * 256 + 0x84,
                        bytes((index * 43 + offset + salt) % 256 for offset in range(124)))
            mode = (slot + 3) % 12
            call(binding['backup_set_explicit_context_body'], 0x1cf, mode, 0, slot, task=True)
            call(binding['backup_set_explicit_context_body'], 0x1cf, mode, 0, 7, task=True)
            for prop, value in [(reds[mode], 4), (reds[mode] + 13, 17)]:
                call(binding['backup_set_explicit_context_body'], prop, value, 0, 7, task=True)
            u.mem_write(binding['ui_info'] + binding['selected_slot_offset'], bytes([slot]))
            if operation != 'bank_cancel':
                # Reset/defaults are operations of an opened edit page. Its
                # real entry owns the UI image pointers, previous property
                # value and current-settings backup these callers restore.
                call(binding['custom_edit_load'], task=True)
            if operation == 'reset_edit':
                call(binding['backup_set_explicit_context_body'], 0x1cf, (mode + 1) % 12, 0, 7, task=True)
                for prop in [reds[mode], reds[mode] + 13]:
                    call(binding['backup_set_explicit_context_body'], prop, 0, 0, 7, task=True)
            default_wb = call(binding['backup_get'], 0x1cf, 0, 1, slot, task=True)
            before = {delta: bytes(u.mem_read(BASE + delta, 7 * 256)) for delta in [0, SHADOW_DELTA]}
            pending, descriptors, cached, copies, tail_writes = [], [], [], [], []
            def at_journal(uc, address, size, data):
                desc = list(struct.unpack('<3I', uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 12)))
                descriptors.append(desc)
                buffer, length, offset = desc
                pending.append((bytes(uc.mem_read(buffer, length)), offset))
            def cache_return(uc, address, size, data):
                expected, offset = pending.pop()
                assert uc.reg_read(UC_ARM_REG_R0) == 0
                assert bytes(uc.mem_read(0x122064c + offset, len(expected))) == expected
                cached.append(dict(bytes=len(expected), offset=offset, sha256=sha(expected), cache_equal=True))
            def at_copy(uc, address, size, data):
                triple = [uc.reg_read(reg) for reg in [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2]]
                if any(BASE + delta < pointer + triple[2] and pointer < BASE + delta + 7 * 256
                       for delta in [0, SHADOW_DELTA] for pointer in triple[:2]):
                    copies.append(dict(destination=triple[0], source=triple[1], bytes=triple[2],
                        caller_return=hex(uc.reg_read(UC_ARM_REG_LR))))
            u.hook_add(UC_HOOK_CODE, at_journal, begin=0xcf8b74, end=0xcf8b74)
            u.hook_add(UC_HOOK_CODE, cache_return, begin=0xcf8b90, end=0xcf8b90)
            u.hook_add(UC_HOOK_CODE, at_copy, begin=0xcf2bbc, end=0xcf2bbc)
            def tail_store(uc, access, address, size, value, data):
                if any(BASE + delta <= address < BASE + delta + 7 * 256 and
                       (address - BASE - delta) % 256 >= 0x84 for delta in [0, SHADOW_DELTA]):
                    from unicorn.arm_const import UC_ARM_REG_PC
                    tail_writes.append(dict(address=address, bytes=size, pc=hex(uc.reg_read(UC_ARM_REG_PC)),
                        lr=hex(uc.reg_read(UC_ARM_REG_LR))))
            u.hook_add(UC_HOOK_MEM_WRITE, tail_store)
            # Default preparation already translated these native helpers.
            # Flush those blocks so newly attached entry/return observers are
            # present; this does not modify firmware or its API results.
            u.ctl_flush_tb()
            if operation == 'bank_cancel':
                call(0xbbc924, 0, task=True)
                assert bytes(u.mem_read(BASE + SHADOW_DELTA, 7 * 256)) == before[0]
                for index in range(7):
                    call(binding['backup_set_explicit_context_body'], 0x1cf, (mode + index + 1) % 12, 0, index, task=True)
                    u.mem_write(BASE + index * 256 + 0x84, b'\xd7' * 124)
                call(0xbbc924, 1, task=True)
                assert bytes(u.mem_read(BASE, 7 * 256)) == before[0]
                assert bytes(u.mem_read(BASE + SHADOW_DELTA, 7 * 256)) == before[0]
                assert len(copies) == 2 and descriptors == [[0x119288c, 0xe74, 0x10]]
            else:
                call(0x1543ee4 if operation == 'defaults' else 0x1543e4c, task=True)
                after = bytes(u.mem_read(BASE, 7 * 256))
                if operation == 'reset_edit':
                    assert after == before[0]
                    assert call(binding['backup_get'], 0x1cf, 0, 0, 7, task=True) == mode
                    assert [call(binding['backup_get'], prop, 0, 0, 7, task=True)
                        for prop in [reds[mode], reds[mode] + 13]] == [4, 17]
                else:
                    assert call(binding['backup_get'], 0x1cf, 0, 0, slot, task=True) == default_wb
                    for index in range(7):
                        low, high = index * 256, (index + 1) * 256
                        assert after[low + 0x84:high] == before[0][low + 0x84:high]
                        if index != slot:
                            assert after[low:high] == before[0][low:high]
                assert bytes(u.mem_read(BASE + SHADOW_DELTA, 7 * 256)) == after
                if tail_writes and not copies:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.with_name('reset-bank-complete-discovery.json').write_text(json.dumps(dict(
                        status='NOT PASS', operation=operation, slot=slot, copies=copies, tail_writes=tail_writes), indent=2) + '\n')
                assert not tail_writes or copies
            assert descriptors and len(cached) == len(descriptors) and not pending
            cases.append(dict(operation=operation, raw_slot=slot, wb_mode=mode, default_wb=default_wb,
                journal_descriptors=descriptors, native_cache_roundtrips=cached, native_bank_copies=copies,
                native_tail_store_events=len(tail_writes),
                seven_custom_record_tails_preserved=True, full_native_call_completed=True,
                setup=setup, native_vfp_exceptions=exceptions))
    result = dict(scope=__doc__, status='PASS', cases=cases,
        elf_sha256=sha((args.build / 'mods.elf').read_bytes()), checker_sha256=sha(Path(__file__).read_bytes()),
        native_defaults_initialized_fixture_records=True, custom_record_count=7,
        physical_journal_io_verified=False, new_wb_metadata_offsets_assigned=False, hardware_verified=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', cases=len(cases), elf=result['elf_sha256'])))


if __name__ == '__main__':
    main()
