"""Reuse frozen native checks on the exact full-storage-guard ELF.

Only artifact paths and native UI setup digest change. Existing file/calibration,
post-FAT frame, explicit ticks and supplied pending-callback boundaries remain
visible. No successful mount, native API reply or new device model is added.
"""
import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path
from build_full_storage_guard_candidate import BUILD, ROOT
import verify_card_processing as processing
import verify_card_films_menu as menu_fixture

OUT = ROOT / 'full-storage-guard-check-unverified'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture_machine(initialized=False):
    path = Path(menu_fixture.__file__).resolve()
    frozen = json.loads((ROOT / 'common-card-file-check-unverified/freeze.json').read_text())['files']
    assert sha(path.read_bytes()) == frozen[str(path)]
    source = inspect.getsource(menu_fixture.main)
    anchor = '    selected=[]\n' if initialized else '    init=[]\n'
    assert source.count(anchor) == 1
    prefix = source.split(anchor)[0].replace('def main():', 'def setup():', 1)
    old = "assert sha(raw)=='db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754'"
    assert prefix.count(old) == 1
    prefix = prefix.replace(old, 'assert sha(raw)==' + repr(sha((BUILD / 'mods.elf').read_bytes())))
    prefix = prefix.replace('0x1388000', 'REGION_START')
    prefix += ('    return u,symbols,call,api,clock,init,exceptions\n' if initialized else
               '    return u,symbols,call,api,clock,exceptions\n')
    region, = json.loads((BUILD / 'manifest.json').read_text())['regions']
    namespace = dict(vars(menu_fixture), BUILD=BUILD, REGION_START=int(region['address'], 0))
    exec(compile(prefix, str(path) + '::guard-before-manual-init', 'exec'), namespace)
    return namespace['setup'](), dict(source_sha256=sha(path.read_bytes()),
        adapted_prefix_sha256=sha(prefix.encode()), artifact_elf_sha256=sha((BUILD / 'mods.elf').read_bytes()))


def uninitialized_machine():
    return fixture_machine(False)


def callback_cases(output):
    import verify_cardio_open_guard as controls
    from verify_cardio_native_worker import Assay
    (u, symbols, call, api, clock, init, exceptions), setup = fixture_machine(True)
    m = Assay.__new__(Assay)
    m.u, m.symbols, m.clock = u, symbols, clock
    # Use existing scratch-call ABI, not a replacement API implementation.
    def bank_observation(machine, job):
        matches = [index for index in range(4)
            if machine.word(symbols['bank_job'] + 4 * index) == job
            and machine.word(symbols['bank_state'] + 4 * index) in (1, 2)]
        assert len(matches) <= 1
        return matches[0] if matches else 0xffffffff
    original_path = Path(controls.__file__).resolve()
    source = inspect.getsource(controls.verify)
    start = '    u = m.u\n'
    assert source.count(start) == 1
    body = source[source.index(start):]
    for expected in [0, 1]:
        old = "assert m.api('x70_lifetime_live') == " + str(expected)
        assert body.count(old) == 1
        body = body.replace(old, "assert m.word(m.symbols['live']) == 0 and m.word(m.symbols['callbacks']) == " + str(expected))
    body = body.replace("m.api('x70_cardio_bank', JOB)", 'BANK_OBSERVATION(m, JOB)')
    old = "if section['sh_flags'] & 2 and section['sh_size']:"
    assert body.count(old) == 1
    body = body.replace(old, old[:-1] + " and REGION_START <= section['sh_addr'] < 0x13c0000:")
    code = 'def run():\n' + body
    namespace = dict(vars(controls), m=m, raw=(BUILD / 'mods.elf').read_bytes(),
        stock=(ROOT.parents[1] / 'firmware/research/xt2-stock-sd-unverified/ffboot.bin').read_bytes(),
        original=False, output=output, BANK_OBSERVATION=bank_observation,
        REGION_START=int(json.loads((BUILD / 'manifest.json').read_text())['regions'][0]['address'], 0))
    exec(compile(code, str(original_path) + '::full-elf-callback-cases', 'exec'), namespace)
    namespace['run']()
    report = json.loads(output.read_text())
    report.update(scope=__doc__ + '\n' + controls.__doc__, full_ordinary_elf=True,
        setup=setup, init_calls=init, native_vfp_exceptions=exceptions,
        getter_checks_replaced_by_real_linked_state_observations=['bank_job/bank_state', 'live=0 and callbacks=0/1'],
        original_checker_sha256=sha(original_path.read_bytes()), adapted_body_sha256=sha(code.encode()),
        checker_sha256=sha(Path(__file__).read_bytes()))
    output.write_text(json.dumps(report, indent=2) + '\n')


