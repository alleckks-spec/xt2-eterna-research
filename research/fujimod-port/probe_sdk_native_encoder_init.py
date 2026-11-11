"""Qualify native encoder initialization on the existing two-core SDK board.

Reuse the frozen native settings probe's CPU/kernel/SD setup; add the existing
SDK XPP JPEG node with independently checked native register/IRQ bindings.
This bounded stage executes encoder initialization only. No capture, crop,
successful encoded image, new device model or camera result is claimed.
"""
import hashlib
import inspect
import json
from pathlib import Path
import probe_sdk_native_fs_settings_commit as native
from firmware_analysis import Firmware

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sdk-native-encoder-power-init-unverified'


def prepare_source():
    f=Firmware('xt2-4.41',True)
    assert f.word(0xefd560+12*0x3c)==134
    assert f.listing(0x15b21f0,0x15b21fc)==[
        '015b21f0: mov r4, r0','015b21f4: mov r0, #0x3c','015b21f8: bl #0xc66ed8']
    source=inspect.getsource(native.main)
    anchor="    nodes = [dict(name='gpio', model=dict(kind='gpio', base=0xfff0c000, inputs=inputs)),"
    assert source.count(anchor)==1
    source=source.replace(anchor,"    nodes = [dict(name='jpeg',model=dict(kind='jpeg',base=0xfffc8000,irq=134,run_ticks=100)),\n             dict(name='power',model=dict(kind='power',base=0xfff10000)),\n"+anchor.replace('    nodes = [','             '))
    start=source.index('        import io\n')
    end=source.index('    except Exception as exc:\n',start)
    source=source[:start]+'''        clock_result=execute_smp_call(0xc560ac)
        stages.append(dict(native_clock_owner_init=hex(0xc560ac),return_value=hex(clock_result),
            native_owner_marker=hex(word(0x1000164))))
        assert word(0x1000164)==0x22233344
        initialized=execute_smp_call(0x15b2108)
        stages.append(dict(native_encoder_init=hex(0x15b2108),result=initialized,
            jpeg_devices=[d for d in board.state()['bus']['devices'] if d['kind']=='xpp-jpeg-encoder'],
            irq_binding=word(0xefd560+12*0x3c)))
        assert initialized==0
'''+source[end:]
    returns=[]
    for ins in f.dis.disasm(f.read(0xc739a0,0xc741d8-0xc739a0),0xc739a0):
        if ins.mnemonic=='bl':returns.append(ins.address+4)
    points=[0x15b211c,0x15b2134,0x15b2140,0x15b2150,0x15b2124,0x15b2170,*returns]
    anchor='points={core:{RETURN,'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+','.join(hex(p) for p in points)+',')
    anchor='            if pc==RETURN:\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,"            if pc in (0x15b2124,0x15b2170):\n                raise AssertionError(dict(native_encoder_refusal=hex(pc),status=hex(r0)))\n"+anchor)
    return source


def main():
    source=prepare_source()
    namespace=dict(vars(native),OUT=OUT)
    exec(compile(source,str(Path(native.__file__))+'::native-encoder-init','exec'),namespace)
    try:
        namespace['main']()
    finally:
        path=OUT/'probe.json';report=json.loads(path.read_text())
        report.update(scope=__doc__,reused_probe_sha256=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
            adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            adapted_body_sha256=hashlib.sha256(source.encode()).hexdigest(),
            successful_encoded_image=False,crop_mod_installed=False)
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(error=report['error'][:500] if report['error'] else None,last=report['stages'][-1])))


if __name__=='__main__':main()
