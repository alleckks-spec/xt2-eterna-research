"""AI-assisted SDK dependency probe, not an X-T2 firmware or camera test.

An authored A32 program initializes the existing XPP SD model and reads its
FAT32 MBR using PIO. No Python MMIO adapter, firmware or success hook is used.
Requires the pinned FujiMod Python SDK built with its emulator feature.
"""
import hashlib
import json
from pathlib import Path
import struct

from fujimod._native import emulator as native
from fujimod.emulator import Asset, Definition, Image, make_board


def main():
    fmt = dict(sectors=0x800000, max_dirty_sectors=4096,
               partition_start=2048, sectors_per_cluster=8, label="SDKPROBE")
    payload = b'{"sdk_dependency_probe":true}\n'
    card = native.CardMedium.formatted(json.dumps(fmt), [("SETTINGS.JSN", payload)])
    assert card.read("SETTINGS.JSN") == payload
    assert native.CardMedium.restored(card.to_bytes()).read("SETTINGS.JSN") == payload
    expected = bytes(card.sector(0))
    base = 0xF0080000  # Synthetic test wiring; not an asserted X-T2 address.
    bank = base + 0x200
    words = []

    def constant(reg, value):
        for opcode, half in ((0xE3000000, value & 0xFFFF),
                             (0xE3400000, value >> 16)):
            words.append(opcode | ((half & 0xF000) << 4) | (reg << 12) | (half & 0xFFF))

    def store(address, value):
        constant(0, address)
        constant(1, value)
        words.append(0xE5801000)  # str r1,[r0]

    def delay():
        words.extend([0xE320F000] * 16)  # nop; instruction ticks are explicit.

    def record(address, output):
        constant(0, address)
        words.append(0xE5901000)
        constant(2, output)
        words.append(0xE5821000)

    store(base, 1)
    delay()
    store(bank + 0x2C, 0x3F03)
    delay()
    store(bank + 0x2C, 0x3F07)
    store(bank + 0x28, 0xF00)
    store(bank + 0x34, 0xFFFFFFFF)
    commands = [(0, 0), (0x081A0000, 0x1AA), (0x371A0000, 0),
                (0x29020000, 0x40100000), (0x02090000, 0),
                (0x031A0000, 0), (0x071B0000, 0x10600),
                (0x101A0000, 512), (0x371A0000, 0x10600), (0x061A0000, 2)]
    for index, (command, argument) in enumerate(commands + [(0x113A0010, 0)]):
        if index == len(commands):
            store(bank + 4, 0x10200)
        store(bank + 0x30, 0xFFFFFFFF)
        store(bank + 8, argument)
        store(bank + 12, command)
        delay()
        record(bank + 0x30, 0x8000 + index * 4)
    store(bank + 0x30, 0x21)
    for index in range(128):
        record(bank + 0x20, 0x9000 + index * 4)
    delay()
    record(bank + 0x30, 0x8100)
    program = struct.pack(f"<{len(words)}I", *words)
    instruction_count = len(words)
    program += struct.pack("<I", 0xEAFFFFFE)
    graph = dict(processors=[dict(model="cortex-a7", released=True,
                                 mprofile=None, rprofile=None,
                                 registers=[["Pc", 0x1000], ["Pstate", 0xD3]])],
                 ram=[dict(base=0, size=0x10000)], decoders=[],
                 mappings=[dict(core=0, address=0, physical=0, size=0x10000, permissions=7)],
                 dma_mappings=[dict(address=0, physical=0, size=0x10000, permissions=3)],
                 peripherals=[dict(core=0, address=0xF0000000, physical=0xF0000000,
                                   size=0x10000000)], instructions_per_tick=[1, 1])
    devices = dict(kind="xpp", cpus=[dict(mpidr=0x80000000,
                   configuration_base=0xFFFF0000, cycles_per_tick=64)],
                   gic=dict(distributor=0xFFFF1000, cpu_interface=0xFFFF2000, lines=512),
                   nodes=[dict(name="sd", model=dict(kind="sd", format=fmt,
                        files={"SETTINGS.JSN": "settings"}, irq=None,
                        options=dict(base=base, register_offset=0x200,
                                     transfer_ticks=10, clock_ticks=2, reset_ticks=3,
                                     rca=1, ram_bytes=0x10000)))])
    definition = Definition(execution=graph, devices=devices,
                            assets=(Asset("program", len(program)), Asset("settings", len(payload))),
                            images=(Image("program", 0x1000, core=0),), quantum=1)
    board = make_board(definition, {"program": program, "settings": payload})
    try:
        board.run(instruction_count)
        statuses = struct.unpack("<11I", board.cpus[0].mem_read(0x8000, 44))
        actual = bytes(board.cpus[0].mem_read(0x9000, 512))
        completed = struct.unpack("<I", board.cpus[0].mem_read(0x8100, 4))[0]
        assert all(value & 1 and not value & 0xFFFF8000 for value in statuses), statuses
        assert actual == expected, "Guest PIO sector differs from formatted medium"
        assert completed & 2, completed
        report = dict(scope=__doc__, sdk_commit="944d5c865d4def32663c1dad24d54ac3001f3f6e",
                      instructions=board.instructions, commands=len(statuses),
                      statuses=statuses, transfer_status=completed,
                      mbr_sha256=hashlib.sha256(actual).hexdigest(), mbr_matches=True,
                      host_medium_restore=True, firmware_executed=False, camera_tested=False)
    finally:
        board.close()
    out = Path(__file__).resolve().parent / "existing-sdk-sd-probe-unverified"
    out.mkdir(exist_ok=True)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
