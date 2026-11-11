"""Execute the full native custom-record import for each declared format.

The original import and native journal cache APIs run without substitutes.
Source bytes, format index and custom-record canaries are explicit inputs.
Cached readback is not a physical NAND write/reboot or spare-tail assignment.
"""
import argparse
import json
import struct
from collections import deque
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
from verify_wb_recall_edit_lifecycle import ROOT, BASE, SHADOW_DELTA, common, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'save-data-menu-native-build-unverified')
    parser.add_argument('--output', type=Path, default=ROOT / 'wb-lifecycle-check-unverified/import-complete.json')
    args = parser.parse_args()
    stock = (ROOT.parents[1] / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes()
    sizes = [int.from_bytes(stock[0xf99d98 + 4 * index:0xf99d98 + 4 * index + 4], 'little') for index in range(6)]
    assert sizes == [0x5c, 0x60, 0x7c, 0x80, 0x80, 0x80]
    cases = []
    for version, extent in enumerate(sizes):
        common.BUILD = args.build
        (u, symbols, call, api, clock, init, exceptions), setup = common.fixture_machine(True)
        source = 0x8002000
        blob = bytearray(0x1574)
        blob[0x36] = version
        for slot in range(7):
            default = bytearray(stock[0xf7f12c + slot * 256:0xf7f12c + (slot + 1) * 256])
            default[0x29] = 3  # Valid native film field in persistent payload.
            default[0x62:0x7c] = (('Import ' + str(slot)).encode() + b'\0').ljust(26, b'\0')
            blob[0xe74 + slot * 256:0xe74 + (slot + 1) * 256] = default
            for delta, salt in [(0, 11), (SHADOW_DELTA, 79)]:
                image = bytearray(stock[0xf7f12c + slot * 256:0xf7f12c + (slot + 1) * 256])
                image[0x84:] = bytes((slot * 41 + offset + salt) % 256 for offset in range(124))
                u.mem_write(BASE + delta + slot * 256, bytes(image))
        u.mem_write(source, bytes(blob))
        u.mem_write(0x10d1930 + 0x46, bytes([version]))
        before = {delta: bytes(u.mem_read(BASE + delta, 7 * 256)) for delta in [0, SHADOW_DELTA]}
        descriptors, pending, roundtrips, readbacks, recent = [], [], [], [], deque(maxlen=48)
        def journal_entry(uc, address, size, data):
            pointer = uc.reg_read(UC_ARM_REG_R0)
            descriptor = list(struct.unpack('<3I', uc.mem_read(pointer, 12)))
            descriptors.append(descriptor)
            buffer, length, offset = descriptor
            pending.append((bytes(uc.mem_read(buffer, length)), offset))
        def cache_return(uc, address, size, data):
            expected, offset = pending.pop()
            assert uc.reg_read(UC_ARM_REG_R0) == 0
            assert bytes(uc.mem_read(0x122064c + offset, len(expected))) == expected
            roundtrips.append(dict(offset=offset, bytes=len(expected), sha256=sha(expected), cache_equal=True))
        u.hook_add(UC_HOOK_CODE, journal_entry, begin=0xcf8b74, end=0xcf8b74)
        u.hook_add(UC_HOOK_CODE, cache_return, begin=0xcf8b90, end=0xcf8b90)
        u.hook_add(UC_HOOK_CODE, lambda uc, address, size, data: recent.append(hex(address)))
        try:
            native_return = call(0xbf5564, source, 0x1574, task=True)
        except Exception:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.with_name('import-complete-discovery.json').write_text(json.dumps(dict(
                status='NOT PASS', version=version, descriptors=descriptors, roundtrips=roundtrips,
                pc=hex(u.reg_read(UC_ARM_REG_PC)), lr=hex(u.reg_read(UC_ARM_REG_LR)), recent=list(recent)), indent=2) + '\n')
            raise
        assert len(descriptors) == len(roundtrips) == 8 and not pending
        assert descriptors[0] == [0x119288c, 0xe74, 0x10]
        slots = []
        for slot in range(7):
            record = BASE + slot * 256
            assert descriptors[slot + 1] == [record + 4, 256, 0xf44 + slot * 256]
            expected = bytes(blob[0xe74 + slot * 256:0xe74 + slot * 256 + extent])
            for delta in [0, SHADOW_DELTA]:
                actual = bytes(u.mem_read(record + delta, 256))
                assert actual[:4] == before[delta][slot * 256:slot * 256 + 4]
                assert actual[4:4 + extent] == expected
                assert actual[4 + extent:] == before[delta][slot * 256 + 4 + extent:(slot + 1) * 256]
            # Read the actual journal cache through the native descriptor/API,
            # to a separate scratch buffer. Do not reset the record to fake it.
            destination = 0x8005000
            u.mem_write(destination, b'\xa7' * 256)
            assert call(0xbbc8c8, destination, slot, task=True) == 0
            assert bytes(u.mem_read(destination, 256)) == bytes(u.mem_read(record + 4, 256))
            readbacks.append(dict(slot=slot, bytes=256, sha256=sha(bytes(u.mem_read(destination, 256))),
                actual_cache_read_api=True))
            slots.append(dict(slot=slot, written_range=[4, 4 + extent], tail84_plus_preserved=True,
                primary_and_shadow_prefix_equal=True, neighbor_prefix_unchanged=True))
        cases.append(dict(format_index=version, source_sha256=sha(blob), native_copy_extent=extent,
            native_return=native_return, descriptors=descriptors, cache_roundtrips=roundtrips,
            native_cache_readbacks=readbacks, slots=slots, setup=setup, native_vfp_exceptions=exceptions))
    result = dict(scope=__doc__, status='PASS', cases=cases,
        elf_sha256=sha((args.build / 'mods.elf').read_bytes()), stock_sha256=sha(stock),
        checker_sha256=sha(Path(__file__).read_bytes()), actual_import_entry=True,
        actual_cache_read_write_api=True, full_native_import_call=True,
        new_wb_metadata_invalidation_implemented=False, spare_tail_qualified=False,
        physical_journal_io_verified=False, hardware_verified=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', formats=len(cases), native_slot_copies=42,
        cache_readbacks=42, elf=result['elf_sha256'])))


if __name__ == '__main__':
    main()