def catalog_first_restore():
    """Follow the new owner's real timer order, retaining the native workers."""
    import verify_common_card_file as common
    import verify_common_settings_restore as restore
    parser = argparse.ArgumentParser()
    parser.add_argument('--saved-choice', choices=restore.SAVED_NAMES, default='eterna')
    parser.add_argument('--invalid-json', action='store_true')
    parser.add_argument('--read-error', type=int, default=0)
    parser.add_argument('--date-card-name', type=int, choices=[0, 1])
    parser.add_argument('--date-folders', type=int, choices=[0, 1])
    parser.add_argument('--menu-flow', action='store_true')
    args = parser.parse_args()
    restore.SAVED_CHOICE = args.saved_choice
    captured = {}
    def capture_native(machine, filesystem, ticks, callbacks, workers):
        captured.update(m=machine, fs=filesystem, ticks=ticks, callbacks=callbacks, workers=workers)
    original_path = Path(common.__file__).resolve()
    pins = json.loads((ROOT / 'common-card-file-check-unverified/freeze.json').read_text())['files']
    assert sha(original_path.read_bytes()) == pins[str(original_path)]
    source = inspect.getsource(common.main)
    constructors = '    for entry in [0xcec598,0xcec634,0xcdf570]:assert m.call(entry)==0\n'
    assert source.count(constructors) == 1
    source = source.replace(constructors, '')
    old = "body+'    return dict(loader="
    assert source.count(old) == 1
    source = source.replace(old, "body+'    CAPTURE_NATIVE(m,fs,ticks,callbacks,workers)\\n    return dict(loader=")
    old = 'namespace=dict(vars(filecheck));namespace.update('
    assert source.count(old) == 1
    source = source.replace(old, "namespace=dict(vars(filecheck));namespace['CAPTURE_NATIVE']=CAPTURE_NATIVE;namespace.update(")
    # The original common helper already replaces the dead-stripped getter;
    # retain its match and alter only its new direct-state expectation.
    direct = '"    assert m.word(m.symbols[\'live\'])==2 and m.word(m.symbols[\'callbacks\'])==0\\n"'
    assert source.count(direct) == 1
    source = source.replace(direct, direct.replace('==2', '==3'))
    destination = restore.OUT / args.saved_choice
    if args.date_card_name is not None or args.date_folders is not None:
        destination = destination / ('save-data-' + str(args.date_folders if args.date_folders is not None else 0)
            + '-' + str(args.date_card_name if args.date_card_name is not None else 1))
    if args.menu_flow:
        destination = destination / 'menu-owner-flow'
    destination.mkdir(parents=True, exist_ok=True)
    namespace = dict(vars(common), make_machine=restore.make_started_machine, OUT=destination,
        CAPTURE_NATIVE=capture_native)
    source = source.replace('def main():', 'def catalog_phase():', 1)
    before_argv = sys.argv
    sys.argv = [sys.argv[0], *(['--invalid-json'] if args.invalid_json else []),
                *(['--read-error', str(args.read_error)] if args.read_error else [])]
    try:
        exec(compile(source, str(original_path) + '::catalog-before-settings', 'exec'), namespace)
        namespace['catalog_phase']()
    finally:
        sys.argv = before_argv
    m, fs, ticks, callbacks = [captured[name] for name in ['m', 'fs', 'ticks', 'callbacks']]
    restore.startup_workers.update(captured['workers'])
    catalog_callbacks = list(callbacks)
    callbacks.clear()
    fs.trace.clear()
    # A native next periodic tick admits settings only after the real catalog
    # and its file requests have retired. No timer slot or ready bit is changed.
    supplied_save_data = args.date_card_name is not None or args.date_folders is not None
    expected_save_data = [args.date_folders if args.date_folders is not None else 0,
                          args.date_card_name if args.date_card_name is not None else 1]
    settle = restore.settle_startup
    settings_adapter_sha256 = None
    if supplied_save_data and settle.__name__ == 'settle_startup':
        settle, settings_adapter_sha256 = supplied_sections_settle(dict(
            save_data=dict(date_folders=bool(expected_save_data[0]), date_card_name=bool(expected_save_data[1])),
            stock_choices=dict(current=dict(values=[dict(setting='film_simulation', value=args.saved_choice)]))))
    settle(m, fs, ticks, callbacks)
    ticks(121)
    index = restore.SAVED_NAMES.index(args.saved_choice)
    key = m.word(m.symbols['film_choice_key'])
    assert key == 32 + index and m.call(0xb510b8, 0x1fc, 0) == 0
    rejected = bool(args.invalid_json or args.read_error)
    if args.saved_choice != 'card_1' or not rejected:
        restore.check_restored_still(m, key, index)
    else:
        assert m.api('film_xt20_select', 0) == 0
    owner, runtime = m.symbols['x70_stock_choice_settings'], m.symbols['x70_settings_runtime']
    extra = m.symbols['save_data_settings']
    assert m.word(runtime + 128) == 2
    assert {m.word(runtime), m.word(runtime + 4)} == {owner, extra}
    for address in [owner, extra]:
        assert m.word(address + 104) == 2 and m.word(address + 52) == 1
        assert m.word(address + 68) == int(address == owner or supplied_save_data) and m.word(address + 64) == 0
    assert m.word(m.symbols['save_data_date_folders']) == expected_save_data[0]
    assert m.word(m.symbols['save_data_date_card_name']) == expected_save_data[1]
    assert m.word(m.symbols['x70_cardio_active']) == m.word(m.symbols['callbacks']) == 0
    assert bytes(m.u.mem_read(m.symbols['bank_state'], 16)) == bytes(16)
    name = 'invalid-json' if args.invalid_json else 'read-error' if args.read_error else 'valid'
    path = destination / (name + '.json')
    report = json.loads(path.read_text())
    report.update(scope=__doc__, status='PASS', saved_choice=args.saved_choice,
        native_startup_order='catalog then settings, from unchanged native timer slots',
        catalog_callbacks=catalog_callbacks, native_settings_startup=restore.startup_evidence,
        owners=2, settings_owner_addresses=[owner, extra], save_data_values=expected_save_data,
        supplied_save_data_section=supplied_save_data, settings_adapter_sha256=settings_adapter_sha256,
        restored_key=key, explicit_selection_setters_after_decode=0,
        adapted_common_sha256=sha(source.encode()), checker_sha256=sha(Path(__file__).read_bytes()))
    if args.menu_flow:
        assert expected_save_data == [0, 1]
        report['native_save_data_menu_owner'] = menu_owner_flow(m, ticks)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print('Catalog-first native settings restore PASS', args.saved_choice, flush=True)


