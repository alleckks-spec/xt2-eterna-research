"""Execute the native RAF metadata aspect writer and its actual copy boundary.

Existing SDK CPU/kernel/clock setup; official calibration data and camera-info
aspect enum are explicit function inputs. Native cache-pointer publication,
metadata body and both aspect copies execute. Stop before later RAF fields;
no RAF file, persistent write, mod hook or hardware capture is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import probe_sdk_native_encoder_descriptor as descriptor
import probe_sdk_native_encoder_init as setup

ROOT=Path(__file__).resolve().parent


def main(aspect):
    out=ROOT/('sdk-native-raf-aspect-'+str(aspect)+'-unverified')
    source=setup.prepare_source()
    source=source.replace('    def execute_smp_call(entry,*args):','    def execute_smp_call(entry,*args,stop=RETURN):')
    source=source.replace('points={core:{RETURN,','points={core:{RETURN,stop,')
    source=source.replace('            if pc==RETURN:\n',"            if pc==RETURN and stop!=RETURN:\n                raise AssertionError(dict(early_return=hex(entry),wanted=hex(stop)))\n            if pc==stop:\n")
    source=source.replace("                assert observed.reg_read('Sp')==RAM+0xe000","                if stop==RETURN:assert observed.reg_read('Sp')==RAM+0xe000")
    begin=source.index('        initialized=execute_smp_call(0x15b2108)')
    end=source.index('    except Exception as exc:\n',begin)
    source=source[:begin]+'''        calibration=(WORKSPACE/'firmware/extracted/xt2-4.41/inverted.bin').read_bytes()[0xc025c:0x10025c]
        cpu.mem_write(0x2c68000,calibration)
        execute_smp_call(0xce3978,stop=0xce3998)
        assert word(0x1025344)==0x2c68000
        camera,record,info,copy,extra=RAM+0x4000,RAM+0x6000,RAM+0x7000,RAM+0x7100,RAM+0x7200
        cpu.mem_write(camera,bytes(0x1000));cpu.mem_write(camera+0x45e,bytes([ASPECT]))
        cpu.mem_write(record,bytes(0x400));cpu.mem_write(info-16,b'\\xa5'*16+bytes(128)+b'\\x5a'*16)
        cpu.mem_write(copy-16,b'\\xa5'*16+bytes(128)+b'\\x5a'*16);cpu.mem_write(extra,bytes(256))
        execute_smp_call(0x16dc9f0,camera,record,info,copy,extra,0,stop=0x16dcdf0)
        expected=[(3,4),(2,3),(9,16),(1,1)][ASPECT]
        pair=struct.unpack('<2H',cpu.mem_read(info+0x14,4));copied=struct.unpack('<2H',cpu.mem_read(copy+0x14,4))
        assert pair==copied==expected
        assert cpu.mem_read(info-16,16)==cpu.mem_read(copy-16,16)==b'\\xa5'*16
        assert cpu.mem_read(info+128,16)==cpu.mem_read(copy+128,16)==b'\\x5a'*16
        stages.append(dict(native_raf_aspect=ASPECT,entry=hex(0x16dc9f0),stop=hex(0x16dcdf0),
            native_info=hex(info),native_copy=hex(copy),offsets=[0x14,0x16],pair=list(pair),copied=list(copied),
            native_cache_pointer_prefix=True,calibration_sha256=hashlib.sha256(calibration).hexdigest(),
            canaries_intact=True,metadata_complete=False,raf_file_written=False))
'''+source[end:]
    namespace=dict(vars(setup.native),OUT=out,ASPECT=aspect)
    exec(compile(source,str(Path(setup.native.__file__))+'::native-RAF-aspect-prefix','exec'),namespace)
    try:
        namespace['main']()
    finally:
        path=out/'probe.json';report=json.loads(path.read_text())
        report.update(scope=__doc__,aspect_fixture=aspect,
            adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            setup_sha256=hashlib.sha256(Path(setup.__file__).read_bytes()).hexdigest(),
            adapted_body_sha256=hashlib.sha256(source.encode()).hexdigest())
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(error=report['error'][:500] if report['error'] else None,last=report['stages'][-1])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--aspect',type=int,choices=[0,1,2,3],required=True)
    main(p.parse_args().aspect)
