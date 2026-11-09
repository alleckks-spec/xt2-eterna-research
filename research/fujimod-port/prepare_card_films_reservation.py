"""Resize the existing X-T2 reservation from an observed ordinary link footprint.

AI-assisted original target-layout glue. Keep the upper BSS/stack boundary and
existing shim/mapping mechanism; reserve only the required32KiB-rounded heap
suffix. Outputs contain private instruction manifests and stay local. Native
prefix validation reuses the existing harness, without new device replies.
"""
import argparse
import copy
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[1]
OUT=ROOT/'card-films-reservation-unverified'


def sha(data):return hashlib.sha256(data).hexdigest()


def mov16(base,value):return base|((value&0xf000)<<4)|(value&0xfff)


def prepare():
    target_path=ROOT/'timer-build-unverified/target.json'
    frozen=ROOT/'continuation-resident-reservation-20261109/resident-reservation-unverified'
    map_path=ROOT/'card-films-build-unverified/failed-mods.map'
    target=json.loads(target_path.read_text());old=copy.deepcopy(target)
    proposal=json.loads((frozen/'proposal.json').read_text())
    code=bytearray((frozen/'reservation.bin').read_bytes());assert sha(code)==proposal['shim']['sha256']
    text=map_path.read_text();matches=re.findall(r'(0x[0-9a-f]+)\s+__x70mod_region_end =',text)
    assert len(matches)==1;end_of_module=int(matches[0],16)
    region,=target['card_regions'];old_start=int(region['address'],0);end=old_start+int(region['size'],0)
    assert (old_start,end)==(0x1390000,0x13c0000)
    footprint=end_of_module-old_start;size=(footprint+0x7fff)&~0x7fff;start=end-size
    assert footprint==225252 and size==229376 and start==0x1388000
    assert proposal['heap']['start']<start<old_start<end
    bss_start=proposal['bss']['start'];shim=proposal['shim']['address']
    updates={0xcf45c4:mov16(0xe3003000,start&0xffff),0xcf45c8:mov16(0xe3403000,start>>16),
             0xcf8200:mov16(0xe3000000,start&0xffff),0xcf8204:mov16(0xe3400000,start>>16),
             shim+28:(start-bss_start)//4}
    words={w['address']:w for w in target['card_words']}
    assert struct.unpack_from('<I',code,28)[0]==(old_start-bss_start)//4
    for i,value in enumerate(struct.unpack('<10I',code)):assert words[shim+4*i]['new']==value
    for address,value in updates.items():words[address]['new']=value
    struct.pack_into('<I',code,28,updates[shim+28])
    region.update(address=hex(start),size=hex(size),
        status='Expanded existing reservation for observed33-source footprint; native prefix checks required, no camera qualification.')
    changed=[w['address'] for w,o in zip(target['card_words'],old['card_words']) if w['new']!=o['new']]
    assert set(changed)==set(updates)
    for edit in proposal['edits']:
        if edit['address'] in updates:edit['new']=updates[edit['address']]
    proposal['region'].update(start=start,end=end,bytes=size,current_loaded_bytes=footprint,remaining_before_stack=size-footprint)
    proposal['heap'].update(new_end=start,new_capacity=start-proposal['heap']['start'])
    proposal['bss']['prefix_bytes']=start-bss_start
    proposal['shim']['sha256']=sha(code)
    stock_path=WORKSPACE/'firmware/research/xt2-stock-sd-unverified/ffboot.bin'
    stock=stock_path.read_bytes();assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    inputs=[Path(__file__),target_path,map_path,frozen/'proposal.json',frozen/'reservation.bin',stock_path]
    proposal['inputs']={str(p.resolve()):sha(p.read_bytes()) for p in inputs}
    proposal['status']='Existing reservation expanded down32KiB; native prefix not yet qualified'
    OUT.mkdir(exist_ok=True);(OUT/'reservation.bin').write_bytes(code)
    (OUT/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    (OUT/'target.json').write_text(json.dumps(target,indent=2)+'\n')
    report=dict(scope=__doc__,old_start=old_start,start=start,end=end,footprint=footprint,
        reserved_bytes=size,headroom=size-footprint,extra_heap_bytes=old_start-start,
        changed_target_words=changed,heap_capacity=proposal['heap']['new_capacity'],
        native_checks=False,hardware_verified=False)
    (OUT/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True);return bytes(code),proposal


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-prefix',action='store_true');a=p.parse_args()
    code,proposal=prepare()
    if a.native_prefix:
        import probe_reservation_native_prefix as probe
        probe.START=proposal['region']['start'];probe.END=proposal['region']['end']
        probe.SHIM=proposal['shim']['address'];probe.RESERVATION_OUT=OUT
        probe.build=lambda:(code,proposal)
        probe.main()


if __name__=='__main__':main()
