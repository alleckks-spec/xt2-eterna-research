"""Fixed corruption gate inside the existing X-T2 SD early-LED reservation.

Original OpenAI Codex-assisted tooling. Local firmware is required; no firmware
instructions are embedded here. This is not flash write protection or secure boot.
"""
import struct
import subprocess
import tempfile
from pathlib import Path
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 0x1030F0
LIMIT = 0x103198
HOOK = 0x103024
LED_CONFIG = 0x103074
LED_BODY = 0x103198
RANGES = ((0x781000, 0x2A68), (0xDF7900, 0x1D4),
          (0xC4D298, 0x328), (0xFA2AF8, 8),
          (0x1569C1C, 0x109C4), (0x16E109C, 8))


def checksum(parts):
    value = 0x811C9DC5
    for part in parts:
        for byte in part:
            value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return value


def compile_guard(source_name="xt2_minimal_boot_guard.S"):
    with tempfile.TemporaryDirectory(prefix='xt2-fixed-guard-') as directory:
        directory = Path(directory)
        obj, out = directory / 'guard.o', directory / 'guard.elf'
        subprocess.run(['clang', '--target=armv7-none-eabi', '-marm',
                        '-march=armv7-a', '-c', str(ROOT / "scripts" / source_name),
                        '-o', str(obj)], check=True, capture_output=True)
        script = directory / 'guard.ld'
        script.write_text(f'ENTRY(xt2_minimal_guard_entry)\n'
                          f'xt2_minimal_led_config = {LED_CONFIG};\n'
                          f'xt2_minimal_led_body = {LED_BODY};\n'
                          f'SECTIONS {{ . = {ENTRY}; .text : {{ *(.text*) }} }}\n')
        linker = sorted((ROOT / '.toolchains/rustup/toolchains').glob(
            '*/lib/rustlib/*/bin/gcc-ld/ld.lld'))[0]
        subprocess.run([str(linker), '-T', str(script), '--no-undefined',
                        str(obj), '-o', str(out)], check=True, capture_output=True)
        with out.open('rb') as stream:
            elf = ELFFile(stream)
            section = elf.get_section_by_name('.text')
            code = section.data()
            symbols = {s.name: s['st_value'] for s in
                       elf.get_section_by_name('.symtab').iter_symbols() if s.name}
            if section['sh_addr'] != ENTRY or ENTRY + len(code) > LIMIT:
                raise ValueError('Guard exceeds existing early-LED reservation')
            if any(s.name and s['st_shndx'] == 'SHN_UNDEF' for s in
                   elf.get_section_by_name('.symtab').iter_symbols()):
                raise ValueError('Unresolved guard symbol')
    return code, symbols


def install(image):
    code, symbols = compile_guard()
    original = struct.unpack('<I', image.mem_read(HOOK, 4))[0]
    displacement = original & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    if (original >> 24 != 0xEA or HOOK + 8 + 4 * displacement != LED_BODY
            or any(image.mem_read(ENTRY, LIMIT - ENTRY))):
        raise ValueError('Pinned early-LED branch or unused configuration differs')
    count = struct.unpack('<I', image.mem_read(LED_CONFIG, 4))[0]
    if count != 10 or LED_CONFIG + 4 + count * 12 != ENTRY:
        raise ValueError('LED configuration overlaps guard')
    expected = symbols['xt2_minimal_guard_expected']
    ranges = (*RANGES, (ENTRY, expected - ENTRY))
    code = bytearray(code)
    offset = symbols['xt2_minimal_guard_ranges'] - ENTRY
    struct.pack_into('<14I', code, offset, *(v for span in ranges for v in span))
    image.mem_write(ENTRY, code)
    value = checksum(image.mem_read(address, size) for address, size in ranges)
    image.mem_write(expected, struct.pack('<I', value))
    displacement = ENTRY - HOOK - 8
    image.mem_write(HOOK, struct.pack('<I', 0xEA000000 | ((displacement >> 2) & 0xFFFFFF)))
    return dict(entry=ENTRY, size=len(code), failure=symbols['xt2_minimal_guard_failed'],
                failure_loop=symbols['xt2_minimal_guard_failed'] + 4,
                ranges_address=symbols['xt2_minimal_guard_ranges'],
                expected_address=expected, checksum=value, ranges=ranges,
                checked_bytes=sum(size for _, size in ranges),
                hook=HOOK, success_continuation=LED_BODY,
                algorithm='FNV-1a32: accidental corruption check, not authentication',
                failure_action='Stop before original LED body and stock startup; no rollback',
                global_flash_write_protection=False, hardware_verified=False)
