"""Native date transitions and compatibility with the stock counter consumer.

Catalog/status/settings/calendar inputs are explicit lower boundaries. The
post-file-open counter consumer is exercised separately without executing or
substituting a successful file-open result. No capture or storage success.
Original AI-assisted native checker.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn.arm_const import *
from probe_date_folders_dual import run_case,ROOT,RAM,CONTEXT,B_CONTEXT
from build_modular_candidate import sha


def decode(m,enabled):
    u=m['u'];doc=json.dumps(dict(date_folders=enabled)).encode();u.mem_write(RAM+0x4000,doc)
    assert m['call'](m['word'](m['symbols']['save_data_settings']+8),RAM+0x4000,len(doc))==1


def requests(m,wanted):
    u=m['u'];call=m['call'];results=[]
    for index,drive in enumerate([0x41,0x41,0x42,0x42,0xffffffff,0xffffffff]):
        before=bytes(u.mem_read(0x10a8c00,6));out=RAM+0x5000
        status=call(0xcee2e0,drive,out,0,0);raw=bytes(u.mem_read(out,0xc4));name=raw.split(b'\0',1)[0].decode()
        assert status==0 and name.endswith(wanted[index//2]),(status,name,wanted)
        assert bytes(u.mem_read(0x10a8c00,6))==before
        results.append(dict(drive=drive,status=status,path=name,counter_bytes=before.hex()))
    return results


def main(build,output):
    output.mkdir(exist_ok=True);transitions=[]
    for name,options in [('no-create',{}),('catalog-dated',dict(asuffix='_1111',bsuffix='_1111'))]:
        prior,m,b=run_case(build,101,100,1001,1,enabled=True,return_machine=True,**options)
        decode(m,False)
        want=['101_FUJI\\DSCF1002','100_FUJI\\DSCF0002','101_FUJI\\DSCF1002'] if name=='no-create' else ['102_FUJI\\DSCF2001','101_FUJI\\DSCF1001','102_FUJI\\DSCF2001']
        off=requests(m,want)
        assert bytes(m['u'].mem_read(CONTEXT+0x216e,5))==bytes(m['u'].mem_read(B_CONTEXT+0x216e,5))==b'_FUJI'
        transitions.append(dict(case=name,off_requests=off,physical_create_completed=False))
    # Native catalog has yesterday's dated folders; the next calendar day
    # must request a different folder number, independently for each owner.
    prior,m,b=run_case(build,101,100,1001,1,enabled=True,return_machine=True,asuffix='_1111',bsuffix='_1111')
    m['u'].mem_write(0x1004b34,bytes((26,11,12,12,34,56)))
    rollover=requests(m,['102_1112\\DSCF2001','101_1112\\DSCF1001','102_1112\\DSCF2001'])
    # The ordinary native consumer parses an actual returned candidate and
    # publishes FRAME NO. Lower boundary starts after file-open; no handle or
    # successful API return is fabricated, and no filesystem call is executed.
    u=m['u'];call=m['call'];ex=m['execute_to'];out=RAM+0x5000
    before=bytes(u.mem_read(0x10a8c00,6)).hex()
    frame,fp,_=ex(0xced3e0,0xced440,0,out,1)
    ex(0xced458,0xced488,frame=frame)
    pair=list(struct.unpack('<3H',u.mem_read(0x10a8c00,6)))
    assert pair==[102,102,2001],pair
    assert bytes(u.mem_read(0x10cc074,5))==b'_1112'
    consumer=dict(before=before,after=pair,native_suffix=bytes(u.mem_read(0x10cc074,5)).decode(),
                  native_entry='0xced3e0',pre_open_stop='0xced440',post_open_lower_boundary='0xced458..0xced488',
                  successful_open_executed=False,capture_completed=False)
    report=dict(scope=__doc__,status='PASS',elf_sha256=sha((build/'mods.elf').read_bytes()),
        transitions=transitions,rollover=rollover,native_counter_consumer=consumer,
        hardware_verified=False,physical_storage=False,full_boot=False,checker_sha256=sha(Path(__file__).read_bytes()))
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',transition_requests=18,native_counter_consumer=pair)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.build,a.output)
