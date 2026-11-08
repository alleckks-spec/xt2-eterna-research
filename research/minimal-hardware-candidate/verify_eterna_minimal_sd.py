"""Execute processing functions from the built minimal SD candidate.

No full boot, device fixtures, physical image processing, or flash operations.
"""
import json
import struct
from unicorn import UC_HOOK_MEM_WRITE

from build_eterna_minimal_sd import build, digest, OUTPUT, CODE, DATA, ALIAS
from build_eterna_payload import ROOT, STOCK
from verify_interpolated_profile_outputs import runtime, outputs, call
from verify_native_parameter_builder import build as aggregate
from verify_development_selector_extension import execute
from verify_profile_selectors import RAM
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_PC


def main():
    image, manifest = build()
    # Test the delivered file, not only an independently patched fixture.
    assert image == (OUTPUT / 'ffboot.bin').read_bytes()
    actual = runtime('xt2-4.41', False)
    baseline = runtime('xt2-4.41', False)
    donor = runtime('xh1-2.15', False)
    actual.mem_map(DATA, 0x4000)
    actual.mem_write(DATA, image[DATA:DATA+0x4000])
    for edit in manifest['edits']:
        a, data = edit['address'], bytes.fromhex(edit['new'])
        if DATA <= a < DATA + 0x4000:
            continue
        # Edits may overlap while specializing the generic ID18 trampoline.
        actual.mem_write(a, image[a:a+len(data)])
    actual.mem_protect(CODE & ~4095, 4096, 5)
    actual.mem_protect(DATA, 0x4000, 1)
    # Watch CPU stores, not host fixture setup. The executed native numeric and
    # selector routines may write only their declared context/output/stack RAM.
    # MMIO is intentionally not mapped or stubbed successful by this harness.
    writes = dict(count=0, min_address=None, max_end=None)
    def bounded_write(uc, access, address, size, value, user_data):
        if not RAM <= address < address + size <= RAM + 0x10000:
            raise AssertionError(('Native write outside laboratory RAM',
                                  hex(uc.reg_read(UC_ARM_REG_PC)), hex(address), size))
        writes['count'] += 1
        writes['min_address'] = min(address, writes['min_address'] or address)
        writes['max_end'] = max(address + size, writes['max_end'] or address + size)
    actual.hook_add(UC_HOOK_MEM_WRITE, bounded_write)
    profiles = [0, 1, 3, 5, *range(7, 18)]
    processing_cases, aggregate_cases, development_cases, color_cases = 0, 0, 0, 0
    for profile in profiles:
        # execute() below deliberately poisons all registers, including SP.
        for machine in [actual, baseline, donor]:
            machine.reg_write(UC_ARM_REG_SP, RAM + 0xE000)
        reference, is_donor = (donor, True) if profile == ALIAS else (baseline, False)
        reference_id = 18 if profile == ALIAS else profile
        for mode in range(5):
            for channel in range(6):
                for adjustment in [0, 4, 8]:
                    observed = outputs(actual, False, profile, mode, channel, adjustment)
                    expected = outputs(reference, is_donor, reference_id, mode, channel, adjustment)
                    assert observed == expected, (profile, mode, channel, adjustment)
                    processing_cases += 1
        for adjustment in [0, 4, 8]:
            for mask in [6, 0x16]:
                assert aggregate(actual, False, profile, adjustment, mask) == aggregate(
                    reference, is_donor, reference_id, adjustment, mask), (profile, adjustment, mask)
                aggregate_cases += 1
        for field46 in (0, 0x17):
            for field54 in (0, 1):
                for machine, profile_id in ((actual, profile), (reference, reference_id)):
                    call(machine, 0x17612a8 if machine is donor else 0x157a0fc, RAM)
                    call(machine, 0x1761e18 if machine is donor else 0x157ac60, RAM, profile_id)
                    for offset, value in {0x51:1, 0x46:field46, 0x54:field54}.items():
                        machine.mem_write(RAM + offset, bytes([value]))
                for xt2_entry, donor_entry, reverse, size in (
                        (0x156FAD8, 0x1756A90, True, 20),
                        (0x156AF80, 0x17524C0, False, 50)):
                    values = []
                    for machine in (actual, reference):
                        machine.mem_write(RAM + 0x2000, b'\xcc' * 64)
                        args = (RAM + 0x2000, RAM) if reverse else (RAM, RAM + 0x2000)
                        call(machine, donor_entry if machine is donor else xt2_entry, *args)
                        values.append(bytes(machine.mem_read(RAM + 0x2000, size)))
                    assert values[0] == values[1], (profile, field46, field54, hex(xt2_entry))
                    color_cases += 1
        development = execute(actual, profile)
        stock_development = execute(baseline, profile)
        assert development['success']
        value = int.from_bytes(development['output'][0x21d:0x221], 'little')
        expected = 16 if profile == ALIAS else int.from_bytes(
            stock_development['output'][0x21d:0x221], 'little')
        assert value == expected, (profile, value, expected)
        development_cases += 1
    # Calibration fixture must stay byte-identical through all processing calls.
    assert actual.mem_read(0x09000000, 0x40000) == baseline.mem_read(0x09000000, 0x40000)
    # The existing public SEPIA ID still uses the original conversion row.
    assert image[0xE8BBB4:0xE8BBB4+21*16] == STOCK.read_bytes()[0xE8BBB4:0xE8BBB4+21*16]
    # Candidate size fits original raw allocation, no shift of neighbouring data.
    assert image[0x950000:0x950400] == STOCK.read_bytes()[0x950000:0x950400]
    assert len(image) == len(STOCK.read_bytes())
    # The shared reader must return stock bytes even for every overridden key.
    # Only the private color-call reader returns donor bytes; misses stay stock.
    from eterna_parameter_overlay import overrides
    parameters = overrides()
    actual.reg_write(UC_ARM_REG_SP, RAM + 0xE000)
    for key in [0, 1, 0x100, 0x3FFFF, *parameters]:
        call(actual, 0xCE35E4, key)
        assert actual.reg_read(UC_ARM_REG_R0) == baseline.mem_read(0x09000000+key, 1)[0]
        call(actual, CODE + 0x40, key)
        expected = parameters[key][1] if key in parameters else baseline.mem_read(0x09000000+key, 1)[0]
        assert actual.reg_read(UC_ARM_REG_R0) == expected
    report = dict(image_sha256=digest(image), processing_cases=processing_cases,
        eterna_processing_cases=90, preserved_other_profiles=14,
        aggregate_cases=aggregate_cases, development_cases=development_cases,
        parameter_cases=len(parameters)+4, unscoped_parameter_cases=len(parameters)+4,
        color_cases=color_cases, parameter_fixture_unchanged=True,
        global_parameter_reader_preserved=image[0xCE323C:0xCE36AC] == STOCK.read_bytes()[0xCE323C:0xCE36AC],
        original_section_table_unchanged=True,
        original_conversion_table_unchanged=True, executable_code_page=True,
        readonly_data_pages=True, bounded_cpu_writes=writes,
        cpu_writes_confined_to_fixture_ram=True,
        global_flash_write_protection=False,
        full_boot_tested=False, hardware_verified=False,
        scope=__doc__, limitations=manifest['limitations'])
    path = ROOT / 'research/eterna-minimal-sd-verification.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
