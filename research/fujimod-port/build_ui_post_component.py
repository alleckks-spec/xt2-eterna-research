"""Build a bounded X-T2 UI-post component, not an installable camera image.

AI-assisted original adapter. Requires privately supplied pinned upstream mods
sources. Generated upstream derivatives and objects must remain local. Reuses
the existing queue and input implementation; custom .activate pages are absent
from this component, so their optional handler is weak and guarded.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',required=True,type=Path,help='upstream decomp/mods directory')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--clang',default='clang')
    p.add_argument('--linker',required=True)
    args=p.parse_args();root=args.source_root.resolve();out=args.output.resolve()
    pins={'lib/menu/xpp/post.c':'8de17ec8f98fd55fdfc9df04f074c161573d9390',
          'lib/menu/xpp/input.c':'f87acf8063ad726246f74b37391ab4f0cf89e155'}
    for name,expected in pins.items():
        data=(root/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected
    out.mkdir(parents=True,exist_ok=True)
    header=Path(__file__).with_name('xt2_ui_post_message_reference.h')
    (out/header.name).write_bytes(header.read_bytes())
    text=(root/'lib/menu/xpp/post.c').read_text()
    replacements={
        'unsigned char payload[0x2c];':'unsigned char payload[XT2_UI_POST_PAYLOAD_BYTES];',
        'int xpp_menu_entries_key(unsigned int *code, unsigned int flags);':
        'int xpp_menu_entries_key(unsigned int *code, unsigned int flags) __attribute__((weak));',
        'status == 0 && xpp_menu_entries_key(&event->code, event->flags)':
        'status == 0 && xpp_menu_entries_key && xpp_menu_entries_key(&event->code, event->flags)'}
    for old,new in replacements.items():
        assert text.count(old)==1,old
        text=text.replace(old,new)
    text='#include "xt2_ui_post_message_reference.h"\n'+text
    text+='\n_Static_assert(sizeof(struct ui_message)==XT2_UI_POST_PACKET_BYTES,"X-T2 extent");\n'
    (out/'post.c').write_text(text)
    # Explicit assay callback; it is never part of a camera candidate.
    (out/'callback.c').write_text('''#include <string.h>
void __aeabi_memclr8(void *p, unsigned int n) { memset(p,0,n); }
extern unsigned int dispatch_current_task(void);
volatile unsigned int assay_callbacks, assay_callback_task;
void assay_callback(void) {
    ++assay_callbacks; assay_callback_task=dispatch_current_task();
}
''')
    includes=[out,root/'include',root/'lib/menu/xpp/include',root/'lib/xpp-hook/include',root/'lib/libc/include']
    sources=[out/'post.c',root/'lib/menu/xpp/input.c',root/'lib/libc/string.c',out/'callback.c']
    commands=[];objects=[]
    for i,source in enumerate(sources):
        obj=out/f'{i}.o';objects.append(str(obj))
        cmd=[args.clang,'--target=armv7-none-eabi','-marm','-march=armv7-a','-mfloat-abi=soft',
             '-std=gnu11','-O2','-ffreestanding','-fno-builtin','-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables','-ffunction-sections','-fdata-sections','-DXPP_TARGET',
             '-MMD','-MF',str(out/f'{i}.d'),*[f'-I{x}' for x in includes],'-c',str(source),'-o',str(obj)]
        subprocess.run(cmd,check=True);commands.append(cmd)
    script='''ENTRY(x70_menu_post)
SECTIONS {
 . = 0x2000000;
 .text : { *(.text*) }
 .rodata : { *(.rodata*) }
 .x70mod.hooks : { *(.x70mod.hooks*) }
 .x70mod.strings : { *(.x70mod.strings*) }
 . = ALIGN(4096);
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
ui_mode = 0x1218a70;
ui_next_event = 0x14da7ac;
ui_post_message = 0xcf8da8;
ui_screen_request = 0x22e7364;
ui_screen_request_send = 0x15ca508;
dispatch_current_task = 0xceed8c;
'''
    (out/'component.ld').write_text(script)
    cmd=[args.linker,'--threads=1','-T',str(out/'component.ld'),'-Map='+str(out/'component.map'),
         *objects,'-o',str(out/'component.elf')]
    subprocess.run(cmd,check=True);commands.append(cmd)
    deps=set(sources+[header,Path(__file__)])
    for i in range(len(sources)):
        deps.update(Path(x) for x in (out/f'{i}.d').read_text().replace('\\\n',' ').split(':',1)[1].split())
    report=dict(scope=__doc__,source_git_blobs=pins,changes=list(replacements),
        inputs={str(x):sha(x.read_bytes()) for x in sorted(deps)},commands=commands,
        elf_sha256=sha((out/'component.elf').read_bytes()),compiler=subprocess.check_output([args.clang,'--version'],text=True).splitlines()[0],
        installable=False,common_candidate_changed=False,hardware_verified=False)
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(elf_sha256=report['elf_sha256'],installable=False)))


if __name__=='__main__':main()
