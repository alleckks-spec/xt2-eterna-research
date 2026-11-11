"""Reuse the qualified native SAVE DATA checker for the A/B date variant.

The original eight stock rows and resource/cursor comparisons remain active.
Date ON is supplied through the actual settings decoder. This checks internal
native packets and commit/cancel ownership, not physical keys or storage.
Original AI-assisted checker adapter; generated source stays in memory.
"""
import argparse
import json
from pathlib import Path
from build_modular_candidate import ROOT,sha
import verify_save_data_menu_candidate as original


def run(build,output,item):
    text=Path(original.__file__).read_text()
    def replace(old,new):
        nonlocal text
        assert old in text,old
        text=text.replace(old,new)
    replace("word(rows+72)==0x7ffffffe", "word(rows+72)==0x7f11 and word(rows+80)==0x7ffffffe")
    replace("state()[6]==9", "state()[6]==10")
    replace("new_rows=1", "new_rows=2")
    if item=='date':
        replace("'save_data_date_card_name'", "'save_data_date_folders'")
        replace("'FORMAT CARD NAME'", "'DATE FOLDERS'")
        replace("{'date_card_name':False}", "{}")
    else:
        # The date row precedes the existing volume item in the same engine.
        replace('0x7f03','0x7f05')
        replace('0x7f01','0x7f03')
        replace('0x7f10','0x7f11')
        replace('word(rows+64)==0x7f11 and word(rows+68)==option',
                'word(rows+72)==0x7f11 and word(rows+76)==option')
        replace("word(rows+72)==0x7f11 and word(rows+80)==0x7ffffffe", "word(rows+64)==0x7f10 and word(rows+80)==0x7ffffffe")
        replace("s['setup_save_table'],8)", "s['setup_save_table'],9)")
        replace("[(0x49,8,2,", "[(0x49,9,2,")
    namespace=dict(__name__='date_menu_reuse',__file__=str(Path(__file__)))
    exec(compile(text,str(Path(original.__file__)), 'exec'),namespace)
    machine=namespace['machine']
    def with_settings(*args,**kwargs):
        u,s,call,loaded=machine(*args,**kwargs)
        if item=='date':
            document=b'{"date_folders":true}'
            u.mem_write(0x8006000,document)
            owner=int.from_bytes(u.mem_read(s['save_data_settings']+8,4),'little')
            assert call(owner,0x8006000,len(document))==1
        return u,s,call,loaded
    namespace['machine']=with_settings
    namespace['main'](Path(build),Path(output)/item,76)
    report_path=Path(output)/item/'verification.json'
    report=json.loads(report_path.read_text())
    report.update(reused_checker_sha256=sha(Path(original.__file__).read_bytes()),
                  adapter_sha256=sha(Path(__file__).read_bytes()),item=item,
                  native_save_data_rows=10,initial_date_on_loaded_through_decoder=item=='date')
    report_path.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=True)
    for item in ['date','volume']:run(a.build,a.output,item)
