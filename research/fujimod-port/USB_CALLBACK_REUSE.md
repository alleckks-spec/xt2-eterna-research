# FujiHack reuse: PR308 and one X-T2 USB prerequisite

Проверено 12 ноября 2026. Продолжение полного порта X-T2; Quick Start,
установщик X70 и новый runtime не включались в этот этап.

## Проверенные источники и соответствие текущему коду

| Источник | Что найдено | Что уже есть у нас / решение |
|---|---|---|
| [PR308](https://github.com/justjake/x70view/pull/308), head `6d189457bf14e9894b917fbd62e4479eea8eb2ff`, FujiMod gitlink `b4314dd650e3ff57755250cb6315636d817b8ff1` | PR открыт, `draft=false`. Штатный callback/E1 transport, общий Memory owner и проверки восстановления; полноценный backup X-T2 не подтверждён | USB debug F7/Fn уже адаптирован. Проверена следующая отдельная граница: native-публикация диагностического callback. Общую зависимость не обновляли |
| [X-T2 flash facts](https://github.com/justjake/fujimod/commit/480aded02e849c6c66a1611b45ee9db2763ad853) | Готовый contract для 64 MiB serial NOR, штатного reader и `xpp-cmd-callback` | Выбранный JSON использован локально для сверки; его 32 KiB контрольный участок совпал с официальным update. Это сравнение исходного update, а не flash readback |
| [PR470](https://github.com/justjake/x70view/pull/470) `e007961f…`, [PR471](https://github.com/justjake/x70view/pull/471) `2e2aa8af…` | Heads совпадают с ранее проверенными источниками | Исправление timer stack, проверки handles и recorded callback/task issue уже перенесены. Их исходные проверки здесь не повторялись |
| [PR472](https://github.com/justjake/x70view/pull/472) `b2ca467f…`, [PR474](https://github.com/justjake/x70view/pull/474) `93f394d1…` | Опубликованы capture/storage contract и ограниченный draft X100F target | X100F timing/GPIO/ready/размещение нельзя перенести численно. Сам PR474 исключает полный набор feature switches и готовые SD builds |
| [Color Chrome branch](https://github.com/justjake/x70view/blob/5108aa3f7983e72a9edb53ebf97331356098eb16/decomp/mods/color-chrome/mod.json), [halation branch](https://github.com/justjake/x70view/blob/6fbcb400440410f4923164f1da7f48f7e93fd9a7/decomp/mods/halation/mod.json) | Код действительно опубликован. Проверенные metadata выбирают только `x70-110` | Не добавлялись в X-T2 и не объявлялись готовыми XPP/X-T20 эффектами. Это ограниченная проверка этих точных веток, не всех веток автора |

Дополнительно сравнен последний listing diff PR308 с нашим core. У нас уже есть
per-bank callbacks и различение конца/ошибки listing. Новое удержание/дренирование
abandoned directory cursor требует отдельного original/fixed контроля; этот diff
не подмешан в текущую сборку без такого контроля. Данная сверка не закрывает все
storage lifetime gaps.

## Один выполненный недостающий шаг

Добавлена оригинальная native SDK-проверка регистрации USB callback:
`ports/fujimod-xt2/probe_sdk_native_usb_callback.py`.
Штатный X-T2 caller класса3 сам выполняет factory, копирует свою таблицу и
публикует её через настоящий native publisher. После публикации:

- native table `0x1e0c180`, slot `+12` = `0x1e0c18c`;
- native diagnostic query callback `0x15e6888`;
- таблица побайтно совпадает с той, которую скопировал native factory;
- штатные callers классов2 и4 публикуют другие таблицы с нулём в этом slot.

Использован существующий SDK CPU/kernel/clock путь. Callback/table/ready и
успешные ответы API не подставлялись. Native factory очищает собственный
предписанный firmware буфер; стенд предоставляет RAM именно для этого буфера.
Scratch caller перенесён за его пределы, чтобы не пересечь штатную очистку.
Это не выбор нового свободного места для модов по нулевым байтам.

На каждом из трёх независимых стендов выполнение остановлено **до** отправки
сообщения запуска USB-класса. USB-запросов и обращений к физической камере нет.
Это проверка штатной функции и её записей, не доказательство режима JIG или
полного USB startup.

`ports/fujimod-xt2/verify_usb_callback_reuse.py` дополнительно проверяет все шесть
имеющихся immutable bulk code checks и исходный update-backed flash control.
Итог: `usb-callback-reuse-final-check-unverified/verification.json`, PASS.
Native отчёты: `sdk-native-usb-callback-{2,3,4}-unverified/probe.json`.

## Что осталось открытым

Нужно пройти реальный внешний выбор USB/service mode до этого caller, отдельно
проверить JIG, затем подключённый transport и контролируемый flash readback.
Наличие callback в проверенном class3 prefix не доказывает, что он зарегистрирован
в JIG. Полученных flash bytes и полного backup нет. Не выполнялись изменения
прошивки/SD-пакета, установка загрузчика, Quick Start или физические USB-команды.

Проверка относится к stock native SDK-пути X-T2 4.41. Её нельзя автоматически
перенести на ELF65ee4fb7 или новый capture/framing5152b253. Полный порт остаётся
активным; основной этап capture/framing не заменён работой над установщиком.

Upstream JSON, исходники, native reports и binding-доказательства остаются
локальными. Публикуются только оригинальный итоговый checker и эта новая выжимка;
они требуют подготовленных локальных входов и не являются standalone backup tool.
