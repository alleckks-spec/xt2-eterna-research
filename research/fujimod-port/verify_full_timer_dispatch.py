"""Execute a production film-loader callback on the X-T2 dedicated timer stack.

Reuse the native UI1/constructor fixture. film_loader_boot registers its real
periodic callback through the linked lifetime wrapper and native timer API;
explicit native ticks invoke it and its real film_cards_tick observer. Mode 0
is a declared input and keeps file admission closed. No callback/API success
stubs or timer records are supplied. This is not scheduled timer-thread, IRQ,
elapsed-time, capture admission, full startup or hardware evidence.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP
from unicorn.unicorn_py3.unicorn import uclib
from build_full_timer_candidate import BUILD, ROOT
from verify_card_processing import make_machine


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=BUILD)
    parser.add_argument('--original-stack', action='store_true')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    (u, symbols, call, api, clock, init, exceptions), setup = make_machine(args.build)
    word = lambda address: struct.unpack('<I', u.mem_read(address, 4))[0]
    assert call(0xcdf570, task=True) == 0
    card = Path(str(args.build) + '-card')
    with (card / 'ffboot.bin').open('rb') as stream:
        stream.seek(0xcdfb04)
        delivered = int.from_bytes(stream.read(4), 'little')
    assert delivered == word(0xcdfb04) == 0x1187ffc
    if args.original_stack:
        u.mem_write(0xcdfb04, struct.pack('<I', 0x1188000))
        u.ctl_flush_tb()
    low, high = 0x1187000, 0x1188000
    assert bytes(u.mem_read(low, 0x2000)) == struct.pack('<I', 0xefefefef) * 0x800
    u.mem_write(low - 16, b'\xa7' * 16)
    u.mem_write(high, b'\xa9' * 16)
    u.mem_write(symbols['ui_mode'], b'\0')
    callback = symbols['film_loader_tick']
    observer = symbols['film_cards_tick']
    active = False
    entries, observers, stack, calls, writes, io = [], [], [], [], [], []
    disassembler = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    def trace(uc, address, size, data):
        nonlocal active
        if address == 0xcdf97c:
            active = True
        if address == 0xcdfaf0:
            active = False
        if not active:
            return
        sp = uc.reg_read(UC_ARM_REG_SP)
        assert low <= sp <= high, (hex(address), hex(sp))
        stack.append(sp)
        if address == callback:
            entries.append(sp)
        if address == observer:
            observers.append(sp)
        instruction = list(disassembler.disasm_lite(bytes(uc.mem_read(address, size)), address))
        if instruction and instruction[0][2] in ('bl', 'blx'):
            calls.append(dict(pc=hex(address), sp=hex(sp), mod8=sp % 8))

    def write(uc, access, address, size, value, data):
        if active and low - 16 <= address < high + 16:
            assert low <= address < address + size <= high, (hex(uc.reg_read(UC_ARM_REG_PC)), hex(address), size)
            writes.append([address, size])

    u.hook_add(UC_HOOK_CODE, trace)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    native = json.loads((args.build / 'target.json').read_text())['symbols']
    for name in ['storage_open_file_async', 'storage_read_async_wrapper', 'storage_write_file_async',
                 'storage_entry_async', 'storage_seek_async']:
        def forbidden(uc, address, size, data):
            io.append(address)
            raise AssertionError(('unexpected I/O in mode0', hex(address)))
        u.hook_add(UC_HOOK_CODE, forbidden, begin=native[name], end=native[name])
    before = u.reg_read(UC_ARM_REG_SP)
    api('film_loader_boot')
    assert word(symbols['film_loader'] + 12) == 0
    assert word(symbols['film_loader'] + 16) != 0
    assert word(symbols['film_loader'] + 4) == 0
    for count in [121, 120]:
        for _ in range(count):
            call(0xcdf968, task=True)
    assert len(entries) == len(observers) == 2
    assert word(symbols['film_loader'] + 4) == 2
    assert word(symbols['film_loader']) == 0  # WAIT; mode0 never admitted storage.
    assert u.reg_read(UC_ARM_REG_SP) == before
    expected_mod8 = 4 if args.original_stack else 0
    assert all(sp % 8 == expected_mod8 for sp in entries)
    assert calls and all(row['mod8'] == expected_mod8 for row in calls)
    assert bytes(u.mem_read(low - 16, 16)) == b'\xa7' * 16
    assert bytes(u.mem_read(high, 16)) == b'\xa9' * 16
    assert not clock.errors and not io
    report = dict(scope=__doc__, status='PASS', original_stack_control=args.original_stack,
        elf_sha256=sha((args.build / 'mods.elf').read_bytes()), delivered_literal=hex(delivered),
        executed_literal=hex(word(0xcdfb04)), callback='film_loader_tick', observer='film_cards_tick',
        registration='film_loader_boot -> x70_timer_start -> native software_timer_start',
        callback_sp=list(map(hex, entries)), observer_sp=list(map(hex, observers)),
        callback_calls=calls, logical_ticks=241, loader_ticks=2, loader_state=0, ui_mode=0,
        native_timer_handle=word(symbols['film_loader'] + 16),
        dedicated_stack=dict(base=hex(low), end=hex(high), maximum_depth=high - min(stack),
            observed_stores=len(writes), sentinels_intact=True),
        setup=setup, init_calls=init, native_vfp_exceptions=exceptions,
        internal_success_stubs=0, supplied_timer_records=0, mod_storage_calls=io,
        timer_thread_scheduled=False, real_time_or_irq=False, hardware_verified=False,
        checker_sha256=sha(Path(__file__).read_bytes()),
        unicorn_sha256=sha(Path(uclib._name).read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['status', 'elf_sha256', 'callback_sp', 'observer_sp', 'dedicated_stack']}))


if __name__ == '__main__':
    main()
