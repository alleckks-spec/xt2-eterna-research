"""Build a pre-startup delivery/power-request probe, not an ETERNA boot.

Original OpenAI Codex-assisted source. Requires private pinned stock/current
images, Clang, ARM LLD and pyelftools. No firmware is distributed by this file.
"""
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from xt2_minimal_boot_guard import checksum

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'firmware/research/xt2-delivery-probe-unverified'
STOCK = ROOT / 'firmware/research/xt2-stock-sd-unverified'
CURRENT = ROOT / 'firmware/research/eterna-minimal-sd-candidate'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def branch(at, target):
    displacement = target - at - 8
    require(displacement % 4 == 0 and -0x2000000 <= displacement < 0x2000000,
            'Invalid branch')
    return struct.pack('<I', 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


def build():
    stock = (STOCK / 'ffboot.bin').read_bytes()
    current = (CURRENT / 'ffboot.bin').read_bytes()
    require(digest(stock) == 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2', 'Stock identity')
    require(digest(current) == 'c1aee308e0b6c54dfede3de4c48885223365b2b8e90c282c74d87a112d58fc10', 'Current identity')
    image = bytearray(stock)
    inert = [(0x781000, 0x2A68), (0xDF7900, 0x1D4)]
    for address, size in inert:
        image[address:address+size] = current[address:address+size]
    with tempfile.TemporaryDirectory(prefix='xt2-delivery-probe-') as tmp:
        tmp = Path(tmp)
        obj, elf_path, linker_script = tmp/'p.o', tmp/'p.elf', tmp/'p.ld'
        subprocess.run(['clang', '--target=armv7-none-eabi', '-marm', '-march=armv7-a',
                        '-c', str(ROOT/'scripts/xt2_delivery_probe.S'), '-o', str(obj)],
                       check=True, capture_output=True)
        linker_script.write_text('ENTRY(probe_entry)\nprobe_wait = 0x103050;\nprobe_led_config = 0x103074;\n'
                                 'probe_led_body = 0x103198;\n'
                                 'SECTIONS { . = 0x1030f0; .text : { *(.text*) } }\n')
        linker = next((ROOT/'.toolchains/rustup/toolchains').glob('*/lib/rustlib/*/bin/gcc-ld/ld.lld'))
        subprocess.run([str(linker), '-T', str(linker_script), '--no-undefined', str(obj),
                        '-o', str(elf_path)], check=True, capture_output=True)
        with elf_path.open('rb') as stream:
            elf = ELFFile(stream)
            code = bytearray(elf.get_section_by_name('.text').data())
            symbols = {s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()
                       if s.name.startswith('probe_')}
    require(len(code) == 168 and not any(stock[0x1030F0:0x103198]), 'Existing reservation differs')
    ranges = [*inert, (symbols['probe_entry'], symbols['probe_expected']-symbols['probe_entry'])]
    struct.pack_into('<6I', code, symbols['probe_ranges']-0x1030F0, *(x for r in ranges for x in r))
    image[0x1030F0:0x103198] = code
    expected = checksum(image[a:a+n] for a,n in ranges)
    struct.pack_into('<I', image, symbols['probe_expected'], expected)
    require(stock[0x103024:0x103028] == branch(0x103024,0x103198), 'LED entry branch differs')
    require(struct.unpack_from('<I',stock,0x10304C)[0] == 0xE51FF004, 'Stock resume instruction differs')
    image[0x103024:0x103028] = branch(0x103024,symbols['probe_entry'])
    # Replace the LED return's indirect reset jump. Both outcomes now request
    # release before executing even the first instruction at native reset 0x100.
    image[0x10304C:0x103050] = branch(0x10304C,symbols['probe_poweroff'])
    # The displaced reset literal and unused following word form a terminal
    # WFE loop, matching the wait strategy of FujiMod's terminal LED entry.
    image[0x103050:0x103054] = struct.pack('<I',0xE320F002)
    image[0x103054:0x103058] = branch(0x103054,0x103050)
    allowed = [(a,a+n) for a,n in inert]+[(0x103024,0x103028),(0x10304C,0x103058),(0x1030F0,0x103198)]
    require(all(a==b or any(lo<=i<hi for lo,hi in allowed)
                for i,(a,b) in enumerate(zip(stock,image))), 'Unexpected change')
    original_manifest = json.loads((CURRENT/'manifest.json').read_text())
    active_sites = original_manifest['private_parameter_call_sites']
    require(all(image[a:a+4] == stock[a:a+4] for a in active_sites), 'Active private call')
    for edit in original_manifest['edits']:
        a, n = edit['address'],len(bytes.fromhex(edit['new']))
        if not any(lo<=a and a+n<=hi for lo,hi in allowed):
            require(image[a:a+n] == stock[a:a+n], 'Active functional edit')
    return bytes(image), dict(image_sha256=digest(image),image_size=len(image),
                             stock_sha256=digest(stock), symbols=symbols,ranges=ranges,
                             expected=expected,guard_size=len(code),
                             active_eterna_hooks=False,native_reset_allowed=False,
                             power_request='Read FFF10004; clear only bit0; write back; DSB; WFE loop',
                             hardware_verified=False,admission='UNREVIEWED: do not use on camera')


def main():
    image, report = build()
    OUT.mkdir(exist_ok=True,parents=True)
    require(not any(p.suffix.lower()=='.dat' for p in OUT.iterdir()), 'DAT present')
    header=(STOCK/'ffsys.bin').read_bytes()
    require(digest(header)=='b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351','Header identity')
    (OUT/'ffboot.bin').write_bytes(image)
    (OUT/'ffsys.bin').write_bytes(header)
    (OUT/'local-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
