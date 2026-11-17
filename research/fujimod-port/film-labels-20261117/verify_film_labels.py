"""Native menu/Fn/Q row, resource and stock-return checks on the delivered ELF.

Reuses the existing UI1 fixture with explicit REC/calibration inputs and native
constructors. This is CPU/function evidence, not physical display acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys

from build_film_labels import WORKSPACE, PORT, BASE, PROFILES, sha, write_json

os.environ.setdefault('LIBUNICORN_PATH', str(WORKSPACE / '.toolchains/unicorn-tci'))
sys.path[:0] = [str(PORT), str(WORKSPACE / 'scripts')]
from probe_fujimod_overlay import setup

NATIVE = dict(width=0x2759210, height=0x275926c, kind=0x27592c8, data=0x2759324,
              resource_kind=0x275430c, resource_data=0x2754390, resource_size=0x2759380)
SURFACES = [('menu', 9, 'recmenu_fsim_table', [(1, 'badge'), (4, 'picker')]),
            ('fn', 9, 'fn_fsim_table', [(4, 'picker')]),
            ('quick', 15, 'quickmenu_fsim_table', [(0, 'tile')])]


def main(build, output, inherited=False):
    output.mkdir(parents=True, exist_ok=False)
    u, s, call, word, evidence = setup(build)
    call(s['menu_table_by_key'], 0x49, task=True)
    stock, cases, returns = {}, [], []
    # The existing native 0x13db71c assay is a Fn lookup. Menu and Q use their
    # installed records directly here, then execute native icon/resource readers
    # and the actual cursor/selection paths below. Do not treat Fn lookup's
    # first argument as a universal table selector.
    for surface, count, table, words in SURFACES:
        p = s['xpp_stock_film_' + surface + '_records']
        stock[surface] = bytes(u.mem_read(p, count * 48))
        table_key = u.mem_read(s[table], 1)[0]
        rows = s['xpp_stock_film_' + surface + '_rows']
        assert [word(rows + 8 * i) for i in range(count, count + 7)] == [*range(32, 38), 0x7ffffffe]
        for index, name in enumerate(PROFILES):
            record = p + (count + index) * 48
            icons = []
            for field, kind in words:
                resource = word(record + 4 * field)
                if surface == 'fn':
                    assert call(0x13db71c, 9, count + index, field, task=True) == resource
                if inherited:
                    assert resource == word(p + 4 * field)
                else:
                    assert resource == s['zz_xt2_film_' + name + '_' + kind + '__xpp_icon_id']
                values = [call(NATIVE[k], resource, task=True) for k in ['width', 'height', 'kind', 'data']]
                width, height, vector_kind, data = values
                expected_size = {'badge': (150, 42), 'picker': (36, 36), 'tile': (80, 48)}[kind]
                assert (width, height, vector_kind) == (*expected_size, 1)
                assert bytes(u.mem_read(data, 4)) == b'GVFF'
                assert call(NATIVE['resource_kind'], resource, task=True) == 5
                assert call(NATIVE['resource_data'], resource, task=True) == data
                scratch = 0x8006000
                u.mem_write(scratch, b'\xa5' * 16)
                call(NATIVE['resource_size'], resource, scratch, task=True)
                assert struct.unpack('<HH', u.mem_read(scratch, 4)) == expected_size
                assert bytes(u.mem_read(scratch + 4, 12)) == b'\xa5' * 12
                icons.append(dict(kind=kind, id=hex(resource), width=width, height=height,
                                  data=hex(data), native_fn_lookup=(surface == 'fn'),
                                  native_icon_readers=True))
            if surface in ('menu', 'fn'):
                text_record = word(record + 8)
                if surface == 'fn':
                    assert call(0x13db71c, 9, count + index, 2, task=True) == text_record
                assert text_record == s['film_xt20_name_' + name]
                assert word(text_record) == 0x54787058
                text = bytes(u.mem_read(word(text_record + 4), 80)).split(b'\0')[0].decode()
                assert ('(approx.)' in text) == (index in (1, 2, 3, 4))
            else:
                text = None
            cases.append(dict(surface=surface, profile=name, text=text, resources=icons))
    # Exercise real native cursor events on all three lists. Commit every extra
    # row at the existing setter boundary, then return to each stock key.
    u.mem_write(0x119299b, bytes([0, 14, 7])); u.mem_write(0x119f2cb, b'\0')
    navigation = []
    for surface, count, table, words in SURFACES:
        descriptor = s[table]
        u.mem_write(0x11802c0, struct.pack('<I', descriptor))
        call(0x13df330, 0, 0, 0, 0, task=True)
        assert word(0x11802d8) == count + 6
        reached = set()
        for event in [4] * (2 * (count + 6)) + [5] * (2 * (count + 6)):
            call(0x13debf0, event, u.mem_read(descriptor, 1)[0], 1, 0, task=True)
            assert call(0xb518d4, 0x8003000, task=True) == 1
            key = word(0x800300c)
            if 32 <= key < 38:
                call(0x154b700, 0x1fc, key, task=True)
                assert word(s['film_choice_key']) == key
                assert call(0xb510b8, 0x1fc, 0, task=True) == 0
                assert call(s['film_xt20_select'], 0, task=True) == s['xt20_film_recipes'] + (key - 32) * 224
                reached.add(key)
        assert reached == set(range(32, 38)), (surface, reached)
        navigation.append(dict(surface=surface, all_six_reached=True, forward_backward=True))
        rows = s['xpp_stock_film_' + surface + '_rows']
        for index in range(6):
            for stock_index in range(count):
                stock_key = word(rows + stock_index * 8)
                call(0x154b700, 0x1fc, 32 + index, task=True)
                call(0x154b700, 0x1fc, stock_key, task=True)
                assert word(s['film_choice_key']) == 0
                assert call(s['film_xt20_select'], 0, task=True) == 0
                # The actual row/resource readers must return the original stock
                # bytes after every extra -> stock transition, including PROVIA.
                for field, kind in words:
                    value = word(s['xpp_stock_film_' + surface + '_records'] + stock_index * 48 + field * 4)
                    if surface == 'fn':
                        assert call(0x13db71c, 9, stock_index, field, task=True) == value
                    expected = struct.unpack_from('<I', stock[surface], stock_index * 48 + field * 4)[0]
                    assert value == expected
                returns.append(dict(surface=surface, profile=32 + index, stock_key=stock_key))
        assert bytes(u.mem_read(s['xpp_stock_film_' + surface + '_records'], count * 48)) == stock[surface]
    assert word(s['film_choice_status']) == word(s['xpp_menu_stock_status']) == 0
    report = dict(status='PASS', scope=__doc__, elf_sha256=sha((build / 'mods.elf').read_bytes()),
                  baseline_defect_reproduced=inherited, cases=cases, navigation=navigation,
                  stock_return_cases=len(returns), stock_records_unchanged=True,
                  setup=evidence, checker_sha256=sha(Path(__file__).read_bytes()),
                  graphics_presented=False, hardware_verified=False)
    write_json(output / 'verification.json', report)
    print(json.dumps(dict(status='PASS', profiles=6, surfaces=3, stock_returns=len(returns),
                          baseline_defect_reproduced=inherited)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-inherited', action='store_true')
    args = parser.parse_args()
    main(args.build.resolve(), args.output.resolve(), args.expect_inherited)