def menu_owner_flow(machine, ticks):
    """Use real menu entry/property/bank operations after native owner loading."""
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_PC
    import struct
    import verify_common_settings_restore as restore
    from verify_cardio_native_worker import RETURN
    u, symbols, call = restore.active_machine
    native = json.loads((BUILD / 'target.json').read_text())['symbols']
    owner = symbols['save_data_settings']
    word = machine.word
    def current():
        return dict(value=word(symbols['save_data_date_card_name']), requested=word(owner + 92),
            completed=word(owner + 96), failed=word(owner + 100),
            menu_open=bytes(u.mem_read(symbols['menu_open'], 1))[0],
            shown=call(native['setp_effective_get'], 0x7f01, task=True),
            film=word(symbols['film_choice_key']))
    assert word(owner + 92) == 0 and word(owner + 104) == 2
    assert bytes(u.mem_read(symbols['menu_open'], 1)) == b'\0'
    # Preserve the supplied REC3 environment. Otherwise SETUP_REC5 alone
    # would suppress settings work and confound the menu_open check.
    assert bytes(u.mem_read(symbols['ui_mode'], 1)) == b'\x03'
    before_film = word(symbols['film_choice_key'])
    assert call(0x13debf0, 1, 0x49, 0, 0, task=True) == 1
    parent_node = list(struct.unpack('<8I', u.mem_read(0x11802c0, 32)))
    assert parent_node[4] == 9
    assert call(0x13debf0, 1, 0x7f03, 0, 0, task=True) == 1
    option_node = list(struct.unpack('<8I', u.mem_read(0x11802c0, 32)))
    assert option_node[4] == 2
    initial = current()
    assert initial['value'] == 1 and initial['shown'] == 0 and initial['menu_open'] == 1
    calls = []
    hooks = []
    for name in ['storage_open_file_async', 'storage_read_async_wrapper', 'storage_write_file_async',
                 'storage_entry_async', 'storage_seek_async']:
        address = native[name]
        hooks.append(u.hook_add(UC_HOOK_CODE,
            lambda uc, pc, size, data, name=name: calls.append(dict(api=name, pc=hex(pc))),
            begin=address, end=address))
    try:
        call(0x154b700, 0x7f01, 1, task=True)
        preview = current()
        assert preview['value'] == 0 and preview['shown'] == 1 and preview['requested'] == 1
        ticks(121)
        assert not calls and word(symbols['x70_cardio_active']) == 0
        call(native['bank_snapshot'], 1, task=True)
        canceled = current()
        assert canceled['value'] == 1 and canceled['shown'] == 0 and canceled['requested'] == 2
        ticks(121)
        assert not calls and word(symbols['x70_cardio_active']) == 0
        call(0x154b700, 0x7f01, 1, task=True)
        selected = current()
        assert selected['value'] == 0 and selected['requested'] == 3
        call(native['bank_snapshot'], 0, task=True)
        call(0x154b700, 0x7f01, 1, task=True)
        committed = current()
        assert committed['value'] == 0 and committed['shown'] == 1 and committed['requested'] == 3
        ticks(121)
        assert not calls and word(symbols['x70_cardio_active']) == 0
        assert committed['completed'] == committed['failed'] == 0
        assert bytes(u.mem_read(symbols['menu_open'], 1)) == b'\x01'
        assert word(symbols['film_choice_key']) == before_film
        deferred_calls = list(calls)
        assert call(0x13debf0, 2, 0, 0x22, 0, task=True) == 1
        assert bytes(u.mem_read(symbols['menu_open'], 1)) == b'\0'
        ticks(121)
        assert len(calls) == 1 and calls[0]['api'] == 'storage_open_file_async'
        job = word(symbols['x70_cardio_active'])
        assert job
        encoded = bytes(u.mem_read(word(job + 52), word(job + 20)))
        assert json.loads(encoded) == dict(save_data=dict(date_card_name=False),
            stock_choices=dict(current=dict(values=[dict(setting='film_simulation', value='eterna')])))
        worker_runs = []
        outer = u.context_save()
        for entry, end, loop in [(0x969b54, 0x969c00, 0x969bb8), (0x969fcc, 0x96a090, 0x96a00c)]:
            u.context_restore(restore.startup_workers[entry])
            u.emu_start(end, RETURN, count=1)
            assert u.reg_read(UC_ARM_REG_PC) == loop
            machine.execute_to(loop, end)
            restore.startup_workers[entry] = u.context_save()
            worker_runs.append(dict(start=hex(loop), end=hex(end)))
        u.context_restore(outer)
        ticks(121)
        assert word(symbols['x70_cardio_active']) == word(symbols['callbacks']) == 0
        assert len(calls) == 1  # Actual native open refuses before write/close.
        assert word(owner + 92) == word(owner + 100) == 3 and word(owner + 96) == 0
        assert word(owner + 64) == 5 and word(owner + 32 + 16) == 1
        assert bytes(u.mem_read(symbols['bank_state'], 16)) == bytes(16)
        failed_after_close = current()
    finally:
        for hook in hooks:
            u.hook_del(hook)
    return dict(parent_node=parent_node, option_node=option_node, initial=initial, preview=preview,
        canceled=canceled, selected=selected, committed=committed,
        native_property=hex(0x7f01), explicit_ticks=605, native_file_requests_while_menu_open=deferred_calls,
        native_file_requests_after_close=calls, serialized_document_sha256=sha(encoded), serialized_document=json.loads(encoded),
        native_write_refusal_workers=worker_runs, failed_after_close=failed_after_close,
        native_menu_sets_open_and_close=True, host_menu_open_writes=0, supplied_ui_mode=3,
        initial_film=before_film, final_film=word(symbols['film_choice_key']),
        menu_left_open=False, successful_settings_write=False, hardware_verified=False)


