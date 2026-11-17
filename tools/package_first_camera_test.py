"""Package the unchanged ordinary candidate after upstream preflight.

Local-only output contains firmware-derived files. Never upload the package.
"""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT/'ports/fujimod-xt2'
SOURCE = ROOT/'artifacts/xt2-441-full-ordinary-20261112-sdtest'
NAME = 'xt2-441-first-camera-20261117'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT/'artifacts'/NAME
    assert not output.exists()
    proof = json.loads((SOURCE/'diagnostics/FINAL-VERIFICATION.json').read_text())
    selected = proof['variants']['ordinary']
    build = Path(selected['build'])
    prep = json.loads((build/'preparation.json').read_text())
    for path, expected in prep['source_sha256'].items():
        assert digest(Path(path)) == expected, path
    for line in (SOURCE/'SHA256SUMS.txt').read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert digest(SOURCE/name) == expected, name
    reports = {}
    for name in ['timer-fixed', 'menu']:
        path = PORT/'first-camera-preflight-20261117'/f'{name}.json'
        report = json.loads(path.read_text())
        assert report['status'] == 'PASS'
        assert report['elf_sha256'] == selected['elf_sha256']
        reports[name] = report
    assert reports['timer-fixed']['delivered_literal'] == '0x1187ffc'
    for name, record in selected['reproducible'].items():
        path = SOURCE/('card' if name.startswith('ff') else 'diagnostics')/name
        assert digest(path) == record['sha256']
    shutil.copytree(SOURCE, output)
    (output/'SHA256SUMS.txt').unlink()
    shutil.copyfile(PORT/'check_first_camera_card.py', output/'CHECK-CARD.py')
    (output/'START-HERE.txt').write_text('''ПЕРВЫЙ ТЕСТ X-T2 4.41 — 17 ноября 2026

Это ordinary-сборка от 12 ноября с повторной сверкой исправлений.
Бинарные файлы не изменены. На настоящей камере ещё НЕ проверена.
Исправление стека таймера уже присутствует. Native-проверка меню проходит.
Clarity, Color Chrome, Snap Focus и SD boot v2 в этот пакет не добавлены.

Подготовить: X-T2 со штатной 4.41, заряженный аккумулятор, отдельная исправная
SD, отформатированная камерой. Сначала сохранить фотографии и настройки,
записать C1–C7 и проверить обычную загрузку. Подготовить отдельную stock
recovery-карту и установить применимый способ резервного копирования и
восстановления. Полный бэкап нашей камеры и recovery ещё не подтверждены.

В корень тестовой карты скопировать ТОЛЬКО card/ffboot.bin и card/ffsys.bin.
Прочитать файлы с карты и сравнить SHA256 с SD-FILES.json. Не смешивать пакеты.
Можно выполнить: python3 CHECK-CARD.py /Volumes/ИМЯ_КАРТЫ
Эта команда только читает файлы и не записывает ничего на карту.
Оставить одну карту; записать слот. USB и HDMI отключить.

ПЕРВЫЙ ПРОХОД — БЕЗ СНИМКОВ И ИЗМЕНЕНИЯ НАСТРОЕК:
1. На выключенной камере удерживать Fn1 и нажатый задний диск при включении.
2. Записать на видео экран, LED и время загрузки. Зелёный LED сам по себе
   не доказывает запуск прошивки. Дождаться REC.
3. Открыть и закрыть I.Q./Fn/Q, проверить BACK, кнопки и оба диска.
   Проверить наличие новых пунктов, пока не сохранять C1–C7 и не снимать.
4. Штатно выключить, дождаться окончания активности карты. Извлечь карту
   на выключенной камере и проверить обычную загрузку без комбинации.
5. Заполнить RESULT-TEMPLATE.txt. Только после успешного прохода переходить
   к следующим этапам HARDWARE-CHECK.txt: выбор профилей, одиночные JPEG,
   затем SD-настройки и отдельные контролируемые проверки C1–C7.

Если за 90 секунд нет REC/управления, есть рестарт, зависание или экран
обновления — прекратить проход, сохранить видео и наблюдения. DAT-обновление
не запускать. Не повторять тест вслепую. Гарантированного восстановления
полностью зависшей камеры проект пока не подтвердил.
''')
    comparison = PORT/'FIRST_CAMERA_PREFLIGHT_2026-11-17.md'
    shutil.copyfile(comparison, output/'UPSTREAM-PREFLIGHT.md')
    for name in reports:
        shutil.copyfile(PORT/'first-camera-preflight-20261117'/f'{name}.json',
                        output/'diagnostics'/f'preflight-{name}.json')
    receipt = dict(status='PASS', firmware_changed=False, hardware_accepted=False,
                   source_package=SOURCE.name, elf_sha256=selected['elf_sha256'],
                   sd_files=selected['reproducible'], checked_sources=len(prep['source_sha256']),
                   comparison_sha256=digest(comparison), native_reports=reports)
    (output/'diagnostics/PREFLIGHT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    files = sorted(p for p in output.rglob('*') if p.is_file())
    (output/'SHA256SUMS.txt').write_text(''.join(f'{digest(p)}  {p.relative_to(output)}\n' for p in files))
    archive = output.with_suffix('.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                info = zipfile.ZipInfo(NAME+'/'+str(p.relative_to(output)),(2026,11,17,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert z.read(name) == (output.parent/name).read_bytes()
        assert len(z.namelist()) == len(set(z.namelist()))
    record = dict(status='PASS', directory=str(output), archive=str(archive),
                  archive_sha256=digest(archive), firmware_changed=False,
                  hardware_accepted=False, files=len(files)+1)
    (output.parent/(NAME+'-receipt.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)


if __name__ == '__main__':
    main()
