"""Execute native _sbrk at the resized target's heap ceiling.

AI-assisted bounded check. Supplied cursor/errno and scratch stack, not heap
high-water, all allocators, wraparound arithmetic or camera workload evidence.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['stock','target','output']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();stock=a.stock.read_bytes();target=json.loads(a.target.read_text())
    assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    ceiling=int(target['card_regions'][0]['address'],0);assert ceiling==0x1388000
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,(len(stock)+4095)&~4095);u.mem_write(0,stock)
    u.mem_map(0x8000000,0x10000);ret=0x800f000;errno=0x8004000
    def call(current,increment):
        u.mem_write(0xfae334,struct.pack('<I',current));u.mem_write(errno,b'\x5a'*4)
        u.reg_write(UC_ARM_REG_R0,errno);u.reg_write(UC_ARM_REG_R1,increment&0xffffffff)
        u.reg_write(UC_ARM_REG_SP,0x800e000);u.reg_write(UC_ARM_REG_LR,ret)
        u.emu_start(0xcf45a8,ret,count=10000)
        assert u.reg_read(UC_ARM_REG_PC)==ret and u.reg_read(UC_ARM_REG_SP)==0x800e000
        return [u.reg_read(UC_ARM_REG_R0),struct.unpack('<I',u.mem_read(0xfae334,4))[0],
                struct.unpack('<I',u.mem_read(errno,4))[0]]
    original=call(ceiling-64,33);assert original==[ceiling-64,ceiling-31,0x5a5a5a5a]
    for word in target['card_words']:
        address=word['address'];assert struct.unpack('<I',u.mem_read(address,4))[0]==word['old']
        u.mem_write(address,struct.pack('<I',word['new']))
    u.ctl_remove_cache(0xcf45a8,0xcf45fc)
    rows=[];start=0x12532fc
    for current,increment in [(start,0),(start,4096),(ceiling-64,32),(ceiling-64,33),
                              (ceiling-32,0),(ceiling-32,1),(ceiling-32,4096),
                              (ceiling-64,16),(ceiling-64,-16)]:
        result=call(current,increment);allowed=current+increment+32<=ceiling
        expected=[current,current+increment,0x5a5a5a5a] if allowed else [0xffffffff,current,12]
        assert result==expected,(current,increment,result,expected)
        assert result[1]<=ceiling-32
        rows.append(dict(cursor=current,increment=increment,result=result,allowed=allowed))
    report=dict(scope=__doc__,status='PASS',ceiling=ceiling,capacity=ceiling-start,
        original_crossing_control=original,cases=rows,hardware_verified=False,
        dependencies={str(path):sha(path.read_bytes()) for path in [Path(__file__),a.stock,a.target]})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',cases=len(rows),capacity=ceiling-start)))


if __name__=='__main__':main()
