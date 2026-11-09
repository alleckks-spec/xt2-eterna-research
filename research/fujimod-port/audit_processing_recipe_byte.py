"""Reject context+0x54 as a recipe-ID byte using positive native owners.

Four bounded X-T2 4.41 processing accesses, not an inventory of every field or
an assertion that some other byte is free. No firmware edits. AI-assisted.
"""
import json
import sys
from pathlib import Path
from capstone.arm import ARM_OP_MEM, ARM_REG_R0, ARM_REG_R4, ARM_REG_R5
from build_fixture import ROOT, WORKSPACE, Firmware, sha

OWNERS=[('profile_constructor',0x157a140,ARM_REG_R0,True),
        ('chroma_selector',0x156acec,ARM_REG_R4,False),
        ('luma_builder',0x156b7f4,ARM_REG_R0,False),
        ('matrix_builder',0x156fb3c,ARM_REG_R5,False)]


def main():
    f=Firmware('xt2-4.41');f.dis.detail=True
    rows=[]
    for role,address,base,writes in OWNERS:
        data=f.read(address,4);instruction,=f.dis.disasm(data,address)
        memory=[op.mem for op in instruction.operands if op.type==ARM_OP_MEM]
        assert len(memory)==1 and memory[0].base==base and memory[0].disp==0x54,role
        assert instruction.mnemonic.startswith('str' if writes else 'ldr'),role
        rows.append(dict(role=role,pc=address,displacement=0x54,writes=writes,
                         base_register=f.dis.reg_name(base),instruction_sha256=sha(data)))
    report=dict(scope=__doc__,field=0x54,stock_owned=True,recipe_storage_rejected=True,
        positive_owners=rows,hardware=False,source_sha256=sha(Path(__file__).read_bytes()),
        manifest_sha256=sha((WORKSPACE/'firmware/extracted/xt2-4.41/manifest.json').read_bytes()))
    out=ROOT/'six-films-check-unverified';out.mkdir(exist_ok=True)
    (out/'recipe-byte-rejection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Context+54 rejected: constructor write and three original processing reads; no bytes assigned.')


if __name__=='__main__':main()
