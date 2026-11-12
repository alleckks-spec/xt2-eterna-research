"""Check genuine SDK directory-drain evidence, keeping its exact ELF boundary.

No firmware, upstream C, native tables or callback implementation is embedded.
The input probes execute the existing native SDK filesystem and scheduler.
This checker does not promote that bounded result to whole-port acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(output):
    paths = [ROOT / name / 'probe.json' for name in [
        'sdk-native-list-drain-original-v2-unverified',
        'sdk-native-list-drain-fixed-unverified']]
    builds = [ROOT / name for name in [
        'full-screen-capture-build-unverified', 'full-controls-build2-unverified']]
    reports = [json.loads(path.read_text()) for path in paths]
    source = ROOT / 'probe_sdk_native_listing_drain.py'
    assert reports[0]['checker_sha256'] == reports[1]['checker_sha256'] == sha(source)
    assert reports[0]['reused_checker_sha256'] == reports[1]['reused_checker_sha256']
    for index, (report, build) in enumerate(zip(reports, builds)):
        assert report['error'] is None
        assert report['elf_sha256'] == sha(build / 'mods.elf')
        assert report['expected_original'] is (index == 0)
        for key in ['firmware_api_substitutions', 'host_registration_writes', 'host_vfp_enable_writes']:
            assert report[key] == 0, key
        assert report['native_core_count'] == 2
        assert report['camera_tested'] is report['hardware_verified'] is False
        result = report['listing_result']
        assert result['actual_native_callbacks'] is True and result['host_poll_calls'] == 0
        assert result['original_entries_untouched'] is True
        assert all(row['task'] == 39 for row in result['old_replies'] + result['new_replies'])
        final = result['final']
        assert final['hold'] == final['callbacks'] == final['active'] == final['native_cursor_live'] == 0
        assert final['banks'] == [0] * 4
        admitted = result['accepted']
        assert admitted['before']['native_cursor_live'] == (1 if index == 0 else 0)
        assert admitted['old_end_seen'] is (index == 1)
    fixed = reports[1]['listing_result']
    assert [row['status'] for row in fixed['old_replies']] == [0, 0, 0, 0, 6]
    assert [row['status'] for row in fixed['new_replies']] == [0, 0, 0, 0, 6]
    assert set(fixed['native_names']) == {'A.TXT', 'B.TXT', 'C.TXT', 'D.TXT'}
    assert fixed['final']['job_b'] == 2 and fixed['final']['status_b'] == 0 and fixed['final']['count_b'] == 4
    assert any(row['before']['native_cursor_live'] == 1 and row['result'] == 0xffffffff
               for row in fixed['held_attempts'])
    receipt = json.loads((builds[1] / 'preparation.json').read_text())
    cardio = ROOT / 'cardio-list-drain-inputs/cardio.c'
    assert receipt['source_sha256'][str(cardio)] == sha(cardio)
    result = dict(status='PASS', scope=__doc__, checker_sha256=sha(Path(__file__)),
                  exact_elf_sha256=[report['elf_sha256'] for report in reports],
                  report_sha256={str(path): sha(path) for path in paths},
                  selected_cardio_sha256=sha(cardio),
                  original_admits_live_cursor=True, fixed_waits_for_native_end=True,
                  native_files_verified=4, native_callback_task=39,
                  corruption_reproduced=False, whole_port_qualified=False, hardware_verified=False)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'native-directory-drain-check-unverified')
    main(parser.parse_args().output)
