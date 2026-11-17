"""Build an isolated caption-only successor of the camera checkpoint.

Requires the owner's local private workspace. Only this original tool is public;
the copied donor label source, firmware and build products remain local.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

LAB = Path(__file__).resolve().parents[1]
WORKSPACE = LAB.parents[1]
PORT = WORKSPACE / 'ports/fujimod-xt2'
BASE = PORT / 'controls-lookup-build-unverified'
BASE_SHA = '2b0eb7506be88d6eafdf17dafb1e2abced2981187e79b30d5c794fcd332d3619'
PROFILES = {
    'eterna': ['ETERNA'],
    'classic_neg': ['CLASSIC', 'NEG.', 'APPROX.'],
    'bleach_bypass': ['BLEACH', 'BYPASS', 'APPROX.'],
    'nostalgic_neg': ['NOSTALGIC', 'NEG.', 'APPROX.'],
    'reala_ace': ['REALA', 'ACE', 'APPROX.'],
    'neutral': ['NEUTRAL'],
}
# Original single-line lettering on a 2x4 grid; no extracted font or icon data.
# Spaces separate pen strokes, digits give x/y pairs (origin is bottom left).
FONT = {
    'A': '0003142320 0121', 'B': '0004 0414232212 120212212000',
    'C': '24040020', 'E': '24040020 0222', 'G': '240400202212',
    'H': '0004 2024 0222', 'I': '0020 1014 0424', 'L': '040020',
    'N': '00042024', 'O': '0004242000', 'P': '0004242202',
    'R': '0004242202 1220', 'S': '240402222000', 'T': '0424 1410',
    'U': '04002024', 'X': '0024 0420', 'Y': '041224 1210',
    '.': '1010',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def vector(lines, width, height):
    """One solid-white stroked GVFF, with a two-pixel minimum outer margin."""
    scale = min((width - 6) / (3 * max(map(len, lines)) - 1),
                (height - 6) / (6 * len(lines) - 2))
    segments, coords = [], []
    total_height = (6 * len(lines) - 2) * scale
    top = (height + total_height) / 2
    for row, text in enumerate(lines):
        left = (width - (3 * len(text) - 1) * scale) / 2
        for col, char in enumerate(text):
            if char == ' ':
                continue
            for stroke in FONT[char].split():
                points = [(int(stroke[i]), int(stroke[i + 1]))
                          for i in range(0, len(stroke), 2)]
                for index, (x, y) in enumerate(points):
                    segments.append(2 if index == 0 else 4)
                    coords.extend((left + (col * 3 + x) * scale,
                                   top - (row * 6 + 4 - y) * scale))
    f = lambda n: struct.unpack('<I', struct.pack('<f', n))[0]
    header = struct.pack('<10I4f', 0x46465647, 0, 0x10002, 0, 56,
                         1, 1, 0, 0x29a, 0, 0, 0, width, height)
    paint = struct.pack('<9I', 0, 0x1b00, f(1), f(1), f(1), f(1), 0, 0, 0)
    words = [1, 0, 1, 0, 0, 0x29a, 0x1900, 0x1801, 0x1701,
             f(max(0.8, scale * 0.65)), f(4), len(segments), len(coords) * 4]
    return (header + paint + struct.pack('<13I', *words) + bytes(segments)
            + bytes(4 - len(segments) % 4) + struct.pack('<%df' % len(coords), *coords))


def make_labels(inputs, badge_size=(150, 42)):
    source = PORT / 'vendor/x70view/decomp/mods/lib/films/xpp/film_labels.generated.c'
    text = source.read_text()
    assert sha(source.read_bytes()) == 'fc81c137aadc35528b24a063290697f91fdf07b80d5e1bd212ccc2371659e273'
    text = text.replace('#include "film_xt20.h"', '#include "film_xt20.h"\n#include "xpp_icons.h"')
    declarations, assets = [], {}
    for name, lines in PROFILES.items():
        ids = []
        for surface, (width, height) in {'picker': (36, 36), 'tile': (80, 48), 'badge': badge_size}.items():
            symbol = 'zz_xt2_film_' + name + '_' + surface
            layout = [' '.join(lines[:-1]), lines[-1]] if surface == 'badge' and len(lines) > 1 else lines
            blob = vector(layout, width, height)
            declarations.append('static const unsigned char ' + symbol + '_gvff[] __attribute__((aligned(4))) = {'
                                + ','.join(str(b) for b in blob) + '};\n'
                                + f'XPP_ICON({symbol}, {width}, {height}, {symbol}_gvff);\n')
            ids.append('XPP_ICON_WORD(' + symbol + ')')
            assets[symbol] = dict(lines=layout, width=width, height=height,
                                  bytes=len(blob), sha256=sha(blob))
        old = f'{{ &film_xt20_name_{name}, &film_xt20_description_{name}, 0, 0, 0 }}'
        new = f'{{ &film_xt20_name_{name}, &film_xt20_description_{name}, ' + ', '.join(ids) + ' }'
        assert text.count(old) == 1
        text = text.replace(old, new)
    marker = 'const struct xpp_menu_stock_label film_xt20_labels[16] = {'
    assert text.count(marker) == 1
    text = text.replace(marker, '\n'.join(declarations) + '\n' + marker)
    destination = inputs / 'film_labels.c'
    destination.write_text(text)
    (inputs / 'xpp_icons.h').write_bytes((PORT / 'native-icon-v2-inputs/xpp_icons.h').read_bytes())
    write_json(inputs / 'assets.json', assets)
    return source, destination, assets


def prepare(inputs):
    assert (LAB / '.git/HEAD').read_text().startswith('ref: refs/heads/experimental/')
    checkpoint = json.loads((WORKSPACE / 'artifacts/checkpoints/xt2-441-20261117/checkpoint.json').read_text())
    for name, digest in checkpoint['source_pins'].items():
        assert sha((WORKSPACE / name).read_bytes()) == digest, name
    assert sha((BASE / 'mods.elf').read_bytes()) == BASE_SHA
    base = json.loads((BASE / 'preparation.json').read_text())
    assert len(base['source_sha256']) == 79
    for name, digest in base['source_sha256'].items():
        assert sha(Path(name).read_bytes()) == digest, name
    inputs.mkdir(parents=True, exist_ok=False)
    old, new, assets = make_labels(inputs)
    binding = PORT / 'card-films-inputs/film_binding.c'
    binding_text = binding.read_text()
    anchor = '.text_word = -1, .second_word = -1, .icon_word = -1, .tile_word = 4, .badge_word = -1'
    assert binding_text.count(anchor) == 1
    binding_copy = inputs / 'film_binding.c'
    binding_copy.write_text(binding_text.replace(anchor, anchor.replace('tile_word = 4', 'tile_word = 0')))
    vendor = PORT / 'vendor/x70view'
    roots = json.loads((BASE / 'source-roots.json').read_text())
    # Replay the exact saved metadata in a private shadow tree. Never rewrite
    # the baseline target, library metadata, pinned sources or tested packages.
    replaced, directories = 0, []
    expected = dict(base['source_sha256'])
    replacements = {str(old): str(new), str(binding): str(binding_copy)}
    for before, after in replacements.items():
        expected.pop(before); expected[after] = sha(Path(after).read_bytes())
    def select(body, directory):
        nonlocal replaced
        for key in ('sources', 'include'):
            if key not in body:
                continue
            values = body[key] if isinstance(body[key], list) else [body[key]]
            values = [str((directory / p).resolve()) for p in values]
            if key == 'sources':
                replaced += sum(p in replacements for p in values)
                values = [replacements.get(p, p) for p in values]
            body[key] = values if isinstance(body[key], list) else values[0]
    for key, root in roots.items():
        if not key.startswith('lib-'):
            continue
        origin = Path(root) / 'lib.json'
        spec = copy.deepcopy(base['metadata'][str(origin)] if str(origin) in base['metadata']
                             else json.loads(origin.read_text()))
        for body in (spec, spec.get('xpp', {})):
            select(body, origin.parent)
        spec.setdefault('xpp', {}).setdefault('include', str(origin.parent / 'include'))
        write_json(inputs / 'lib' / key[4:] / 'lib.json', spec)
    for index, directory in enumerate(map(Path, base['mod_directories'])):
        spec = json.loads((directory / 'mod.json').read_text())
        for body in (spec, spec.get('xpp', {})):
            select(body, directory)
        spec['include'] = [str(PORT / 'native-icon-v2-inputs'), *spec.get('include', [])]
        destination = inputs / ('mod-%02d' % index)
        write_json(destination / 'mod.json', spec)
        directories.append(str(destination))
    assert replaced == 2
    target = json.loads((BASE / 'target.json').read_text())
    write_json(inputs / 'target.json', target)
    return base, expected, directories, target, assets


def main(output, inputs, grow=False):
    output, inputs = output.resolve(), inputs.resolve()
    assert not output.exists() and not Path(str(output) + '-card').exists()
    base, expected, directories, target, assets = prepare(inputs)
    sys.path[:0] = [str(PORT / 'vendor/x70view'), str(PORT / 'vendor/x70view/decomp/tools'), str(PORT),
                   str(WORKSPACE / '.toolchains/fujimod-944-emulator-python')]
    import mod, mod_xpp
    from tools.sd_boot import xpp_mods
    from build_framing_screens import resize
    if grow:
        # Existing measured reservation procedure, using the actual failed map.
        target_receipt = resize(target, grow)
    else:
        target_receipt = None
    old_libs, old_load, old_flags, old_linker, old_run = (
        mod_xpp.LIBS, xpp_mods.load_target, mod_xpp.COMPILE, mod_xpp.linker_script, mod_xpp._run)
    mod_xpp.LIBS = inputs / 'lib'
    def load_target(name):
        if name != 'xt2-441':
            return old_load(name)
        from tools import firmware_registry as registry
        assert target['firmware'] == name and target['firmware_sha256'] == registry.load(name)['source']['sha256']
        assert target['card_regions']
        return copy.deepcopy(target)
    xpp_mods.load_target = load_target
    mod_xpp.COMPILE += ' -include ' + str(PORT / 'controls-lookup-inputs/binding_identity.h')
    def linker(*args, **kwargs):
        result = old_linker(*args, **kwargs)
        addition = ''.join('  .x70mod.' + name + ' 0 (INFO) : { KEEP(*(.x70mod.' + name + ')) }\n'
                           for name in ['walkthrough_binding_choices', 'walkthrough_never_shown'])
        return result.replace('  .unexpected :', addition + '  .unexpected :')
    def run(command, work):
        try:
            return old_run(command, work)
        except ValueError:
            import shutil
            if (Path(work) / 'mods.map').exists():
                shutil.copyfile(Path(work) / 'mods.map', output / 'failed-mods.map')
            raise
    mod_xpp.linker_script, mod_xpp._run = linker, run
    try:
        specs = [json.loads((Path(p) / 'mod.json').read_text()) for p in directories]
        libraries = mod_xpp.resolve_libraries(specs, 'xt2-441')
        sources = [(mod_xpp.LIBS / n / p).resolve() for n, s in libraries.items() for p in s['sources']]
        sources += [(Path(d) / p).resolve() for d, s in zip(directories, specs) for p in s['sources']]
        assert len(sources) == len(set(sources)) == 79 and len(libraries) == 22
        assert {str(p): sha(p.read_bytes()) for p in sources} == expected
        print('Exact baseline selected; only copied labels and Q resource binding replaced.', flush=True)
        result = mod.build_xpp_mods(directories, output, 'xt2-441', 'reserved-native-prefix')
        assert all(row['available'] for row in result['availability'])
        assert len(result['words']) == 130
        write_json(output / 'target.json', target)
        write_json(output / 'preparation.json', dict(scope=__doc__, base_elf_sha256=BASE_SHA,
            elf_sha256=sha((output / 'mods.elf').read_bytes()), source_sha256=expected,
            reservation=target_receipt, inputs=str(inputs), assets=assets,
            generator_sha256=sha(Path(__file__).read_bytes()), hardware_verified=False))
        xpp_mods.compose_card('xt2-441', output, Path(str(output) + '-card'))
        print('Built', sha((output / 'mods.elf').read_bytes()), flush=True)
    finally:
        mod_xpp.LIBS, xpp_mods.load_target, mod_xpp.COMPILE, mod_xpp.linker_script, mod_xpp._run = (
            old_libs, old_load, old_flags, old_linker, old_run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--grow-from-map', type=Path)
    parser.add_argument('--toolchain-bin', type=Path,
                        help='Existing pinned GNU 13.2.Rel1 bin directory; normal hash checks remain enabled.')
    args = parser.parse_args()
    os.environ.setdefault('XPP_SEGMENT_LOADER_TOOLCHAIN', str(
        (args.toolchain_bin or WORKSPACE / '.toolchains/arm-gnu-13.2-darwin-arm64/bin').resolve()))
    if args.toolchain_bin:
        os.environ['XPP_SEGMENT_LOADER_TOOLCHAIN'] = str(args.toolchain_bin.resolve())
    main(args.output, args.inputs, args.grow_from_map)