def supplied_sections_settle(document):
    import verify_common_settings_restore as restore
    settings_source = inspect.getsource(restore.settle_startup)
    old = "    settings_document=json.dumps(dict(stock_choices=dict(current=dict(values=[dict(setting='film_simulation',value=SAVED_CHOICE)])))).encode()"
    assert settings_source.count(old) == 1
    settings_source = settings_source.replace(old, '    settings_document=json.dumps(SUPPLIED_SETTINGS_DOCUMENT).encode()')
    settings_source = settings_source.replace('def settle_startup(', 'def settle_supplied_sections(', 1)
    settings_namespace = dict(vars(restore), SUPPLIED_SETTINGS_DOCUMENT=document)
    exec(compile(settings_source, str(Path(restore.__file__)) + '::supplied-save-data-section', 'exec'), settings_namespace)
    return settings_namespace['settle_supplied_sections'], sha(settings_source.encode())


def has_save_data():
    from elftools.elf.elffile import ELFFile
    with (BUILD / 'mods.elf').open('rb') as stream:
        return any(symbol.name == 'save_data_settings'
            for symbol in ELFFile(stream).get_section_by_name('.symtab').iter_symbols())


def main():
    global BUILD, OUT
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--case', choices=['callbacks', 'timer', 'processing', 'file', 'restore', 'write'], required=True)
    parser.add_argument('--build', type=Path, default=BUILD)
    parser.add_argument('--output', type=Path, default=OUT)
    args, remainder = parser.parse_known_args()
    BUILD, OUT = args.build.resolve(), args.output.resolve()
    sys.argv = [sys.argv[0], *remainder]
    OUT.mkdir(exist_ok=True)
    if args.case == 'callbacks':
        callback_cases(OUT / 'callbacks.json')
        return
    if args.case == 'timer':
        import verify_full_timer_dispatch as timer
        timer.make_machine = lambda build: fixture_machine(True)
        for original in [True, False]:
            sys.argv = [sys.argv[0], '--build', str(BUILD), '--output',
                str(OUT / ('dispatch-original.json' if original else 'dispatch-fixed.json')),
                *(['--original-stack'] if original else [])]
            timer.main()
        return
    if args.case == 'processing':
        processing.BUILD = BUILD
        processing.OUT = OUT / 'processing'
        processing.make_machine = lambda: fixture_machine(True)
        processing.main()
        return
    import verify_common_card_file as common
    import verify_common_settings_restore as restore
    common.BUILD = restore.BUILD = BUILD
    common.make_machine = lambda: fixture_machine(True)
    restore.make_machine = uninitialized_machine
    if args.case == 'file':
        common.OUT = OUT / 'file'
        common.main()
    elif args.case == 'restore':
        restore.OUT = OUT / 'restore'
        restore.OUT.mkdir(exist_ok=True)
        if has_save_data():
            catalog_first_restore()
        else:
            restore.main()
    else:
        import verify_common_settings_write as write
        write.OUT = OUT / 'write'
        if has_save_data():
            restore.main = catalog_first_restore
            original = Path(write.__file__).resolve()
            source = inspect.getsource(write.main)
            old = "assert produced==dict(stock_choices=dict(current=dict(values=[dict(setting='film_simulation',value='eterna')])))"
            assert source.count(old) == 1
            options = argparse.ArgumentParser(add_help=False)
            options.add_argument('--date-card-name', type=int, choices=[0, 1])
            options.add_argument('--date-folders', type=int, choices=[0, 1])
            options.add_argument('--saved-choice', choices=restore.SAVED_NAMES, default='eterna')
            preferences, _ = options.parse_known_args()
            expected = dict(stock_choices=dict(current=dict(values=[dict(setting='film_simulation', value='eterna')])))
            nondefault = {}
            if preferences.date_card_name == 0:
                nondefault['date_card_name'] = False
            if preferences.date_folders == 1:
                nondefault['date_folders'] = True
            if nondefault:
                expected['save_data'] = nondefault
                write.OUT = OUT / ('write-save-data-' + str(preferences.date_folders if preferences.date_folders is not None else 0)
                    + '-' + str(preferences.date_card_name if preferences.date_card_name is not None else 1))
            source = source.replace(old, 'assert produced==EXPECTED_SETTINGS_DOCUMENT,produced')
            namespace = dict(vars(write), OUT=write.OUT, EXPECTED_SETTINGS_DOCUMENT=expected)
            if preferences.date_card_name is not None or preferences.date_folders is not None:
                supplied = dict(save_data=dict(
                    date_card_name=preferences.date_card_name != 0, date_folders=preferences.date_folders == 1),
                    stock_choices=dict(current=dict(values=[dict(setting='film_simulation', value=preferences.saved_choice)])))
                native_settle, settle_digest = supplied_sections_settle(supplied)
                needle = 'captured={};original=restore.settle_startup'
                assert source.count(needle) == 1
                source = source.replace(needle, 'captured={};original=SUPPLIED_SECTIONS_SETTLE')
                namespace['SUPPLIED_SECTIONS_SETTLE'] = native_settle
            source = source.replace('def main():', 'def verify_volume_write():', 1)
            exec(compile(source, str(original) + '::save-data-owner-regression', 'exec'), namespace)
            namespace['verify_volume_write']()
            path = write.OUT / 'verification.json'
            report = json.loads(path.read_text())
            report.update(adapter_sha256=sha(Path(__file__).read_bytes()),
                adapted_checker_sha256=sha(source.encode()), expected_shared_settings_document=expected,
                default_section_omitted=not bool(nondefault))
            path.write_text(json.dumps(report, indent=2) + '\n')
        else:
            write.main()


if __name__ == '__main__':
    main()
