"""Run existing six-owner native settings/fault assays on either final ELF.

Only the variant-selection assertion changes for the USB configuration. The
native case engines, owner checks, inputs, instruction bounds and callbacks
remain unchanged. No camera or physical USB operation is performed.
"""
import argparse
import inspect
import json
import sys
from pathlib import Path

from build_modular_candidate import ROOT, sha

ELFS = {
    '2b0eb7506be88d6eafdf17dafb1e2abced2981187e79b30d5c794fcd332d3619': False,
    '6ae0688d90ef10b8c727da96af4469f927ba56bf2aed3a4f650abb884c3860b9': True,
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--case', choices=['commit', 'restore', 'issue', 'capacity'], required=True)
    p.add_argument('--settings-readback', type=Path)
    a = p.parse_args()
    digest = sha((a.build / 'mods.elf').read_bytes())
    receipt = json.loads((a.build / 'preparation.json').read_text())
    assert digest in ELFS and receipt['elf_sha256'] == digest
    assert receipt['usb_debug_selected'] == ELFS[digest]
    assert not (a.output / 'probe.json').exists()
    import verify_common_controls_sdk_settings as settings
    import verify_common_controls_sdk_cardio as cardio
    import verify_common_q_sdk_settings as qsettings
    base = settings if a.case in ['commit', 'restore'] else cardio
    original_getsource = inspect.getsource
    source = original_getsource(base.main)
    anchor = "not receipt['usb_debug_selected']"
    assert source.count(anchor) == 1
    source = source.replace(anchor, "receipt['usb_debug_selected'] == " + repr(ELFS[digest]))

    def getsource(obj):
        return source if obj is base.main else original_getsource(obj)

    before = sys.argv
    sys.argv = [before[0], '--build', str(a.build), '--output', str(a.output), '--case', a.case]
    if a.settings_readback:
        sys.argv += ['--settings-readback', str(a.settings_readback)]
    inspect.getsource = getsource
    try:
        if base is settings:
            qsettings.main()
        else:
            namespace = dict(vars(cardio))
            exec(compile(source, str(__file__) + '::final-six-owner-cardio', 'exec'), namespace)
            namespace['main']()
    finally:
        inspect.getsource = original_getsource
        sys.argv = before
        path = a.output / 'probe.json'
        if path.exists():
            report = json.loads(path.read_text())
            report.update(final_variant_adapter_sha256=sha(Path(__file__).read_bytes()),
                          final_variant_adapted_source_sha256=sha(source.encode()),
                          final_variant_original_sha256=sha(Path(base.__file__).read_bytes()),
                          final_variant_usb=ELFS[digest], final_variant_case=a.case)
            path.write_text(json.dumps(report, indent=2) + '\n')
            assert report['elf_sha256'] == digest and report['error'] is None


if __name__ == '__main__':
    main()
