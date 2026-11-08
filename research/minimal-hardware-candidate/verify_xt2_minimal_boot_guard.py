"""Bounded native early-entry corruption/ABI checks, not ROM transfer/full boot.

Host supplies the image in RAM. GPIO register storage is an explicit fixture,
used only to compare the unchanged stock LED operation. No flash, storage,
sensor, scheduler, cache coherence or power-off recovery is modeled successful.
"""
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn import arm_const as reg
from build_eterna_minimal_sd import OUTPUT, ROOT
from build_eterna_payload import STOCK
from xt2_minimal_boot_guard import ENTRY, LIMIT, LED_CONFIG, checksum, compile_guard


def digest(data):
    return hashlib.sha256(data).hexdigest()


def machine(image):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0, (len(image) + 4095) & ~4095)
    u.mem_write(0, image)
    u.mem_map(0xFFF0C000, 0x1000)
    return u


def main():
    sources = [Path(__file__), ROOT/'scripts/xt2_minimal_boot_guard.S',
               ROOT/'scripts/xt2_minimal_boot_guard.py', ROOT/'scripts/build_eterna_minimal_sd.py']
    source_pins = {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sources}
    image = (OUTPUT / 'ffboot.bin').read_bytes()
    stock = STOCK.read_bytes()
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    guard = manifest['boot_integrity_guard']
    resume = struct.unpack_from('<I', stock, 0x103050)[0]
    assert struct.unpack_from('<I', image, 0x103050)[0] == resume
    assert digest(image) == manifest['image_sha256']
    ranges = guard['ranges']
    expected = struct.unpack_from('<I', image, guard['expected_address'])[0]
    assert checksum(image[a:a + n] for a, n in ranges) == expected
    assert ENTRY + guard['size'] <= LIMIT
    compiled, symbols = compile_guard()
    code_end = symbols['xt2_minimal_guard_ranges'] - ENTRY
    assert image[ENTRY:ENTRY+code_end] == compiled[:code_end]
    previous = (ROOT / 'research/minimal-before-boot-guard/ffboot.bin').read_bytes()
    assert digest(previous) == '47a9376657501fec7805c0fa17b958dea2b100bfc13652d764a7b73401723751'
    changes = [(0x103024, 4), (ENTRY, guard['size'])]
    for i, (a, b) in enumerate(zip(previous, image)):
        assert a == b or any(lo <= i < lo + n for lo, n in changes)
    # The functional bytes verified in the previous numeric run are unchanged.
    assert all(image[a:a+n] == previous[a:a+n] for a, n in ranges[:-1])
    registers = [getattr(reg, 'UC_ARM_REG_R' + str(i)) for i in range(13)]
    registers += [reg.UC_ARM_REG_LR, reg.UC_ARM_REG_SP, reg.UC_ARM_REG_CPSR]
    gpio_addresses = sorted({a for a, _, _ in struct.iter_unpack(
        '<III', stock[LED_CONFIG+4:LED_CONFIG+4+120])})
    modes = [0x13, 0xA0000013, 0xF8000013]
    active = dict(failure=False, writes=[], body=0)
    u = machine(image)
    def watch(uc, access, address, size, value, _):
        scratch = 0x103058 <= address < address + size <= 0x103074
        gpio = address in gpio_addresses and size == 4
        assert scratch or (gpio and not active['failure']), (hex(address), size)
        active['writes'].append((address, size, value))
    u.hook_add(UC_HOOK_MEM_WRITE, watch)
    def mmio_read(uc, access, address, size, value, _):
        assert not active['failure'], ('MMIO read before rejection', hex(address))
    u.hook_add(UC_HOOK_MEM_READ, mmio_read, begin=0xF0000000, end=0xFFFFFFFF)
    def failed(uc, pc, size, _):
        uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, failed, begin=guard['failure_loop'], end=guard['failure_loop'])
    def body(uc, pc, size, _):
        active['body'] += 1
    u.hook_add(UC_HOOK_CODE, body, begin=guard['success_continuation'],
               end=guard['success_continuation'])

    def prepare(uc, flags):
        values = [0x12340000 + i * 0x100 for i in range(14)] + [0xDEAD0000, flags]
        for register, value in zip(registers, values):
            uc.reg_write(register, value)
        for a in gpio_addresses:
            uc.mem_write(a, struct.pack('<I', 0x11223344 ^ a))
        return values

    clean = []
    for flags in modes:
        baseline = machine(stock)
        before = prepare(baseline, flags)
        baseline.emu_start(0, resume, count=10000)
        assert baseline.reg_read(reg.UC_ARM_REG_PC) == resume
        assert [baseline.reg_read(r) for r in registers] == before
        active.update(failure=False, writes=[], body=0)
        before = prepare(u, flags)
        u.emu_start(0, resume, count=1000000)
        assert u.reg_read(reg.UC_ARM_REG_PC) == resume
        assert [u.reg_read(r) for r in registers] == before
        assert active['body'] == 1
        assert all(u.mem_read(a, 4) == baseline.mem_read(a, 4) for a in gpio_addresses)
        clean.append(dict(cpsr=hex(flags),registers_sp_lr_flags_preserved=True,
                          stock_gpio_result_identical=True, writes=len(active['writes'])))

    # Every original functional edit's first and last byte, including overlapping
    # specialization writes. These bytes are read, not executed before the gate.
    points = set()
    for edit in manifest['edits']:
        a, n = edit['address'], len(bytes.fromhex(edit['new']))
        if any(lo <= a and a + n <= lo + size for lo, size in ranges[:-1]):
            points.update((a, a + n - 1))
    points.add(guard['expected_address'])
    failures = []
    def refusal(address, replacement, name):
        original = bytes(u.mem_read(address, len(replacement)))
        u.mem_write(address, replacement)
        active.update(failure=True, writes=[], body=0)
        prepare(u, 0xA0000013)
        try:
            u.emu_start(0, resume, count=1000000)
            assert u.reg_read(reg.UC_ARM_REG_PC) == guard['failure_loop'], name
            assert u.reg_read(reg.UC_ARM_REG_CPSR) & 0x1C0 == 0x1C0
            assert active['body'] == 0
            assert all(0x103058 <= a < a+n <= 0x103074
                       for a, n, _ in active['writes'])
            failures.append(dict(name=name,address=hex(address),
                                 stopped_before_led_and_stock_start=True,
                                 interrupts_masked=True, no_mmio_reads_or_writes=True))
        finally:
            u.mem_write(address, original)
    for address in sorted(points):
        refusal(address, bytes([image[address] ^ 1]), 'single-bit functional corruption')
    refusal(0x781000, bytes(0x4000), 'lost entire profile allocation')
    refusal(0xDF7900, bytes(0x700), 'resident tail replaced by zeros')
    refusal(0x781000, stock[0x781000:0x785000], 'mixed stock profile allocation')
    table = guard['ranges_address']
    assert struct.unpack_from('<II', image, table) == tuple(ranges[0])
    for index in range(7):
        refusal(table + 8*index, struct.pack('<I', 0xFFF0C280), 'non-RAM span rejected')
        refusal(table + 8*index + 4, struct.pack('<I', 0xFFFFFFFF), 'overflowing length rejected')
    refusal(guard['expected_address']-4, struct.pack('<I', 0xFFFFFFFF),
            'corrupt terminator rejected')
    # A blanket -255 flash denial changes the original writer's caller result;
    # it is not a transparent read-only mode. No device response is fabricated.
    flash = []
    for status in (0, 0xFFFFFF01):
        u.reg_write(reg.UC_ARM_REG_R0, status)
        u.emu_start(0xC5A210, 0xC5A2C0, count=20)
        assert u.reg_read(reg.UC_ARM_REG_PC) == 0xC5A2C0
        assert u.reg_read(reg.UC_ARM_REG_R0) == status
        flash.append(dict(supplied_native_program_status=hex(status),
                          original_caller_status=hex(u.reg_read(reg.UC_ARM_REG_R0))))
    assert source_pins == {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sources}
    report = dict(scope=__doc__,image_sha256=digest(image),guard=guard,
                  source_sha256=source_pins, sources_unchanged_during_run=True,
                  assembly_matches_current_source=True,
                  clean_entry_cases=clean,corruption_cases=failures,original_reset_resume=hex(resume),
                  existing_functional_bytes_unchanged=True,
                  native_program_error_propagation=flash,
                  flash_prohibition_installed=False,
                  limitation='Error propagation is not proof of a full boot failure or success. '
                  'A whole-driver denial needs real persistence dependencies and recovery evidence. '
                  'Guard does not cover a bypassed/corrupt entry branch, arbitrary verifier-code corruption '
                  'or later CPU/DMA overwrites. FNV is not a signature.',
                  original_rom_transfer=False,full_boot=False,hardware_verified=False)
    path = ROOT / 'research/eterna-minimal-boot-guard-verification.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(image_sha256=report['image_sha256'],guard_bytes=guard['size'],
                         clean_cases=len(clean),corruptions_rejected=len(failures),
                         unchanged_functional_bytes=True,hardware_verified=False)))


if __name__ == '__main__':
    main()
