"""Native import/cache/cancel validates coherent WB marker invalidation.

Reuse the existing full native import checker. Both primary and native-shadow
metadata start marked; only the declared marker changes, before the actual
journal-cache write. The negative control qualifies the earlier primary-only
candidate's stale-shadow reactivation, not a successful complete port.
"""
import argparse
import inspect
import json
import sys
from pathlib import Path
import verify_wb_import_lifecycle as native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-stale-shadow', action='store_true')
    args = parser.parse_args()
    original = Path(native.__file__).resolve()
    source = inspect.getsource(native.main)
    old = '                u.mem_write(BASE + delta + slot * 256, bytes(image))'
    assert source.count(old) == 1
    source = source.replace(old, '                image[0x84:0x87] = bytes([0xa5, 4, 17])\n' + old)
    old = "                assert actual[4 + extent:] == before[delta][slot * 256 + 4 + extent:(slot + 1) * 256]"
    assert source.count(old) == 1
    source = source.replace(old, '''                expected_record = bytearray(before[delta][slot * 256:(slot + 1) * 256])
                expected_record[4:4 + extent] = expected
                expected_record[0x84] = EXPECTED_SHADOW_MARKER if delta else 0
                assert actual == expected_record, (version, slot, delta, list(actual[0x84:0x87]))''')
    old = 'tail84_plus_preserved=True,'
    assert source.count(old) == 1
    source = source.replace(old, 'marker_invalidated=True, inactive_pair_preserved=True, tail87_plus_preserved=True,')
    old = '        cases.append(dict(format_index=version,'
    assert source.count(old) == 1
    source = source.replace(old, '''        call(0xbbc924, 1, task=True)
        markers_after_cancel = [bytes(u.mem_read(BASE + index * 256 + 0x84, 3))[0] for index in range(7)]
        assert markers_after_cancel == [EXPECTED_SHADOW_MARKER] * 7, markers_after_cancel
        cases.append(dict(native_bank_cancel_markers=markers_after_cancel, format_index=version,''')
    source = source.replace('new_wb_metadata_invalidation_implemented=False', 'new_wb_metadata_invalidation_implemented=True')
    source = source.replace('def main():', 'def execute():', 1)
    namespace = dict(vars(native), EXPECTED_SHADOW_MARKER=0xa5 if args.expect_stale_shadow else 0)
    before_argv = sys.argv
    sys.argv = [sys.argv[0], '--build', str(args.build), '--output', str(args.output)]
    try:
        exec(compile(source, str(original) + '::wb-marker-import-cancel', 'exec'), namespace)
        namespace['execute']()
    finally:
        sys.argv = before_argv
    report = json.loads(args.output.read_text())
    report.update(scope=__doc__, checker_sha256=native.sha(Path(__file__).read_bytes()),
        original_checker_sha256=native.sha(original.read_bytes()), adapted_checker_sha256=native.sha(source.encode()),
        expected_stale_shadow_control=args.expect_stale_shadow,
        primary_and_shadow_marker_coherent=not args.expect_stale_shadow,
        old_marker_reactivated_by_bank_cancel=args.expect_stale_shadow)
    if args.expect_stale_shadow:
        report['status'] = 'PASS: expected stale-shadow counterexample reproduced'
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
