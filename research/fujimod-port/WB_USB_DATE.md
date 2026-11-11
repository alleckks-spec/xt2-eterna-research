# Compatible WB + USB + qualified A/B date-folders composition

`wb-usb-date-build-unverified` adds the frozen production dual-slot date layer
(0cbd4cb6) to the completed WB+USB composition (c4e87e6d), both derived from
native-menu base892f. The separate builder consumes frozen receipts, verifies
all79date freeze pins, rejects conflicting shared source/metadata/target owners
and uses the existing ordinary linker/SD composer. The date layer contributes
two existing producer instances; shared libraries and menu/settings owners are
included once. No new service, emulator, scheduler or file format is introduced.

Exact ELF: `18d06d6afe79b67dba7d9fae33ed0586d5d941a4ec40122502b8bc5d85f331d0`.
42 sources, 14 libraries, eight mods and81SDwords. Payload249224bytes occupies
the unchanged262144-byte reservation at0x1380000, leaving12920bytes. Fresh
`wb-usb-date-rebuild-unverified` and SD correspondence checks identify all four
reproduced files. No physical SD transfer or camera acceptance is claimed.

## Rerun evidence on the combined artifact

All checks below execute this exact ELF, rather than transferring a parent
artifact's results:

- WB84complete SAVE/cache-readback/recall/edit chains, two guards, seven reset
  cases; six import formats/42slots with primary and shadow marker invalidation.
- Native volatile USB controls and49native custom film SAVE cases.
- Native date A/B/auto arbitration, five catalog cases, four edge cases, two
  refusal cases and four OFF/stock cases, including counter preservation and
  callee-saved ABI. Date transitions, next-day requests and the explicit native
  post-open counter consumer remain qualified at their original lower boundary.
- Both SAVE menu items, ten native rows with all eight stock rows preserved;
  DATE FOLDERS property7f01/option7f03 and FORMAT CARD NAME7f03/7f05. The native
  settings-loaded owner flow uses these actual IDs and verifies native menu
  open/close, cancel/commit, save deferral and the real driver-refusal result.
- All21native storage/timer/settings/menu reports, formatter14/codec4, films356
  plus99identity checks, NR43/three menus and JPEG33/three menus.
- Delivered native BSS/allocator operands and map arguments; memory reservation
  and crossing-allocation refusal. Actual MMU installation is not asserted.

The original frozen checkers remain unchanged. Small inspect/anchor adapters
record original and adapted source hashes and preserve their native inputs and
limits. The separate WB+USB milestone and original date/USB/WB reports remain
frozen.

## Positive native SETTINGS persistence in the existing SDK

Both final original SDK probes are reused on this combined ELF. Their existing
two-A7 board, RAM-only FAT32 SD model, native mount, timer8/IRQ56, native tasks
and original storage workers execute. Default-owner commit writes ETERNA and
reads back166bytes; a separate fresh software board restores key32.

An additional nondefault-owner case calls the actual native property setter to
turn DATE FOLDERS on and FORMAT CARD NAME off. The save_data owner reaches
requested2/completed2/failed0. The actual merged SETTINGS.JSN write and readback
contain those two booleans plus ETERNA. A separate fresh software board consumes
those exact readback bytes and restores both values and key32, with owner
request/completion/failure generations allzero. No host settings decoder or
selection setter runs during restore. Neither case substitutes successful APIs,
callbacks, registration/VFP writes or ticks. The earlier intentionally missing
write-driver refusal fixtures continue to pass separately.

`verify_composed_sdk_settings.py --save-data-nondefault` is specifically the
qualified two-item menu mapping. Its default without that option preserves the
original892f probe behavior. Original SDK sources/reports remain byte-exact;
source history snapshots retain the earlier wrapper used by the default commit.

## Limits and next step

This closes software-fixture positive settings write/readback/restore for the
combined stock-choice and save_data owners. It does not prove physical SD or
NAND retention, power-loss safety, full ROM/camera boot, actual capture-time
contention, installed cache/MMU/DMA coherency, physical key routing or USB host
exchange. WB record extension ownership remains limited to the reviewed native
paths in WB_SHIFT_CHECKPOINT_2026-11-12.md. WB native NV-cache evidence is distinct
from the SD settings-file evidence. Native date post-open tests supply an
explicit lower boundary and do not fabricate a successful capture/file-open.

The next software step is the independently qualified Fn/Q aspect chooser and
its dependency/menu integration. Keep incompatible Fn action owners in separate
configurations and rerun affected exact-artifact checks before camera testing.
Generated derivatives, firmware bytes and private reports stay local. Only
original builder/adapters/checker and this note are publication candidates.

## Later negative-control discovery

A subsequent explicit native media-error fixture on18d06d6a exposes an inline
read callback while its cardio bank is RUNNING. The original callback is
classified stale and the request stays BUSY with an open handle. The passing
normal chains and listed bounded checks do not cover this newly reproduced
path. Existing upstream PR471 recorded-callback/task-issue adaptation is being
qualified in a separate successor. This frozen candidate does not contain
that fix and is not a completed or camera-accepted port. The raw local failure
report is cardio-task-contract-original-unverified/probe.json and is not
published. Private upstream inputs/generated C and all binaries stay local.
