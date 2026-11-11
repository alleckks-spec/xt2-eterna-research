# Open-handle guard and native settings integration

AI-assisted original build/check adapters, November 11, 2026. No camera access.
This stage integrates the bounded open-handle subset of published x70view
PR471 into the existing ordinary X-T2 platform, preserving the corrected
dispatcher stack. It then checks the same behavior in the larger volume-name
configuration prepared by the other task worker.

## Guard artifact

`build_full_storage_guard_candidate.py` starts from the four-mod full-timer
receipt. Its one replaced C source is byte-equivalent to the earlier tested
listing/status component before the open-handle transformation. The other32
C sources and14-library selection remain unchanged. The earlier native
listing/error corrections remain present. No firmware symbol, request pool,
filesystem service, timer implementation or success backend is invented.

The source transformation is a bounded backport of
[PR471](https://github.com/justjake/x70view/pull/471), head
`2e2aa8af51526f81ec22036502b02881507dcd00`, contributed by Taylor Chapman
(heytchap) and Claude (Anthropic). The credit remains in the generated local
source and the original transformer. Generated upstream derivatives stay
private. This is **not** the PR's full guarded backend: builder-token identity,
lost-request timeout/recovery, task-context issue, stock/capture admission and
DMA/cache maintenance remain separate gaps.

Successful open callbacks with handle0, a handle at/above the native drive-A
range, or a negative handle no longer reach native read/write/seek/close
wrappers that would spin. The job reports -23 and retires its ownership.
Invalid stale opens retire without calling native close. Valid handles and
native error callbacks keep their previous boundaries.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| mods.elf |183584|cb2474c16e0c3583b2a5a63eaf82be71e8ac7aa06128db18f810e7b25d330925|
| region.bin |225924|babdcd691ad4e1a05b05406fae1f462e0463376c1a6d0a1d5c8abd340b5c35c7|
| ffboot.bin |46505984|bc2b9eaa4875f1fd20782ae76d38c1d8a201e9d3ca98cb01fb85d9b43c7a48c6|
| ffsys.bin |2048|b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351|

Directories: `full-storage-guard-build-unverified/`, its `-card` sibling and
`full-storage-guard-rebuild-unverified/` with its `-card` sibling. The four
binary artifacts reproduce byte-for-byte in a fresh output directory.
There are67 delivery words. Resident footprint grows by32bytes and fits the
unchanged229376-byte reservation with3452bytes spare. This footprint applies
only to this four-mod composition.

## Exact-ELF evidence

`verify_full_storage_guard.py` reuses the frozen existing native helpers;
it changes artifact selection, qualified region bounds and the necessary
request order. It does not edit the frozen checkers or their earlier reports.

-24 supplied pending-open callback cases execute the actual linked begin,
  claim, finish and callback-retirement code. Invalid handles/errors/stale
  callbacks retire; valid handles stop at the native I/O entry before any
  filesystem success is supplied. The full ELF dead-strips the bank/lifetime
  getters, so assertions observe actual `bank_job`, `bank_state`, `live` and
  `callbacks` words. No API getter shim is installed.
- Actual `film_loader_boot` registers the production periodic callback;
  native tick dispatch calls `film_loader_tick` and its real observer twice.
  Original/fixed stack controls give4mod8/0mod8. The fixed mode0 path uses
  at most88observed stack bytes, restores outer SP and preserves sentinels.
  This is not a stack bound for parsing/capture or a scheduled timer thread.
- Existing central-assembly reader-first/writer-first interleavings and the
  declared seven-argument still-wrapper boundary pass on this changed ELF.
- Supplied film data traverses native open/read/close, parser, publisher and
  UI into the real still body. Malformed JSON and native read error256 are
  rejected with resources retired at the existing three lowerFS boundaries.
- Seven saved film choices traverse native settings read/codec and actual
  still assembly without a setter after restoration; malformed/read-error
  film cases preserve the existing rejection contract.
- Commit/cancel, one save request after repeated commit and the real native
  missing-write-driver refusal still behave as before. This is a regression,
  not new positive-write progress: no native write body or successful save
  completion is produced.

Reports: `full-storage-guard-check-unverified/`.
`verify_storage_guard_delivery.py` pins17 related reports to this exact ELF,
verifies all source hashes,67-word ELF/region/SD correspondence and the fresh
binary rebuild. Numeric NR/JPEG reports from older ELF artifacts are **not**
silently transferred to this changed artifact; the final larger composition
has its own separate numeric regressions coordinated by the parent task.

## Integration into the larger five-mod artifact

The independently built `volume-name-resized-build-unverified/` contains this
guard, the timer word and the existing sd-volume-name/save_data implementation.
Its exact ELF is
`58eab0e9177c61d00b689b4bd08ae3c52cb7215975266f7bc93d6462d0c3affa`;
region229736bytes, SHA256
`7100b2fed021ad828c959932926b3bc56440ad5c4b4ae4aa2abd9562c84dc41a`.
ffboot SHA256:
`e4135cad07d50a1eaed6af4473667cd842d766285eb474365bf0301f715f8c5e`.
It has37C sources and68delivery words at its newly checked larger reservation.
See that composition's own memory/formatter checkpoint for its measured
reservation change; the smaller four-mod reservation is not reused as proof.

The same24callback, production-timer, central assembly, native file and error
checks pass on this relocated ELF. Actual policy startup registers the new
save_data owner before the prior late-start owners, changing the real timer
slot order. The first native300ms tick now starts the film catalog before
SETTINGS.JSN. The earlier harness assumed settings first and stopped at that
honest mismatch. The corrected harness completes the actual catalog request,
retains both native worker frames, then lets later native ticks admit the
settings file. It never reorders timer slots, patches readiness or calls a
successful kernel/storage substitute.

Seven saved choices and two film-rejection cases then pass in the actual
catalog-first order. The runtime's two distinct owner pointers are checked:
stock_choices and save_data. An absent save_data section decodes its defaults
(date_folders0/date_card_name1), with found0; the supplied stock section has
found1. Both owners reach registered2, loads1 and error0.

Two additional native-read cases supply a real save_data section alongside
the saved ETERNA selection. date_card_name=false and true both restore into
the actual owner/global value, with date_folders=false. Actual still ETERNA
parameters are checked after decode without a new selection setter. These
are saved JSON inputs at the declared native lowerFS boundary, not files
previously written by the camera.

A subsequent commit encodes both owners correctly: default save_data is
omitted from the166-byte JSON; restored date_card_name=false survives in the
216-byte JSON beside the ETERNA selection. Native write-open then encounters
the real unregistered write driver and fails. Requested/dirty/error state
and retry ownership remain intact and file/bank/callback resources retire.
There is no successful native write/readback/power-cycle result.

Reports: `volume-name-storage-check-unverified/`. Delivery audit pins20
related reports to the exact ELF and checks byte-identical fresh artifacts
against `volume-name-rebuild-unverified/`. The two supplied-section reports
are under `restore/eterna/save-data-0-{0,1}/valid.json`; the nondefault
serializer regression is `write-save-data-0-0/verification.json`.

## Reproduction and remaining boundary

Use the same pinned builder environment as FULL_TIMER_CHECKPOINT. Build with
`build_full_storage_guard_candidate.py --output NEW_DIRECTORY`, then repeat
with a fresh directory. Runtime checks use the existing local TCI environment:

```sh
PYTHONPATH="$PWD/scripts:$PWD/ports/fujimod-xt2" \
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 \
.venv/bin/python ports/fujimod-xt2/verify_full_storage_guard.py \
  --case restore --saved-choice eterna \
  --build ports/fujimod-xt2/volume-name-resized-build-unverified \
  --output ports/fujimod-xt2/NEW_REPORT_DIRECTORY \
  --date-card-name 0 --date-folders 0
```

Cases are callbacks, timer, processing, file, restore and write. File/restore
retain `--invalid-json` and `--read-error 256`; restore supports all seven
saved names. Runtime calls require the same approved local unsandboxed TCI
execution as earlier project assays. The delivery checker accepts --build,
--rebuild and --reports after the required related reports exist.

The outstanding positive native-write chain remains a software gap: genuine
write-driver registration/bootstrap, open/create, write/count, close, readback
and restore. Capture admission, callback task issue, watchdog/lost requests,
DMA/cache, full boot/timer scheduling, physical SD writes, power-off/C1-C7 and
hardware color/encoder behavior remain unproved. Continue the native driver
registration chain and independent remaining X-T20 mod adaptations. None of
these candidates is a completed or hardware-qualified full port.
