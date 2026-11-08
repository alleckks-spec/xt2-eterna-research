"""Small offline helpers. Addresses are original virtual addresses, no USB I/O."""
import json
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


class Firmware:
    def __init__(self, model, include_layout=False):
        self.model = model
        root = Path('firmware/extracted') / model
        self.manifest = json.loads((root / 'manifest.json').read_text())
        self.units = [(s['inner_header']['base'], (root / s['file']).read_bytes())
                      for s in self.manifest['streams'] if 'inner_header' in s]
        if include_layout:
            layout = json.loads((root / 'layout.json').read_text())
            self.units.extend((s['base'], (root / s['file']).read_bytes()) for s in layout['units'])
        self.dis = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    def read(self, address, count):
        for base, data in self.units:
            if base <= address and address + count <= base + len(data):
                return data[address-base:address-base+count]
        raise ValueError(f'Unmapped {address:#x}+{count:#x}')

    def word(self, address):
        return struct.unpack('<I', self.read(address, 4))[0]

    def listing(self, start, end):
        lines = []
        for a in range(start, end, 4):
            raw = self.read(a, 4)
            ins = list(self.dis.disasm_lite(raw, a))
            lines.append(f'{a:08x}: ' + (f'{ins[0][2]} {ins[0][3]}' if ins else f'.word {self.word(a):#x}'))
        return lines

    def calls_to(self, target):
        hits = []
        for base, data in self.units:
            for i, (w,) in enumerate(struct.iter_unpack('<I', data[:len(data)//4*4])):
                if w & 0x0f000000 == 0x0b000000:
                    delta = w & 0xffffff
                    if delta & 0x800000:
                        delta -= 0x1000000
                    if base+i*4+8+delta*4 == target:
                        hits.append(base+i*4)
        return hits


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('model')
    p.add_argument('start', type=lambda s:int(s,0))
    p.add_argument('size', type=lambda s:int(s,0))
    a = p.parse_args()
    print('\n'.join(Firmware(a.model).listing(a.start, a.start+a.size)))
