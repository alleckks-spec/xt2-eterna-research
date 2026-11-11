# X-T2 custom WB pair: bounded native integration

The existing pinned x70view custom-WB-shift mod is adapted to X-T2 4.41 in
`wb-shift-coherent-build-unverified`. It saves the current WB R/B pair with
each of the seven native custom records and restores it through the existing
SAVE, recall and edit hooks. This does not add a separate WB editor.

Exact ELF: `b69eb2d7f5faf104566ddd25e25ea1eb6257b1305e41f4c686b2e965973924a7`.
The ordinary composition has 38 C sources, 14 libraries, six mods and 76 SD
words. Its 246144-byte payload occupies the existing 262144-byte reservation
at `0x1380000`, leaving 16000 bytes. The fresh
`wb-shift-coherent-rebuild-unverified` reproduces ELF, payload and both SD
files byte for byte. The delivery checker matches ELF → region → SD bytes.

## Storage decision and native lifetime

The X-T20 offsets cannot be reused: X-T2's existing name/property writers
occupy them. The declared extension uses absolute record offsets 0x84–0x86
for the existing magic/R/B tuple. This is qualified for the reviewed native
paths below, rather than inferred from zero-filled bytes or a copy end alone.

On the preceding exact 892f6d3b artifact, the canonical fixtures exercise
exactly seven records. The following block contains native UI state and is
not an eighth custom record. Earlier eight-block diagnostics remain preserved
as legacy evidence; their extra canary is not evidence of record ownership.

- 168 complete native recall/edit calls cover seven records and twelve WB
  modes, including the native journal, cache write and coherent bank copy.
- 15 complete defaults/reset/bank cases use native-initialized records and
  a real edit entry before reset. They cover whole-bank snapshot/cancel.
- Six actual native import formats cover 42 slot copies, native cache writes
  and 42 complete 256-byte cache readbacks. Import copies reach through 0x83.
- The corrected native custom SAVE serializer covers 49 slot/film cases.

The native import journal hook invalidates the old marker in both the active
record and its native shadow after field copies and before journaling. An
earlier primary-only candidate is retained as a negative control: all six
formats let native bank cancellation revive the stale shadow marker. The
coherent candidate prevents that revival in all seven records. No new
settings format, storage service or success callback is introduced.

## Exact changed-artifact checks

On b69eb2d7, 84 complete SAVE → native cache read → deliberately clobbered RAM
→ native cache reload → recall → edit chains pass across seven records and
twelve WB modes. They check the selected pair, Kelvin behavior, neighboring
records and tail canaries. Two marker/range guards and seven native reset,
defaults, subsequent SAVE and bank cancellation cases also pass. The upstream
defaults contract is retained: defaults reset stock fields while the previous
saved pair remains until the next SAVE; this is not a promise of zeroed WB.

The corrected 49-case native film serializer also passes on this exact ELF.
All 21 existing native storage/timer/settings/menu-chain reports were rerun,
including real native startup ordering, file error/refusal paths, merged
save_data restore and menu-open save deferral. The native SAVE menu, 14 name
formatter cases, four codec cases and delivered BSS/allocator checks pass.
Numeric regressions pass: films 356 plus 99 identity checks, NR 43 with three
menus, JPEG 33 with three menus. `integration.json`, `delivery.json` and the
frozen report manifest identify the exact evidence and source snapshots.

## Limits and next step

These are bounded executions of actual linked and stock ARM functions using
the existing harness. Native cache API entry/return and cache bytes are
observed; physical NAND completion, power-cycle persistence and camera
behavior are not proven. Raw record indices 0–6 are exercised; physical C1–C7
selection and button routing remain unverified. The supported-path extension
does not claim ownership against every unknown firmware writer.

Full boot, installed MMU/cache state, DMA and task/IRQ timing remain open.
The separate SD settings positive-write driver gap remains open; real refusal
is retained rather than replaced with success. The next integration step is
to compose the completed compatible date-folder/USB variants with this WB
layer and rerun affected exact-artifact checks before any camera validation.

Generated upstream derivatives, firmware bytes and raw private evidence stay
local. Only original transformers, builders, checkers and this note are
publication candidates, subject to the parent publication review.

## Parent publication review

The separate exact892f SDK positive settings-write/recovery chain has since
passed; see [native settings checkpoint](NATIVE_SETTINGS_PERSISTENCE.md).
That positive result is not transferred to this b69eb2d7 WB artifact.
The published build wrapper requires the local private-input transformer
prepare_wb_shift_candidate.py, which is intentionally not distributed with
its upstream-derived templates. Generated C, private inputs and native reports
stay local. The original checkers require the prepared existing workspace.
