"""Rerun the unchanged formatter/codec/memory checks on the larger menu ELF.

The old formatter verifier predates this menu consumer. Keep its numeric,
buffer, native calendar/BSS/heap and entry-ABI checks; only adapt artifact word
count and replace its old absent-menu assertion with the linked consumer.
No old result is copied to the new artifact. AI-assisted parameter adapter.
"""
import argparse
import inspect
from pathlib import Path
import verify_volume_name_candidate as volume

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'save-data-menu-native-build-unverified')
    parser.add_argument('--output',type=Path,default=ROOT/'save-data-menu-dependencies-unverified')
    args=parser.parse_args()
    source=inspect.getsource(volume.verify)
    changes={
        '    verify_card(build,68)':'    verify_card(build,72)',
        "    assert 'xpp_menu_entries_boot' not in symbols":"    assert 'xt2_save_menu_text' in symbols",
        'general_mod_menu_engine_present=False':'general_mod_menu_engine_present=True',
    }
    for before,after in changes.items():
        assert source.count(before)==1,before
        source=source.replace(before,after)
    namespace=dict(vars(volume));namespace['__file__']=__file__
    namespace['__doc__']=__doc__+'\n'+volume.__doc__.replace('general mod menu, ','')
    exec(compile(source,str(Path(volume.__file__))+':menu-artifact','exec'),namespace)
    namespace['verify'](args.build,args.output)


if __name__=='__main__':main()
