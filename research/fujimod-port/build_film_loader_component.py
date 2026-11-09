"""Build the supplied upstream loader/parser/publisher with the X-T2 adapters.

AI-assisted original build glue. This is a bounded component at a synthetic
address, not an SD candidate. Menu row and immutable recipe imports refer to
the supplied common ELF, which must also be loaded by a checker. Card rows and
mutable processing ownership are not admitted by this build.
"""
import argparse
import hashlib
import io
import json
import shlex
import subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
from prepare_cardio_status import prepare as prepare_cardio
from prepare_timer_restart import prepare as prepare_timer
from prepare_film_parser import prepare as prepare_parser


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',required=True,type=Path)
    p.add_argument('--common',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--clang',default='clang')
    p.add_argument('--linker',required=True)
    a=p.parse_args();root=a.source_root.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True);(out/'build.json').unlink(missing_ok=True)
    common=a.common.read_bytes()
    assert sha(common)=='06ab09771172acde5d7e330066ad4f8679083a751767f80701d225ee5e43b85d'
    symbols={s.name:s['st_value'] for s in ELFFile(io.BytesIO(common)).get_section_by_name('.symtab').iter_symbols()}
    cardio=prepare_cardio(root/'lib/cardio/cardio.c',out/'cardio')
    timer=prepare_timer(root/'lib/lifetime/timer.c',out/'timer')
    parser=prepare_parser(root/'lib/film-storage/film_parse.c',out/'parser')
    # Preserve the already checked X-T2 UI packet extent. No custom pages in
    # this component; the upstream optional page handler remains guarded.
    post=(root/'lib/menu/xpp/post.c').read_text()
    for old,new in {
        'unsigned char payload[0x2c];':'unsigned char payload[0x44];',
        'int xpp_menu_entries_key(unsigned int *code, unsigned int flags);':
        'int xpp_menu_entries_key(unsigned int *code, unsigned int flags) __attribute__((weak));',
        'status == 0 && xpp_menu_entries_key(&event->code, event->flags)':
        'status == 0 && xpp_menu_entries_key && xpp_menu_entries_key(&event->code, event->flags)'
    }.items():
        assert post.count(old)==1,old
        post=post.replace(old,new)
    post+='\n_Static_assert(sizeof(struct ui_message)==76,"X-T2 packet");\n'
    (out/'post.c').write_text(post)
    (out/'api.h').write_bytes((root/'targets/xt2-441-api.h').read_bytes())
    sources=[root/n for n in [
        'lib/film-storage/film_loader.c',
        'lib/films/film_user_table.c','lib/films/xpp/cards.c',
        'lib/films/xpp/choice.c','lib/films/xpp/film_labels.generated.c',
        'lib/films/xpp/film_sources.generated.c','lib/settings/json.c',
        'lib/settings/generated/film.c','lib/cardio/unpaced/unpaced.c',
        'lib/lifetime/lifetime.c','lib/libc/string.c','lib/menu/xpp/input.c']]
    sources += [parser,cardio,timer,out/'post.c',Path(__file__).with_name('aeabi_loader_memory.c').resolve()]
    includes=[out,out/'cardio',root/'include']+[root/n for n in [
        'lib/libc/include','lib/film-storage/include','lib/films/include',
        'lib/films/xt20/include','lib/settings/include','lib/lifetime/include',
        'lib/cardio/include','lib/menu/xpp/include','lib/menu-stock-choices/include',
        'lib/resources/include','lib/xpp-hook/include']]
    deps={Path(__file__).resolve(),root/'targets/xt2-441.json',root/'targets/xt2-441-api.h',
          root/'lib/cardio/cardio.c',root/'lib/lifetime/timer.c',root/'lib/film-storage/film_parse.c',
          root/'lib/menu/xpp/post.c'}
    for name in ['prepare_cardio_status.py','prepare_cardio_listing.py',
                 'xt2_cardio_status_reference.h','xt2_cardio_listing_reference.h',
                 'prepare_timer_restart.py','prepare_film_parser.py']:
        deps.add(Path(__file__).with_name(name).resolve())
    commands=[];objects=[]
    for i,source in enumerate(sources):
        obj=out/f'{i}.o';objects.append(str(obj))
        cmd=[a.clang,'--target=armv7-none-eabi','-march=armv7-a','-marm','-mfloat-abi=soft',
             '-std=gnu11','-O2','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections',
             '-DXPP_TARGET','-DX70_SETTINGS_PROCESSOR="xprocessor-pro"',
             *[f'-I{x}' for x in includes],'-MMD','-MF',str(out/f'{i}.d'),'-c',str(source),'-o',str(obj)]
        subprocess.run(cmd,check=True);commands.append(cmd)
        deps.update(Path(x) for x in shlex.split((out/f'{i}.d').read_text().replace('\\\n',' ').split(':',1)[1]))
    native=json.loads((root/'targets/xt2-441.json').read_text())['symbols']
    native.update(storage_media_ready=0x967490,storage_media_queue=0x9c3544,
                  storage_send_request_packet=0x969f24,dispatch_current_task=0xceed8c,
                  ui_post_message=0xcf8da8,ui_next_event=0x14da7ac,
                  ui_screen_request=0x22e7364,ui_screen_request_send=0x15ca508)
    imports={n:symbols[n] for n in ['xpp_menu_stock_show','xt20_film_recipes']}
    script='''ENTRY(film_loader_boot)
EXTERN(film_loader_ready film_loader_idle film_loader_reload film_loader_refresh x70_lifetime_live)
SECTIONS {
 . = 0x2100000; .text : { *(.text*) } .rodata : { *(.rodata*) }
 . = ALIGN(4096); .data : { *(.data*) *(.x70mod.shared*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.x70mod.hooks*) *(.x70mod.strings*) }
}
'''
    script+=''.join(f'{n} = {v:#x};\n' for n,v in sorted((native|imports).items()))
    (out/'component.ld').write_text(script)
    cmd=[a.linker,'--threads=1','--gc-sections','-T',str(out/'component.ld'),
         '-Map='+str(out/'component.map'),*objects,'-o',str(out/'component.elf')]
    subprocess.run(cmd,check=True);commands.append(cmd)
    report=dict(scope=__doc__,common_sha256=sha(common),imports=imports,commands=commands,
                dependencies={str(x):sha(x.read_bytes()) for x in sorted(deps)},
                elf_sha256=sha((out/'component.elf').read_bytes()),hardware_verified=False,
                installable=False,common_candidate_changed=False)
    report['compiler']=subprocess.check_output([a.clang,'--version'],text=True).splitlines()[0]
    report['linker_sha256']=sha(Path(a.linker).read_bytes())
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(elf_sha256=report['elf_sha256'],installable=False)))


if __name__=='__main__':main()
