"""Reuse the native storage/settings suite with the qualified two-item SAVE menu.

Only the volume property's actual ID, option ID and native parent row count
change. All native open/close, preview/cancel/commit and deferral assertions
remain. The original suite/source and its earlier reports stay immutable.
"""
import inspect
import json
from pathlib import Path
import verify_full_storage_guard as original


def main():
    source=inspect.getsource(original.menu_owner_flow)
    for old,new in [('0x7f03','0x7f05'),('0x7f01','0x7f03'),('parent_node[4] == 9','parent_node[4] == 10')]:
        assert old in source;source=source.replace(old,new)
    namespace=dict(vars(original));exec(compile(source,str(Path(original.__file__))+'::dual-item-owner','exec'),namespace)
    def dual_owner(*args, **kwargs):
        namespace['BUILD']=original.BUILD
        return namespace['menu_owner_flow'](*args, **kwargs)
    original.menu_owner_flow=dual_owner
    original.main()
    report=dict(scope=__doc__,checker_sha256=original.sha(Path(__file__).read_bytes()),
        original_checker_sha256=original.sha(Path(original.__file__).read_bytes()),adapted_menu_owner_sha256=original.sha(source.encode()),
        elf_sha256=original.sha((original.BUILD/'mods.elf').read_bytes()),native_volume_property='0x7f03',native_volume_option='0x7f05',native_parent_rows=10)
    (original.OUT/'dual-menu-native-adapter.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
