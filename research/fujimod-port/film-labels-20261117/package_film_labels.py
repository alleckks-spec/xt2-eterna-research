"""Package only an exact ELF whose film-label native checks have passed.

Creates a fresh local camera-test directory and ZIP. Does not write an SD card,
alter a checkpoint or promote software results to camera acceptance.
"""
import argparse
import json
from pathlib import Path
import shutil
import zipfile
from elftools.elf.elffile import ELFFile

from build_film_labels import LAB, BASE, BASE_SHA, PROFILES, sha, write_json


START = """X-T2 4.41 — отдельный экспериментальный тест подписей

Проверка на камере для этого пакета ещё НЕ выполнена.
Используйте ранее подготовленную FAT32-карту. Не форматируйте её в камере.
Сохраните прежние файлы карты на компьютере. При выключенной камере замените
только ffboot.bin и ffsys.bin файлами из каталога card этого пакета.
Запуск — тем же проверенным способом, что у пакета Nov17.

Без съёмки проверьте СИМУЛЯЦИЯ ПЛЁНКИ в меню, назначенной Fn и Q:
ETERNA; Classic Neg.; Bleach Bypass; Nostalgic Neg.; REALA ACE; Neutral.
У четырёх приблизительных профилей остаются (approx.) / APPROX.
Пройдите список в обе стороны. Выберите каждый профиль, закройте и откройте
список. Вместо Стандарт/STD должно быть название выбранного профиля.
После каждого вернитесь в PROVIA; проверьте также Velvia и Classic Chrome.
Подписи штатных профилей должны оставаться штатными.

Выключите камеру, дождитесь окончания записи на карту, извлеките тестовую SD
и проверьте обычный штатный запуск. Зафиксируйте результаты в RESULT.json.

Исчезновение модов после простоя не исправлялось. Этот тест не подтверждает
качество цвета, JPEG, Exif, съёмку, видео или общую аппаратную стабильность.
"""


def scope_audit(build):
    """Check that old icon IDs/recipes/patch sites retain their original meaning."""
    old = json.loads((BASE / 'preparation.json').read_text())['source_sha256']
    new = json.loads((build / 'preparation.json').read_text())['source_sha256']
    common = set(old) & set(new)
    assert len(common) == 77 and all(old[n] == new[n] for n in common)
    assert {Path(n).name for n in set(old) - set(new)} == {'film_labels.generated.c', 'film_binding.c'}
    assert {Path(n).name for n in set(new) - set(old)} == {'film_labels.c', 'film_binding.c'}
    with (BASE / 'mods.elf').open('rb') as a, (build / 'mods.elf').open('rb') as b:
        ea, eb = ELFFile(a), ELFFile(b)
        sa = {s.name: s for s in ea.get_section_by_name('.symtab').iter_symbols()}
        sb = {s.name: s for s in eb.get_section_by_name('.symtab').iter_symbols()}
        ids = {n: s['st_value'] for n, s in sa.items() if n.endswith('__xpp_icon_id')}
        assert len(ids) == 20 and all(sb[n]['st_value'] == v for n, v in ids.items())
        assert sb['__xpp_icons_count']['st_value'] == 38
        def value(elf, symbol):
            section = elf.get_section(symbol['st_shndx'])
            start = symbol['st_value'] - section['sh_addr']
            return section.data()[start:start + symbol['st_size']]
        assert value(ea, sa['xt20_film_recipes']) == value(eb, sb['xt20_film_recipes'])
        assert ea.get_section_by_name('.text')['sh_size'] == eb.get_section_by_name('.text')['sh_size']
    a = json.loads((BASE / 'manifest.json').read_text())
    b = json.loads((build / 'manifest.json').read_text())
    assert {(r['address'], r['old']) for r in a['words']} == {(r['address'], r['old']) for r in b['words']}
    return dict(status='PASS', elf_sha256=sha((build / 'mods.elf').read_bytes()),
                unchanged_sources=77, replaced_sources=2, original_mod_icon_ids_preserved=20,
                new_icons=18, builtin_recipe_bytes_unchanged=True, text_section_size_unchanged=True,
                patch_sites_and_stock_preimages_unchanged=130, hardware_verified=False)


