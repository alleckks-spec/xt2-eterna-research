"""Build a bounded read/write component with the existing X-T2 compiler recipe.

The ordinary port is not altered. Exact original/fixed components allow
negative callback tests without inventing a successful filesystem backend.
"""
import argparse
import json
import shlex
import subprocess
from pathlib import Path
from prepare_cardio_open_guard import prepare, sha

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', action='store_true')
    p.add_argument('--linker', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    root = ROOT/'vendor/x70view/decomp/mods'
    source = prepare(root/'lib/cardio/cardio.c', out, a.original)
    (out/'build.json').unlink(missing_ok=True)
    reference = json.loads((ROOT/'cardio-status-component-unverified/build.json').read_text())
    compiler = reference['commands'][0][0]
    linker = str(a.linker.resolve())
    includes = [out, root/'include', root/'lib/cardio/include',
                root/'lib/lifetime/include', root/'lib/libc/include']
    sources = [source, root/'lib/lifetime/lifetime.c', root/'lib/libc/string.c']
    commands, objects = [], []
    deps = {Path(__file__), ROOT/'prepare_cardio_open_guard.py',
            ROOT/'prepare_cardio_status.py', ROOT/'prepare_cardio_listing.py'}
    for i, src in enumerate(sources):
        obj = out/f'{i}.o'
        objects.append(str(obj))
        cmd = [compiler, '--target=armv7-none-eabi', '-march=armv7-a', '-marm',
            '-mfloat-abi=soft', '-std=gnu11', '-O2', '-ffreestanding', '-fno-builtin',
            '-ffunction-sections', '-fdata-sections', '-DXPP_TARGET',
            *[f'-I{x}' for x in includes], '-MMD', '-MF', str(out/f'{i}.d'),
            '-c', str(src), '-o', str(obj)]
        subprocess.run(cmd, check=True)
        commands.append(cmd)
        deps.update(Path(x) for x in shlex.split((out/f'{i}.d').read_text().replace('\\\n', ' ').split(':', 1)[1]))
    target_path = ROOT/'card-processing-build-unverified/target.json'
    target = json.loads(target_path.read_text())
    deps.add(target_path)
    script = '''ENTRY(x70_cardio_read)
EXTERN(x70_cardio_list x70_cardio_write x70_cardio_write_at x70_cardio_abandon
       x70_cardio_bank x70_cardio_busy x70_lifetime_live x70_callback_issued)
SECTIONS {
 . = 0x2000000; .text : { *(.text*) } .rodata : { *(.rodata*) }
 . = ALIGN(4096); .data : { *(.data*) *(.x70mod.shared*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
'''
    script += ''.join(f'{name} = {value:#x};\n' for name, value in target['symbols'].items()
                      if name.startswith(('storage_', 'dispatch_')))
    (out/'component.ld').write_text(script)
    cmd = [linker, '--threads=1', '--gc-sections', '-T', str(out/'component.ld'),
           '-Map='+str(out/'component.map'), *objects, '-o', str(out/'component.elf')]
    subprocess.run(cmd, check=True)
    commands.append(cmd)
    report = dict(scope=__doc__, original=a.original, commands=commands,
        dependencies={str(x.resolve()): sha(x.read_bytes()) for x in sorted(deps)},
        elf_sha256=sha((out/'component.elf').read_bytes()),
        preparation_sha256=sha((out/'preparation.json').read_bytes()),
        linker_sha256=sha(Path(linker).read_bytes()), hardware_verified=False)
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(original=a.original, elf_sha256=report['elf_sha256'])))


if __name__ == '__main__':
    main()
