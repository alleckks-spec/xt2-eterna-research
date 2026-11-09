"""Check the X-T2 stock JPEG-table binding without a device or encoder model.

Original AI-assisted research tool. Inputs are locally supplied extracted stock
firmware; no firmware, coefficients or instruction listings are emitted. This
executes table preparation only, not JPEG encoding, UI or a complete camera.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)
from unicorn.unicorn_py3.unicorn import uclib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inputs(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    layout = json.loads((root / 'layout.json').read_text())
    wanted = [s for s in manifest['streams'] if s['inner_header']['base'] > 0x1300000]
    wanted += [s for s in layout['units'] if s['file'] == 'overlay-002.bin']
    units = []
    for s in wanted:
        data = (root / s['file']).read_bytes()
        assert sha(data) == s['sha256'], s['file']
        units.append((s.get('base', s.get('inner_header', {}).get('base')), data))
    assert len(units) == 2
    return units


def read(units, address, size):
    for base, data in units:
        if base <= address and address + size <= base + len(data):
            return data[address-base:address-base+size]
    raise ValueError(f'Unmapped input {address:#x}+{size:#x}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--target', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    reference, target = inputs(args.reference), inputs(args.target)
    dis = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    source_entry = 0x292b2e8
    # Locate by a bounded prefix, then qualify the full body and native outputs.
    prefix = read(reference, source_entry, 28)
    overlay_base, overlay = target[1]
    candidates = [overlay_base+i for i in range(0, len(overlay)-len(prefix)+1, 4)
                  if overlay[i:i+len(prefix)] == prefix]
    assert len(candidates) == 1, candidates
    entry = candidates[0]
    assert entry == 0x2a232e8
    source_body = list(dis.disasm(read(reference, source_entry, 0x84), source_entry))
    target_body = list(dis.disasm(read(target, entry, 0x84), entry))
    assert len(source_body) == len(target_body) == 33
    relocations = []
    for old, new in zip(source_body, target_body):
        assert old.mnemonic == new.mnemonic
        if old.mnemonic in ('movw', 'movt', 'bl'):
            if old.mnemonic != 'bl':
                assert old.op_str.split(',')[0] == new.op_str.split(',')[0]
            relocations.append(new.address-entry)
        else:
            assert old.op_str == new.op_str, hex(new.address)
    # Every changed immediate is a known pointer or scaler call. Guards, channel
    # fields and control flow must remain identical; do not mask arbitrary words.
    assert relocations == [0x1c,0x20,0x24,0x28,0x3c,0x40,0x44,0x48,0x58,0x5c,0x60,0x74]
    scaler = 0x15a0dd0
    assert target_body[22].op_str == f'#{scaler:#x}'
    assert target_body[29].op_str == f'#{scaler:#x}'
    # The native submitter stores history[index].value then supplies request+a0.
    submit = list(dis.disasm(read(target, entry+0x84, 0x74), entry+0x84))
    assert submit[16].mnemonic == 'str' and submit[16].op_str == 'r0, [r4, r3, lsl #3]'
    assert submit[17].op_str == 'r5, r4, #0xa0'
    assert submit[21].mnemonic == 'bl' and submit[21].op_str == f'#{entry:#x}'
    # Request initialization is also equivalent, apart from its relocated
    # callback pointer. In particular +d8 receives the caller's stack argument;
    # this does not establish which real capture descriptor supplies tag 4.
    old_ctor = list(dis.disasm(read(reference, source_entry-0xec,0xb4),source_entry-0xec))
    new_ctor = list(dis.disasm(read(target,entry-0xec,0xb4),entry-0xec))
    assert len(old_ctor) == len(new_ctor) == 45
    for i,(old,new) in enumerate(zip(old_ctor,new_ctor)):
        assert old.mnemonic == new.mnemonic
        if i in (37,38):
            assert old.mnemonic in ('movw','movt')
            assert old.op_str.split(',')[0] == new.op_str.split(',')[0]
        else:
            assert old.op_str == new.op_str, hex(new.address)
    assert new_ctor[41].mnemonic == 'str' and new_ctor[41].op_str == 'r3, [r0, #0xd8]'
    # Three request setup blocks (thumbnail, primary, secondary) retain their
    # stack argument layout verbatim; all calls are relative within this overlay.
    assert read(reference,0x2928418,0x174) == read(target,0x2a20418,0x174)
    tables = [0x197085c, 0x197089c, 0x19708dc]
    coefficients = [read(target, a, 64) for a in tables]
    maximum = max(map(max, coefficients))
    assert maximum == 121
    order = read(target, 0x197091c, 64)
    assert sorted(order) == list(range(64)) and order[0] == 0
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0, 0x3001000)
    for base, data in target:
        u.mem_write(base, data)
    channel, stack, done = 0x2f00000, 0x2ff0000, 0x3000000
    output = [0x22f2ec8, 0x22f2708]
    stock_cache = 0x1e0e1ac
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, a, n, v, _: writes.append((a,n)))
    cases = []
    for enabled, scale, option, alternate in [
        (1,s,o,a) for s in (16,64,128,512) for o in (1,2) for a in (0,1)
    ] + [(0,16,1,0), (2,16,1,1)]:
        u.mem_write(channel, bytes(0x80))
        u.mem_write(channel+0x29, bytes([enabled]))
        for dest in output:
            u.mem_write(dest-16, b'\xa5'*(64+32))
        u.mem_write(stock_cache-16,b'\x5a'*(64+32))
        for reg, value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),
                              (channel,scale,option,alternate)):
            u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,stack)
        u.reg_write(UC_ARM_REG_LR,done)
        writes.clear()
        u.emu_start(entry,done,count=100000)
        assert u.reg_read(UC_ARM_REG_PC) == done
        assert u.reg_read(UC_ARM_REG_SP) == stack
        for a,n in writes:
            assert (stack-0x1000 <= a and a+n <= stack) or (
                channel <= a and a+n <= channel+0x80) or any(
                d <= a and a+n <= d+64 for d in output) or (
                stock_cache+1 <= a and a+n <= stock_cache+64), (hex(a),n)
        for i,dest in enumerate(output):
            actual = bytes(u.mem_read(dest,64))
            if enabled == 1:
                base = coefficients[1 if i == 0 else (0 if alternate else 2)]
                expected = bytes([1] + [max(1,min(255,(scale*option*base[j])>>10)) for j in order[1:]])
                assert actual == expected, (scale, option, alternate, i)
                if scale == 16 and option == 1:
                    assert actual == b'\x01'*64
            else:
                assert actual == b'\xa5'*64
            assert bytes(u.mem_read(dest-16,16)) == b'\xa5'*16
            assert bytes(u.mem_read(dest+64,16)) == b'\xa5'*16
        if enabled == 1:
            assert struct.unpack('<2I',u.mem_read(channel+0x2c,8)) == tuple(output)
            secondary = coefficients[0 if alternate else 2]
            assert bytes(u.mem_read(stock_cache+1,63)) == bytes(secondary[j] for j in order[1:])
        else:
            assert bytes(u.mem_read(stock_cache,64)) == b'\x5a'*64
        assert bytes(u.mem_read(stock_cache-16,17)) == b'\x5a'*17
        assert bytes(u.mem_read(stock_cache+64,16)) == b'\x5a'*16
        cases.append(dict(enabled=enabled,scale=scale,option=option,alternate=alternate))
    report = dict(scope=__doc__,status='PASS: bounded stock table preparation',
        entry=hex(entry),scaler=hex(scaler),cases=cases,coefficient_max=maximum,
        inputs=[dict(base=hex(a),bytes=len(b),sha256=sha(b)) for a,b in reference+target],
        qualified=['unique bounded entry prefix','full preparation body roles',
                   'submitter channel and scale-history addressing',
                   'request initializer and three caller blocks',
                   'stock scaler outputs and write extents'],
        limitations=['request producers and capture descriptor tags not qualified',
                     'mod not linked by this check','no JPEG encoder, startup, settings or physical camera'],
        hardware_verified=False,source_sha256=sha(Path(__file__).read_bytes()),
        unicorn_library_sha256=sha(Path(uclib._name).read_bytes()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],entry=report['entry'],cases=len(cases))))


if __name__ == '__main__':
    main()
