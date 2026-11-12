"""Package the two audited X-T2 4.41 SD-test variants and verify every member.

Local-only firmware-derived artifacts. Publish this original tooling and notes,
never the generated archives, binaries, private inputs or raw native evidence.
"""
import argparse
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from build_modular_candidate import ROOT, sha

WORKSPACE = ROOT.parents[1]
NAMES = {
    'ordinary': 'xt2-441-full-ordinary-20261112-sdtest',
    'usb': 'xt2-441-full-usb-debug-20261112-sdtest',
}
RECEIPT = 'xt2-441-final-sd-packages-20261112.json'

PROTOCOL = '''Первый аппаратный тест полного FujiMod на X-T2 4.41
Статус: программные проверки пройдены, на камере НЕ запускалось.

Подготовка
X-T2 должна уже иметь штатную прошивку 4.41. Сохранить снимки и текущие
настройки; проверить обычный запуск без тестовой SD. Использовать отдельную
исправную карту, отформатированную камерой, и заряженный аккумулятор.
Для первого запуска оставить только тестовую карту; записать используемый слот.
USB и HDMI на первых этапах отключить. Варианты испытывать по очереди.

В корень SD скопировать только card/ffboot.bin и card/ffsys.bin одного пакета.
Прочитать их обратно с SD и сверить SHA256 с SD-FILES.json. Не копировать ELF,
region.bin, JSON из diagnostics, ZIP или DAT. Не смешивать разные пакеты.
Это существующий SD recovery-start; меню обновления DAT не используется.

1. Только старт и меню, без снимка.
На выключенной камере вставить SD. Удерживать Fn1 и нажатый задний диск при
включении; отпустить после начала загрузки. Записать время, LED и экран.
Ранний зелёный LED означает только вход carrier в RAM. Проверить выход в REC,
открыть I.Q./FILM SIMULATION, найти ETERNA и другие новые пункты.
Проверить открытие/закрытие I.Q./Fn/Q, BACK, кнопки и оба диска. Предел
наблюдения 90 секунд — предел протокола, не гарантия восстановления.
Если запуска или управления нет, не переходить к съёмке и не повторять вслепую.

2. Меню и обратимость выбора.
Проверить отмену PROVIA→ETERNA через BACK, затем подтверждение ETERNA.
Проверить ASPECT/SURROUND и направляющие, подписи размеров в Fn, меню controls.
Назначить одному control NEXT FRAMING GUIDELINE и проверить одно изменение
на нажатие; вернуть DEFAULT. Записывать фактические названия физических кнопок:
логические native event-тесты ещё не доказывают маркировку scanner на камере.

3. Одиночные снимки, только после нормальных этапов 1–2.
На неподвижной цветной сцене с фиксированными экспозицией/WB/DR снять
PROVIA→ETERNA→PROVIA. Дождаться каждой записи, сохранить оригиналы JPEG
и настройки. Отдельно проверить один квадратный кадр и возврат к 3:2.
Сравнить реальные размеры/EXIF/видимое кадрирование. Hook/дескрипторные
программные проверки не заменяют эту проверку пикселей и encoder output.
NR/JPEG-max и прочие параметры менять по одному с контрольным stock-снимком.
Первый проход — без серии и видео; это ещё не нагрузочная приёмка.

4. Сохранение SD-настроек и возврат к обычному запуску.
Зафиксировать настройки, штатно выключить и дождаться окончания активности.
Проверить созданный FUJIMOD/SETTINGS.JSN и сохранить его копию. Повторный
старт с тем же пакетом должен восстановить выбранные SD-настройки.
Затем выключить, дождаться окончания активности, удалить SD и проверить
обычный запуск, дату/время и штатные настройки без комбинации кнопок.
Не подменять проверку внутреннего NAND/C1–C7 наличием SETTINGS.JSN на SD.
WB C1–C7 испытывать отдельным контролируемым проходом после этих этапов,
с заранее записанными исходными значениями. Физическое сохранение не доказано.

5. Дополнительные функции отдельными проходами.
Профили с SD проверять на подготовленных совместимых JSON-рецептах в
FUJIMOD/FILMS: поставляемая функция — начальная загрузка при старте.
Runtime editor/refresh/reload в выбранной сборке не включены. Не удалять
и не менять карту во время записи для первого теста. FORMAT CARD NAME
и DATE FOLDERS испытывать на отдельной пустой тестовой карте, фиксируя
названия и результаты после выключения. Вариант USB имеет свой раздел README.

При экране обновления, неожиданном рестарте, потере управления, зависшей
записи или нештатном выключении сохранить наблюдения и прекратить проход.
Проверенного восстановления полностью зависшей камеры у проекта нет;
извлечение батареи нельзя объявлять гарантированным recovery.

В RESULT-TEMPLATE.txt записать хеши с карты, слот, время/LED/экран,
изменённые настройки, исходные JPEG и результат запуска без SD.
'''


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def archive_bytes(directory):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(directory.rglob('*')):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(str(Path(directory.name) / path.relative_to(directory)), (2026, 11, 12, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out.getvalue()


def verify(directory, archive_path, variant):
    checks = {}
    for line in (directory / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert name not in checks
        checks[name] = digest
        assert sha((directory / name).read_bytes()) == digest, name
    files = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    assert set(checks) | {'SHA256SUMS.txt'} == files
    assert {p.name for p in (directory / 'card').iterdir()} == {'ffboot.bin', 'ffsys.bin'}
    sd = json.loads((directory / 'SD-FILES.json').read_text())
    for name, record in sd.items():
        raw = (directory / 'card' / name).read_bytes()
        assert sha(raw) == record['sha256'] and len(raw) == record['bytes']
    proof = json.loads((directory / 'diagnostics/FINAL-VERIFICATION.json').read_text())
    selected = proof['variants'][variant]
    assert proof['status'] == 'PASS' and proof['software_package_gate']
    assert not proof['hardware_accepted'] and not selected['hardware_accepted']
    for name, record in selected['reproducible'].items():
        file = directory / ('card' if name.startswith('ff') else 'diagnostics') / name
        assert sha(file.read_bytes()) == record['sha256']
    assert selected['consumes_fn_image_size'] == (variant == 'usb')
    raw = archive_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        members = archive.namelist()
        assert len(members) == len(set(members)) == len(files)
        assert set(members) == {directory.name + '/' + n for n in files}
        for name in files:
            assert archive.read(directory.name + '/' + name) == (directory / name).read_bytes()
    assert raw == archive_bytes(directory), 'Deterministic repack differs'
    return dict(directory=str(directory),archive=str(archive_path),archive_bytes=len(raw),
                archive_sha256=sha(raw),files=len(files),variant=variant,
                elf_sha256=selected['elf_sha256'],sd_files=sd,
                all_members_verified=True,deterministic_repack=True,hardware_accepted=False)


def main(audit, artifacts, verify_only):
    proof = json.loads((audit / 'verification.json').read_text())
    assert proof['status'] == 'PASS' and proof['software_package_gate']
    assert set(proof['variants']) == set(NAMES) and not proof['hardware_accepted']
    for path, digest in proof['report_sha256'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    for path, record in proof['source_snapshots'].items():
        assert sha(Path(record['snapshot']).read_bytes()) == record['sha256'], path
    result = {}
    for variant, name in NAMES.items():
        directory, archive_path = artifacts / name, artifacts / (name + '.zip')
        selected = proof['variants'][variant]
        build = Path(selected['build'])
        if not verify_only:
            assert not directory.exists() and not archive_path.exists()
            (directory / 'card').mkdir(parents=True)
            diagnostics = directory / 'diagnostics'
            diagnostics.mkdir()
            for n in ['ffboot.bin', 'ffsys.bin']:
                shutil.copyfile(Path(str(build) + '-card') / n, directory / 'card' / n)
            for n in ['mods.elf','region.bin','preparation.json','manifest.json','target.json','source-roots.json']:
                shutil.copyfile(build / n, diagnostics / n)
            shutil.copyfile(audit / 'verification.json', diagnostics / 'FINAL-VERIFICATION.json')
            shutil.copyfile(audit / (variant + '-card.json'), diagnostics / 'CARD-CORRESPONDENCE.json')
            write_json(diagnostics / 'SOURCE-PINS.json', {p:r['sha256'] for p,r in proof['source_snapshots'].items()})
            write_json(directory / 'SD-FILES.json', {n:selected['reproducible'][n] for n in ['ffboot.bin','ffsys.bin']})
            (directory / 'HARDWARE-CHECK.txt').write_text(PROTOCOL)
            usb = '''USB-debug: отдельная несовместимая конфигурация.
Она занимает Fn IMAGE SIZE; обычный chooser IMAGE SIZE при этом действии
не сохраняется. Все девять новых controls/Q остаются в составе. Проверены
RAM/guards/GPIO/Fn ABI; физический кабель и host debug-протокол не проверены.
USB проверять отдельным проходом после базовой SD-приёмки. Этот пакет
не предоставляет доказанного flash backup, JIG-сеанса или обновления NAND.
''' if variant == 'usb' else '''Обычный вариант: USB-debug не включён, штатное действие Fn IMAGE SIZE
сохранено. Начинать аппаратную приёмку рекомендуется с этого пакета.
'''
            readme = f'''X-T2 4.41 — полный выбранный порт FujiMod, {variant}, 12 ноября 2026

Итоговый пакет программного этапа для аппаратного SD-теста.
На камере НЕ запускался; аппаратная приёмка не выполнена.
Подготовлено с помощью OpenAI Codex. Производные бинарные файлы только локально.

Состав: шесть встроенных film/RGB-профилей, начальная загрузка card films,
NR, JPEG-max, WB R/B для семи custom profiles, SD SETTINGS, SAVE DATA,
FORMAT CARD NAME, DATE FOLDERS, ASPECT/SURROUND, направляющие, overlay/
DevTools, меню и девять логических controls с Q. Не все названия каталога
имеют готовую X-T20 реализацию: F-Log/film-grain/HDMI-rec и отсутствующие
providers в этот выбранный порт не включены. Optional controls.function
direct-action provider не выбран; его owner остаётся с default-настройками.

{usb}
ELF SHA256: {selected['elf_sha256']}
{selected['sources']} C/ASM-источников; 22 библиотеки; {selected['mods']} модов;
{selected['words']} доставленных слов; payload {selected['payload_bytes']} байт.
В резерве осталось {selected['spare_bytes']} байт. Это остаток link-region,
а не доказанный запас heap/stack или нагрузки на настоящей камере.

Проверены точные ELF/region/оба SD-файла и их повторная сборка; numeric/menu/
WB/память, native controls/captions/dimensions/screens, ранние icon objects,
запись/чтение и fresh-board restore шести SETTINGS owners, storage fault/retry,
REC backpressure, FAT→recipe→UI→processing и ограниченный reader lifecycle.
Это CPU/native SDK/function fixtures. Полная ROM-загрузка камеры не эмулируется.

Не доказаны: реальные пиксели source0 и JPEG/EXIF output, непрерывная съёмка,
реальные cache/DMA/нагрузка, физические кнопки/экран, SD boot/power-cycle,
внутреннее NAND/C1–C7, выключение/восстановление и USB-сеанс.

Сначала читать HARDWARE-CHECK.txt. В корень SD — только два файла из card/.
SHA256SUMS.txt покрывает все вложенные файлы, SD-FILES.json удобен для
проверки копии на карте. diagnostics не копировать на SD. Исходные отчёты
и private-source-snapshot сохранены в рабочей папке, не в публичном GitHub.
'''
            (directory / 'README.txt').write_text(readme)
            (directory / 'LIMITS.txt').write_text('\n'.join(proof['limits']) + '\n')
            (directory / 'RESULT-TEMPLATE.txt').write_text(f'''variant={variant}
camera_model=X-T2
camera_firmware=4.41
elf_sha256={selected['elf_sha256']}
sd_slot=
sd_model_capacity=
ffboot_sha256_read_from_card=
ffsys_sha256_read_from_card=
boot_time_LED_screen=
menus_buttons_dials=
cancel_commit=
single_JPEG_original_files=
aspect_dimensions_EXIF=
settings_readback_and_second_boot=
shutdown_and_boot_without_SD=
failure_stage_and_observations=
''')
            builder = 'build_controls_lookup_candidate.py' if variant == 'ordinary' else 'build_q_usb_lookup_candidate.py'
            extra = '' if variant == 'ordinary' else ' --base ports/fujimod-xt2/controls-lookup-build-unverified --base-sha256 ' + proof['variants']['ordinary']['elf_sha256']
            (directory / 'REBUILD.txt').write_text(f'''Run from the original complete local workspace, with its pinned private inputs and toolchain.
Use a new unused output directory. The builder also produces <output>-card.
PYTHONPATH="$PWD/scripts:$PWD/ports/fujimod-xt2" .venv/bin/python ports/fujimod-xt2/{builder}{extra} --output <fresh-output>
Compare mods.elf/region.bin and both card files with FINAL-VERIFICATION.json reproducible hashes.
This package does not redistribute private upstream sources or the firmware needed for rebuilding.
''')
            checks = [f'{sha(p.read_bytes())}  {p.relative_to(directory)}' for p in sorted(directory.rglob('*')) if p.is_file()]
            (directory / 'SHA256SUMS.txt').write_text('\n'.join(checks) + '\n')
            archive_path.write_bytes(archive_bytes(directory))
        result[variant] = verify(directory, archive_path, variant)
    record = dict(status='PASS',software_package_gate=True,hardware_accepted=False,
                  audit_sha256=sha((audit / 'verification.json').read_bytes()),
                  packager_sha256=sha(Path(__file__).read_bytes()),packages=result)
    receipt = artifacts / RECEIPT
    if verify_only:
        assert json.loads(receipt.read_text()) == record
    else:
        assert not receipt.exists()
        write_json(receipt, record)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--artifacts',type=Path,default=WORKSPACE / 'artifacts')
    p.add_argument('--verify-only',action='store_true')
    a = p.parse_args()
    main(a.audit.resolve(),a.artifacts.resolve(),a.verify_only)
