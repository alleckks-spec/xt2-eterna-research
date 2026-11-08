"""Bounded native queue -> reader -> private prepare -> isolated color consumption.

The same UC supplies native file transport and consumers. A host copy to the
prepared placement plus manual hook writes is an EXPLICIT supplied boundary,
not an activation implementation. Independent byte oracles check record getters;
native interpolation uses a separate direct-RAM differential reference, sharing
native arithmetic, and is not an independent mathematical oracle.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import shutil
import re
from datetime import datetime, timezone

import verify_xt2_normal_reader_pipeline as pipeline
import xt2_profile_container as container
import xt2_native_profile_package as package

ROOT = pipeline.ROOT
SCENARIOS = [(0, 0, 4), (0, 3, 4), (3, 2, 8)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def variants():
    # Authored perturbations of the pinned canonical vendor-derived fixture.
    # These are NOT wholly original synthetic tables, nor safe camera presets.
    canonical = package.canonical_document()
    result = []
    for name, tone_delta, gain_delta in [('laboratory_a', 128, 32),
                                         ('laboratory_b', 256, 64)]:
        document = copy.deepcopy(canonical)
        document['display_name'] = name
        tone = bytearray.fromhex(document['tone_record51_hex'])
        struct.pack_into('<H', tone, 16, struct.unpack_from('<H', tone, 16)[0] + tone_delta)
        gain = bytearray.fromhex(document['gain_records77_111_hex'])
        for index in range(35):
            offset = index * 48 + 4
            struct.pack_into('<H', gain, offset, struct.unpack_from('<H', gain, offset)[0] + gain_delta)
        document['tone_record51_hex'] = tone.hex()
        document['gain_records77_111_hex'] = gain.hex()
        profile = package.validate(document)
        blob = container.pack(profile)
        assert container.unpack(blob).tone == profile.tone
        result.append((name, profile, blob, dict(tone_LE16_offset16_add=tone_delta,
                                                every_gain_LE16_offset4_add=gain_delta)))
    return result


def observer(profile, blob):
    def consume(u, payload, hooks, base):
        from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_PROT_READ, UC_PROT_EXEC
        from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC
        from verify_interpolated_profile_outputs import outputs, call
        from verify_custom_profile_interpolation import setup
        from verify_tone_table_port import call as tone_call
        from verify_gain_table_port import call as gain_call
        from verify_profile_selectors import RAM
        staged = bytes(u.mem_read(payload, 0x4000))
        hook_words = bytes(u.mem_read(hooks, 348))
        # Supplied host boundary, performed only in this isolated test machine.
        u.mem_map(base, 0x4000)
        u.mem_write(base, staged)
        u.mem_protect(base, 0x4000, UC_PROT_READ | UC_PROT_EXEC)
        for address, old, new in struct.iter_unpack('<3I', hook_words):
            assert bytes(u.mem_read(address, 4)) == struct.pack('<I', old)
            u.mem_write(address, struct.pack('<I', new))
        u.ctl_flush_tb()
        # Same parameter backing as the existing synthetic consumer fixture.
        stock = (ROOT/'firmware/extracted/xt2-4.41/inverted.bin').read_bytes()[0xc025c:0x10025c]
        u.mem_map(0x09000000, 0x40000)
        u.mem_write(0x09000000, stock)
        u.mem_map(0x1025000, 0x1000)
        u.mem_write(0x1025344, struct.pack('<I', 0x09000000))
        u.reg_write(UC_ARM_REG_C1_C0_2, 0xf << 20)
        u.reg_write(UC_ARM_REG_FPEXC, 1 << 30)
        trace = dict(pcs=[], reads=[], native=[])
        native_entries = (0x15703f8, 0x156a140, 0xc4d298, 0xc4d4f4, 0xce323c)
        def native_entry(uc, pc, size, data):
            trace['native'].append(hex(pc))
        for pc in native_entries:
            u.hook_add(UC_HOOK_CODE, native_entry, begin=pc, end=pc)
        def execute(uc, pc, size, data):
            trace['pcs'].append(hex(pc))
        def read(uc, access, address, size, value, data):
            trace['reads'].append(dict(address=hex(address), size=size,
                                       bytes=bytes(uc.mem_read(address, size)).hex()))
        u.hook_add(UC_HOOK_CODE, execute, begin=base, end=base+0x3fff)
        for offset, size in [(0x1e58, 72), (0x2e70, 1680), (0x3600, 1192)]:
            u.hook_add(UC_HOOK_MEM_READ, read, begin=base+offset, end=base+offset+size-1)
        def take_trace():
            result = dict(native_entry_hits=trace['native'][:], payload_instruction_count=len(trace['pcs']),
                          payload_instruction_addresses=sorted(set(trace['pcs']), key=lambda s:int(s,16)),
                          staged_data_reads=trace['reads'][:])
            trace['native'].clear()
            trace['pcs'].clear()
            trace['reads'].clear()
            return result
        # Independent bytes calculated directly from the input container, not
        # the materializer, staged copy, payload builder, or ARM getter output.
        tone_expected = blob[64+4:64+13] + blob[64+14:64+70]
        tone_status, tone_actual = tone_call(u, 0xc4d298, 51)
        assert tone_status == 1 and tone_actual == tone_expected
        tone_trace = take_trace()
        gains = []
        for index in (77, 94, 111):
            offset = 136+(index-77)*48+4
            expected = blob[offset:offset+44]
            actual = gain_call(u, 0xc4d4f4, index)
            assert actual == expected
            gains.append(dict(index=index, actual=actual.hex(), expected=expected.hex(), trace=take_trace()))
        parameters = []
        for key in (0x9bbc, 0x9f40):
            expected = next(value for k, value in struct.iter_unpack('<IB3x', blob[1816:]) if k == key)
            call(u, 0xce323c, key)
            actual = u.reg_read(UC_ARM_REG_R0)
            assert actual == expected
            parameters.append(dict(key=hex(key), actual=actual, expected=expected, trace=take_trace()))
        # Exact stock record output oracle, using original unmodified firmware.
        from firmware_analysis import Firmware
        f = Firmware('xt2-4.41', True)
        stock_tone_record = f.read(0xfa2b00, 72)
        status, actual = tone_call(u, 0xc4d298, 0)
        expected = stock_tone_record[4:13]+stock_tone_record[14:70]
        assert status == 1 and actual == expected
        stock_getter = dict(tone_index0_matches=True, trace=take_trace())
        actual = gain_call(u, 0xc4d4f4, 0)
        assert actual == f.read(0xfa1c84+4, 44)
        stock_getter.update(gain_index0_matches=True, gain_trace=take_trace())
        direct = setup(profile, False)
        from verify_interpolated_profile_outputs import runtime
        stock_reference = runtime('xt2-4.41', False)
        records = []
        for slot in (18, 3):
            for scenario in SCENARIOS:
                actual = outputs(u, False, slot, *scenario)
                trace_result = take_trace()
                expected = outputs(direct if slot == 18 else stock_reference, False, slot, *scenario)
                assert actual == expected, (slot, scenario, actual, expected)
                assert '0x15703f8' in trace_result['native_entry_hits'] and '0x156a140' in trace_result['native_entry_hits']
                if slot == 18:
                    assert any(base+0x1e58 <= int(r['address'],16) < base+0x1ea0 for r in trace_result['staged_data_reads'])
                    assert any(base+0x2e70 <= int(r['address'],16) < base+0x3500 for r in trace_result['staged_data_reads'])
                records.append(dict(slot=slot, mode=scenario[0], channel=scenario[1], adjustment=scenario[2],
                                    actual=actual, expected=expected, matches=True, trace=trace_result))
        assert bytes(u.mem_read(payload,0x4000)) == staged
        assert bytes(u.mem_read(base,0x4000)) == staged
        assert bytes(u.mem_read(0x09000000,0x40000)) == stock
        return dict(same_uc_as_native_reader=True, staged_buffer=hex(payload), consumer_base=hex(base),
                    host_copy_bytes=0x4000, manually_written_hook_words=29,
                    prepared_hook_words_sha256=sha(hook_words), prepared_bytes_retained=True,
                    original_parameter_RAM_unchanged=True,
                    independent_record_oracle=dict(tone=dict(index=51, actual=tone_actual.hex(),
                                                            expected=tone_expected.hex(), trace=tone_trace),
                                                   gains=gains, parameters=parameters, stock=stock_getter),
                    differential_interpolation=records,
                    numerical_reference='Separate UC: original XT2 arithmetic and table access with explicit custom parameters written to RAM; not an independent mathematical oracle.')
    return consume


def pin_inputs():
    # Static transitive local Python import closure plus compiled translation
    # units, discovered before execution. Dynamic helper loading is audited at end.
    paths = []
    pending_python = [Path(__file__).resolve()]
    seen_python = set()
    while pending_python:
        source = pending_python.pop()
        if source in seen_python: continue
        seen_python.add(source); paths.append(source)
        for node in ast.walk(ast.parse(source.read_text())):
            names = [n.name for n in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                local = ROOT/'scripts'/(name.split('.')[0]+'.py')
                if local.exists(): pending_python.append(local)
    paths += [ROOT/'scripts'/name for name in pipeline.SOURCES]
    paths += list((ROOT/'firmware/research/profile-materializer-unverified').glob('*.h'))
    paths += [ROOT/p for p in ['firmware/research/profile-materializer-unverified/runtime-template.reloc',
                              'firmware/extracted/xt2-4.41/inverted.bin',
                              'firmware/extracted/xh1-2.15/inverted.bin',
                              'research/color-parameter-port-execution.json',
                              'research/selection-parameter-port-execution.json']]
    for model in ('xt2-4.41', 'xh1-2.15'):
        directory = ROOT/'firmware/extracted'/model
        manifest_file = directory/'manifest.json'
        paths.append(manifest_file)
        manifest = json.loads(manifest_file.read_text())
        paths += [directory/item['file'] for item in manifest['streams'] if 'inner_header' in item]
        if (directory/'layout.json').exists():
            layout_file = directory/'layout.json'
            paths.append(layout_file)
            paths += [directory/item['file'] for item in json.loads(layout_file.read_text())['units']]
    # Include every recursively named quoted C header in all compiled inputs.
    pending = [ROOT/'scripts'/n for n in pipeline.SOURCES]
    seen = set()
    while pending:
        source = pending.pop()
        if source in seen: continue
        seen.add(source)
        for name in re.findall(r'#include \"([^\"]+)\"', source.read_text()):
            header = next(p for p in (source.parent/name, ROOT/'scripts'/name, ROOT/'firmware/research/profile-materializer-unverified'/name) if p.exists())
            paths.append(header); pending.append(header)
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(set(paths))}


def main():
    import sys
    pins = pin_inputs()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    evidence = ROOT/'research'/('loaded-profile-consumption-'+stamp)
    evidence.mkdir()
    for name in pins:
        if Path(name).suffix in ('.py','.c','.h','.S'):
            target=evidence/'snapshot'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
    old_source=ROOT/'research/normal-reader-validation-20261108T133351/snapshot/scripts/verify_xt2_normal_reader_pipeline.py'
    shutil.copyfile(old_source,evidence/'historical-pipeline-verifier.py')
    (evidence/'observer-seam-history.json').write_text(json.dumps(dict(historical_source_sha256=sha(old_source.read_bytes()),current_source_sha256=pins['scripts/verify_xt2_normal_reader_pipeline.py'],historical_source=str(old_source.relative_to(ROOT)),frozen_report_unchanged=True),indent=2)+'\n')
    (evidence/'pre-input-hashes.json').write_text(json.dumps(pins, indent=2)+'\n')
    manifest = (ROOT/'firmware/research/profile-materializer-unverified/runtime-template.reloc').read_bytes()
    profiles = variants()
    input_profiles = [dict(name=n, container_sha256=sha(b), profile_sha256=p.digest(),
                          perturbations=changes) for n,p,b,changes in profiles]
    (evidence/'pre-profile-hashes.json').write_text(json.dumps(input_profiles, indent=2)+'\n')
    from firmware_analysis import Firmware
    firmware = Firmware('xt2-4.41', True)
    with tempfile.TemporaryDirectory(prefix='xt2-loaded-consumption-') as directory:
        sections, symbols, compiled = pipeline.build(Path(directory))
        cases = []
        for name, profile, blob, changes in profiles:
            print('Consuming '+name, flush=True)
            case = pipeline.assay(firmware, sections, symbols, blob, manifest,
                                  prepared_observer=observer(profile, blob))
            fixture_hook_addresses=sorted([int(a,16) for a in case['filesystem']['boundary_roles']]+[0x57e20])
            assert not set(fixture_hook_addresses).intersection((0x15703f8,0x156a140,0xc4d298,0xc4d4f4,0xce323c))
            case.update(name=name, perturbations=changes,fixture_hook_addresses=[hex(a) for a in fixture_hook_addresses],numeric_consumer_entries_not_stubbed=True)
            cases.append(case)
    outputs = [c['prepared_consumption']['differential_interpolation'] for c in cases]
    sensitivity = []
    for a,b in zip(*outputs):
        assert (a['slot'],a['mode'],a['channel'],a['adjustment']) == (b['slot'],b['mode'],b['channel'],b['adjustment'])
        changed = [k for k in ('tone','gain','bounds') if a['actual'][k] != b['actual'][k]]
        if a['slot'] == 3:
            assert not changed
        sensitivity.append(dict(slot=a['slot'],mode=a['mode'],channel=a['channel'],adjustment=a['adjustment'],changed=changed))
    assert any('tone' in c['changed'] for c in sensitivity if c['slot']==18)
    assert any('gain' in c['changed'] for c in sensitivity if c['slot']==18)
    post = pin_inputs()
    assert pins == post, 'Pinned input changed during assay; results not publishable'
    loaded_helpers = sorted({str(Path(m.__file__).resolve().relative_to(ROOT)) for m in sys.modules.values()
                             if getattr(m,'__file__',None) and str(Path(m.__file__).resolve()).startswith(str(ROOT/'scripts')+'/')})
    assert all(p in pins for p in loaded_helpers)
    report = dict(scope=__doc__, passed=True, evidence_directory=str(evidence.relative_to(ROOT)),
                  input_hashes_pre_run=pins, inputs_unchanged_post_run=True,
                  loaded_local_helpers=loaded_helpers, profiles=input_profiles,
                  firmware_units=[dict(base=hex(b),sha256=sha(d)) for b,d in firmware.units],
                  manifest_sha256=sha(manifest), compiled=compiled,cases=cases,
                  sensitivity=sensitivity, custom_interpolation_comparisons=6,stock_interpolation_comparisons=6,
                  activation=False, owner_tail_implementation_changed=False, physical_camera=False,
                  full_emulation=False,mounted_media=False,
                  limitations=['Native storage lower layers, task identity, and mounted context remain explicit models from the reused native queue fixture.',
                               'Harness releases route after worker return; no autonomous owner/tail integration or consumer exclusion is implemented.',
                               'Host copy and manual isolated hook writes supply the prepare-to-consumer boundary; no runtime installation/cache/quiescence proof.',
                               'Byte oracles are independent container/stock slicing. Numerical comparison shares original ARM arithmetic and is differential, not an independent math oracle.',
                               'Laboratory profiles perturb canonical vendor-derived tables. Representation validity is not numerical/hardware safety.',
                               'Only three correlated synthetic contexts per profile and one noncustom slot; no pixels, peripheral output, full boot, or hardware.'],
                  reproduction='LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_xt2_loaded_profile_consumption.py')
    out = ROOT/'research/native-loaded-profile-consumption-verification.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    (evidence/'post-input-hashes.json').write_text(json.dumps(post,indent=2)+'\n')
    print(json.dumps(dict(report=str(out), passed=True,custom=6,stock=6,sensitivity=sensitivity)))


if __name__ == '__main__':
    main()
