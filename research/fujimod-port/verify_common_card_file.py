"""AI-assisted supplied file -> common publisher/UI -> real native still chain.

No filesystem model is expanded: reuse its three lower data/metadata hooks,
post-FAT directory frame and retained native worker loops. The actual common
ELF and already initialized native UI context replace the isolated component.
"""
import argparse,inspect,json,struct,hashlib
from pathlib import Path
from types import SimpleNamespace
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
import verify_film_loader_file_boundary as filecheck
from verify_cardio_native_worker import Assay
from verify_card_processing import make_machine,BUILD,RAM
import verify_card_still_native as still

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'common-card-file-check-unverified'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--invalid-json',action='store_true');parser.add_argument('--read-error',type=int,default=0);args=parser.parse_args()
    pins=json.loads((ROOT/'film-loader-check-unverified/file-boundary-freeze.json').read_text())['files']
    original=Path(filecheck.__file__).resolve();assert hashlib.sha256(original.read_bytes()).hexdigest()==pins[str(original)]
    (u,symbols,call,api,clock,init,exceptions),setup=make_machine()
    m=Assay.__new__(Assay);m.u=u;m.symbols=symbols;m.clock=clock
    m.call=lambda entry,*args:call(entry,*args,task=False)
    m.semaphore_results=[]
    descriptors=[]
    def take():
        descriptor,payload=RAM+0x6000,RAM+0x6100
        u.mem_write(descriptor,struct.pack('<3I',0,0,payload))
        assert m.call(0xcefb60,120,descriptor,0)==0
        code,source,destination,size=struct.unpack('<HBBI',u.mem_read(descriptor,8))
        current_task=m.call(0xceed8c)
        assert source==current_task==1 and destination==120 and size in (8,60),(code,source,destination,size,current_task)
        descriptors.append(dict(code=code,source=source,destination=destination,size=size))
        return descriptor,payload,code
    m.take=take
    u.hook_add(UC_HOOK_CODE,lambda uc,a,z,d:m.semaphore_results.append(uc.reg_read(UC_ARM_REG_R0)),begin=0x969ff4,end=0x969ff4)
    for entry in [0xcec598,0xcec634,0xcdf570]:assert m.call(entry)==0
    for n,v in dict(ui_mode=3,ui_capture_state=0,ui_capture_block=0,raw_backup_flag=0,menu_open=0).items():u.mem_write(symbols[n],bytes([v]))
    source=inspect.getsource(filecheck.main)
    start='    assert not(a.invalid_json and a.read_error)\n';end='    report=dict(scope=__doc__'
    assert source.count(start)==source.count(end)==1
    body=source[source.index(start):source.index(end)]
    old_doc="    doc=b'{\"name\":' if a.invalid_json else json.dumps(dict(name='Port file',base='provia',icon='custom')).encode()"
    assert body.count(old_doc)==1
    body=body.replace(old_doc,'    doc=SUPPLIED_DOCUMENT')

    old="    assert m.word(m.symbols['film_card_count'])==0"
    assert body.count(old)==1
    body=body.replace(old,"    assert m.word(m.symbols['film_card_count'])==int(not rejected)")
    # Original assertion above describes a disabled isolated publisher. The
    # common artifact includes the enabled existing publisher; no byte is set.
    old_ready="    assert m.api('film_loader_ready')==1 and m.api('film_loader_idle')==1\n"
    assert body.count(old_ready)==1
    assert 'film_loader_ready' not in symbols and 'film_loader_idle' not in symbols
    body=body.replace(old_ready,'')  # dead-stripped unused getters, no surrogate
    old_live="    assert m.api('x70_lifetime_live')==2 and m.word(m.symbols['callbacks'])==0\n"
    assert body.count(old_live)==1 and 'x70_lifetime_live' not in symbols
    body=body.replace(old_live,"    assert m.word(m.symbols['live'])==2 and m.word(m.symbols['callbacks'])==0\n")
    code='def execute():\n'+body+'    return dict(loader=state(),callbacks=callbacks,workers=runs,resources=resources,lower_boundary_calls=fs.trace,card_count=m.word(m.symbols[\'film_card_count\']))\n'
    doc=dict(name='Port file',base='provia',icon='custom',matrix=[900,10,20,30,1100,40,50,60,1200],
             chroma=[1100,900,50,-30],luma=dict(bounds=[40,80,160,220],shift=[10,20,30,40,50],gain=[260,270,280,290,300]),
             tone_curve=dict(combined=dict(widths=[2,2,3,4,5,5,5,6,6],points=[round(16383*i/27) for i in range(28)])))
    supplied=b'{"name":' if args.invalid_json else json.dumps(doc).encode()
    namespace=dict(vars(filecheck));namespace.update(m=m,a=SimpleNamespace(invalid_json=args.invalid_json,read_error=args.read_error),SUPPLIED_DOCUMENT=supplied)
    exec(compile(code,str(Path(filecheck.__file__))+'::common-prefix','exec'),namespace)
    report=namespace['execute']();report.update(scope=__doc__,setup=setup,descriptors=descriptors,elf_sha256=hashlib.sha256((BUILD/'mods.elf').read_bytes()).hexdigest(),hardware_verified=False)
    rejected=bool(args.invalid_json or args.read_error)
    if not rejected:
        event=RAM+0x500;u.mem_write(event,bytes(80));assert call(0x14da7ac,event,task=True)==1
        assert m.word(symbols['film_card_shown'])==1
        # Borrow only the frozen still checker's setup/observations/helpers;
        # retain this loaded machine, catalog and real published recipe.
        still_pins=json.loads((ROOT/'card-still-native-check-unverified/freeze.json').read_text())['files']
        still_path=Path(still.__file__).resolve();assert hashlib.sha256(still_path.read_bytes()).hexdigest()==still_pins[str(still_path)]
        source=inspect.getsource(still.main);anchor='    stock=assemble(0);';assert source.count(anchor)==1
        prefix=source.split(anchor)[0]
        old_machine='(u,symbols,call,api,clock,init,exceptions),setup=processing.make_machine()'
        assert prefix.count(old_machine)==1
        prefix=prefix.replace(old_machine,'(u,symbols,call,api,clock,init,exceptions),setup=SUPPLIED_MACHINE').replace('def main():','def helpers():',1)
        prefix+='    return assemble,entries\n'
        context=dict(vars(still));context['SUPPLIED_MACHINE']=((u,symbols,call,api,clock,init,exceptions),setup)
        exec(compile(prefix,str(still_path)+'::loaded-machine-prefix','exec'),context)
        assemble,entries=context['helpers']();stock=assemble(0);actual=assemble(38);groups=actual['groups']
        assert actual['native_slot']==0 and actual['tag']==[7,0x58,0x54]
        assert groups['matrix']==[doc['matrix']] and groups['curve']==[doc['tone_curve']['combined']['points']]
        assert groups['chroma']==[[doc['chroma'][i] for i in [0,2,3,1]]]
        pairs=[]
        for shift,gain in zip(doc['luma']['shift'],doc['luma']['gain']):pairs += [shift&0xffff,gain]
        assert groups['luma']==[dict(enabled=1,bounds=doc['luma']['bounds'],pairs=pairs)]
        assert actual['groups']!=stock['groups'] and len(entries)==2
        report['native_still']=dict(stock=stock,card=actual,body_entries=entries,stock_trampoline_surrogates=0)
        report['native_ui_row_shown']=True
    else:assert m.word(symbols['film_card_count'])==m.word(symbols['film_card_shown'])==0
    report.update(status='PASS',invalid_json=args.invalid_json,supplied_read_error=args.read_error,
                  live_timer_holds=m.word(symbols['live']),outstanding_callbacks=m.word(symbols['callbacks']),
                  initialized_fs_context_fixture=True,post_fat_directory_frame=True,lower_filesystem_hooks=3,kernel_api_stubs=0,
                  mounted_fat=False,full_startup=False,physical_capture=False,
                  supplied_file_sha256=hashlib.sha256(supplied.ljust(3008,b' ')).hexdigest(),
                  input_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [
                      original,Path(still.__file__).resolve(),ROOT/'verify_card_processing.py',ROOT/'verify_cardio_native_worker.py',
                      ROOT.parents[1]/'scripts/xt2_native_profile_fs_fixture.py']},
                  original_file_checker_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),adapted_file_prefix_sha256=hashlib.sha256(code.encode()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    OUT.mkdir(exist_ok=True);name='invalid-json' if args.invalid_json else ('read-error' if args.read_error else 'valid')
    (OUT/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('Common file -> publisher -> UI -> native still PASS',name,report['card_count'])

if __name__=='__main__':main()
