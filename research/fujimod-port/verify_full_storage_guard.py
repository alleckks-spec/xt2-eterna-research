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
    path.write_text(json.dumps(report, indent=2) + '\n')
    print('Catalog-first native settings restore PASS', args.saved_choice, flush=True)


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
