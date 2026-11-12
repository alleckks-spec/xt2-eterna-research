"""Reuse native detail cases with the final lookup source and ninth Q caption.

Only source provenance and the selected Q row are adapted. All original
native dimensions, stock equality, message ABI and caption assertions remain.
"""
import argparse
import inspect
import json
from pathlib import Path
from build_modular_candidate import sha
from verify_final_variant_sdk import ELFS


def main(build, output, case):
    digest = sha((build / 'mods.elf').read_bytes())
    assert digest in ELFS
    if case == 'dimensions':
        import verify_controls_menu_dimensions as original
        source = inspect.getsource(original.main)
        assert source.count('full-controls-menu-inputs') == 2
        source = source.replace('full-controls-menu-inputs', 'controls-lookup-inputs')
    else:
        import verify_controls_menu_captions as original
        source = inspect.getsource(original.main)
        anchor = "'command_control_press']"
        assert source.count(anchor) == 1
        source = source.replace(anchor, "'command_control_press','quick_menu_button']")
    namespace = dict(vars(original))
    exec(compile(source, str(__file__) + '::existing-native-' + case, 'exec'), namespace)
    namespace['main'](build, output)
    path = output / 'verification.json'
    r = json.loads(path.read_text())
    assert r['status'] == 'PASS' and r['elf_sha256'] == digest
    r.update(final_detail_adapter_sha256=sha(Path(__file__).read_bytes()),
             final_detail_original_sha256=sha(Path(original.__file__).read_bytes()),
             final_detail_adapted_sha256=sha(source.encode()))
    path.write_text(json.dumps(r, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--case', choices=['dimensions', 'captions'], required=True)
    a = p.parse_args()
    main(a.build, a.output, a.case)
