"""Native X-T2 producer through the actual encoder-program descriptor boundary.

Reuse existing native SDK CPU/kernel/clock/domain prerequisites and existing
JPEG node. Camera geometry and the worker ownership header are declared inputs.
Request fields and the program descriptor are produced by native code. Stop
before programming/encoding; no crop, pixels, encoded result or camera claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import probe_sdk_native_encoder_init as setup

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sdk-native-encoder-descriptor-unverified'


def main(kind=0,output=None):
    out=Path(output) if output else ROOT/('sdk-native-encoder-descriptor-kind'+str(kind)+'-unverified')
    source=setup.prepare_source()
    anchor='    def execute_smp_call(entry,*args):'
    assert source.count(anchor)==1
    source=source.replace(anchor,'    def execute_smp_call(entry,*args,stop=RETURN):')
    source=source.replace('points={core:{RETURN,','points={core:{RETURN,stop,')
    anchor='            if pc==RETURN:\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,"            if pc==RETURN and stop!=RETURN:\n                raise AssertionError(dict(early_native_return=hex(entry),wanted=hex(stop),status=hex(r0)))\n            if pc==stop:\n")
    source=source.replace("                assert observed.reg_read('Sp')==RAM+0xe000","                if stop==RETURN:assert observed.reg_read('Sp')==RAM+0xe000")
    begin=source.index('        initialized=execute_smp_call(0x15b2108)')
    end=source.index('    except Exception as exc:\n',begin)
    source=source[:begin]+'''        # Same geometry boundary as the existing native JPEG producer assay.
        cpu.mem_write(0x24825e8+0x2c,struct.pack('<I',RAM+0x4000))
        cpu.mem_write(RAM+0x4000+0x58c,struct.pack('<3H',6000,4000,6000))
        execute_smp_call(0x2a79c14,stop=0x2a759a0)
        state=word(0x24825e8+8)
        assert state==0x22f5a20
        requests=[]
        for kind,offset in [(0,0x150),(1,0x54),(2,0x25c)]:
            p=state+offset
            assert word(p+4)==10 and word(p+8)==0 and word(p+12)==kind
            requests.append(dict(kind=kind,pointer=hex(p),width=word(p+0xac),height=word(p+0xb0)))
        stages.append(dict(native_requests=requests,geometry_fixture=[6000,4000,6000],request_fields_supplied=False))
        control,job=RAM+0x6000,RAM+0x6100
        cpu.mem_write(control,bytes(0x80));cpu.mem_write(job,bytes(0x80))
        cpu.mem_write(control+0x14,struct.pack('<I',job))
        cpu.mem_write(job+0x20,struct.pack('<I',state+0x150))
        execute_smp_call(0x2a233e0,control,stop=0x15b2244)
        current=board.cpus[active_core]
        pointer=current.reg_read({'Arm32':{'R':0}})
        fields=list(struct.unpack('<7I',current.mem_read(pointer,28)))
        stages.append(dict(native_encoder_descriptor=hex(pointer),program_entry=hex(0x15b2244),
            pitch=fields[0],x=fields[1],y=fields[2],width=fields[3],height=fields[4],
            source=hex(fields[5]),destination=hex(fields[6]),
            worker_header_supplied=True,descriptor_fields_supplied=False,
            stopped_before_program=True))
'''+source[end:]
    source=source.replace('state+0x150',f'state+{[0x150,0x54,0x25c][kind]:#x}')
    namespace=dict(vars(setup.native),OUT=out)
    exec(compile(source,str(Path(setup.native.__file__))+'::native-encoder-descriptor','exec'),namespace)
    try:
        namespace['main']()
    finally:
        path=out/'probe.json';report=json.loads(path.read_text())
        report.update(scope=__doc__,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            setup_sha256=hashlib.sha256(Path(setup.__file__).read_bytes()).hexdigest(),
            adapted_body_sha256=hashlib.sha256(source.encode()).hexdigest(),request_kind=kind,encoded_result=False)
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(error=report['error'][:500] if report['error'] else None,last=report['stages'][-1])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',type=int,choices=[0,1,2],default=0)
    p.add_argument('--output',type=Path)
    args=p.parse_args();main(args.kind,args.output)