def main(build, checks, output, memory_report, menu_report, timer_report):
    assert (LAB / '.git/HEAD').read_text().startswith('ref: refs/heads/experimental/')
    assert not output.exists() and not output.with_suffix('.zip').exists()
    report = json.loads((checks / 'verification.json').read_text())
    digest = sha((build / 'mods.elf').read_bytes())
    assert digest != BASE_SHA and report['elf_sha256'] == digest
    assert report['status'] == 'PASS' and not report['baseline_defect_reproduced']
    assert len(report['cases']) == 18 and report['stock_return_cases'] == 198
    assert report['stock_records_unchanged'] and report['hardware_verified'] is False
    correspondence = json.loads((build / 'card-correspondence.json').read_text())
    assert correspondence['elf_sha256'] == digest
    assert correspondence['elf_region_equal'] and correspondence['region_sd_equal']
    extras = {}
    for name, path in [('MEMORY', memory_report), ('MENU', menu_report), ('TIMER', timer_report)]:
        data = json.loads(path.read_text())
        assert data['elf_sha256'] == digest
        assert data['status'].startswith('PASS')
        extras[name] = path
    audited = scope_audit(build)
    prep = json.loads((build / 'preparation.json').read_text())
    assert prep['elf_sha256'] == digest and len(prep['source_sha256']) == 79
    for name, expected in prep['source_sha256'].items():
        assert sha(Path(name).read_bytes()) == expected, name
    output.mkdir(parents=True)
    card = Path(str(build) + '-card')
    for name in ('ffboot.bin', 'ffsys.bin'):
        destination = output / 'card' / name
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(card / name, destination)
        expected = correspondence['files'][name]
        assert destination.stat().st_size == expected['bytes']
        assert sha(destination.read_bytes()) == expected['sha256']
    for name in ('verification.json',):
        shutil.copyfile(checks / name, output / 'SOFTWARE-CHECKS.json')
    for name, path in extras.items():
        shutil.copyfile(path, output / ('CHECK-' + name + '.json'))
    shutil.copyfile(build / 'card-correspondence.json', output / 'CHECK-SD.json')
    write_json(output / 'SCOPE-AUDIT.json', audited)
    (output / 'START-HERE.txt').write_text(START)
    write_json(output / 'RESULT.json', dict(package_elf_sha256=digest, hardware_verified=False,
        profiles={name: dict(menu=None, fn=None, q=None, stock_return=None) for name in PROFILES},
        stock_boot_without_sd=None, observations=''))
    records = {str(p.relative_to(output)): dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
               for p in sorted(output.rglob('*')) if p.is_file()}
    write_json(output / 'FILES.json', dict(elf_sha256=digest, files=records, hardware_verified=False))
    (output / 'SHA256SUMS.txt').write_text(''.join(
        f'{sha(p.read_bytes())}  {p.relative_to(output)}\n'
        for p in sorted(output.rglob('*')) if p.is_file()))
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                z.write(p, str(p.relative_to(output)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert z.read(name) == (output / name).read_bytes(), name
    print(json.dumps(dict(package=str(archive), sha256=sha(archive.read_bytes()),
                          elf_sha256=digest, hardware_verified=False)), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--checks', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--memory-report', type=Path, required=True)
    p.add_argument('--menu-report', type=Path, required=True)
    p.add_argument('--timer-report', type=Path, required=True)
    a = p.parse_args()
    main(a.build.resolve(), a.checks.resolve(), a.output.resolve(),
         a.memory_report.resolve(), a.menu_report.resolve(), a.timer_report.resolve())
