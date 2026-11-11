# X-T2 native SAVE DATA menu consumer

AI-assisted continuation, November 11, 2026. The existing FORMAT CARD NAME
declaration now has a tested native SAVE DATA consumer. This closes the missing
consumer of the preceding volume-name stage within the bounds below. It does
not complete the full FujiMod port or physical camera acceptance.

## Implementation and exact artifact

`prepare_save_data_menu.py` selects the scalar SAVE DATA item closure from
upstream `menu/xpp/menu_entries.c`, pin
`9d22f1b41c70c20407158e699f2583ac4907ff16`, blob
`c3774209fc38963874c19e5b39b431b47ae2167b`. The existing choice/get/set methods,
open-note tracking and bank-snapshot restoration contract are reused. The two
former X-T2 stock-choice/caption bridges are replaced in their existing library
selection; no second menu service or duplicate hook owner is added.

The selected closure serves SAVE DATA scalar choices only. It records an error
for unsupported declarations rather than silently dropping another mod's item.
Fn/Q assignment, other lists, action rows and item pages are not enabled here.
FORMAT CARD NAME uses the unchanged original `save_data` owner and choices.
The X-T2 adapter uses a 24-byte mod-owned label buffer so the 16-character title
keeps its final E; no native object/record ABI or shared upstream header grows.

The X-T2 list is not the four-row X-T20 list. The independently checked X-T2
descriptor is table ID `0xf8`, screen key `0x49`, menu index `0x349`, with eight
stock rows. All eight child pointers and 48-byte resource records are retained.
Its table lookup and dependency callers were located from their real native
contracts, not an address delta. Native interface constructor `cec598` is
required before stock FRAME NO. admission reads the DCF interface.

Primary build: `save-data-menu-native-build-unverified`; card sibling `-card`.

| File | SHA-256 |
| --- | --- |
| mods.elf | 892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e |
| region.bin | c14236301977ab5256d81cb2e4805b17ef5bcdf2b8d19b9389d7a99e4e7640c4 |
| ffsys.bin | b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351 |
| ffboot.bin | 76575223714856684953678903898924bac8fb5ae84c9780581b189023201da4 |

Five mods, 37 sources, 14 libraries, 72 delivered words. Four words are added
to the 68-word volume-name baseline: two SAVE DATA table pointers, native table
lookup and dependency entry. Existing apply/shown/snapshot/admission/OSD hook
sites remain singly owned. The ordinary builder checks all preimages, hook
conflicts and branch reach. Card `accepted=false` remains unchanged.

## New native UI evidence

`verify_save_data_menu_candidate.py`, report
`save-data-menu-check-unverified/verification.json`, passes on this exact ELF:

- All eight stock rows return the same original 40-byte native cursor records;
  their complete resources, child pointers and stock visibility statuses match
  an unmodified-firmware baseline using the same supplied inputs.
- The real native open event opens the nine-row SAVE DATA list. Its extra item
  opens a real two-row option descriptor, property `0x7f01`, table `0x7f03`.
  Native calls set the real `menu_open` byte; no host write supplies that flag.
- The original resource reader obtains FORMAT CARD NAME, ON and OFF tags. The
  delivered OSD entry/thunk turns them into the complete strings, and the
  original line body reaches native font measurement with each exact text
  pointer and supplied font size 24. Reusing each object for a stock message
  restores its original type/style. Glyph/display completion is not claimed.
- Modes 0, 1, 2, 7 and 32 leave the complete mod region unchanged when the
  selected apply/shown/admission/dependency/snapshot handlers are called.
- A native internal directional packet executes
  `bf7b88 -> 14a7f1c -> 141cd64`, moves the actual cursor to OFF and applies the
  value through the synthetic-property hook. No host cursor/value update is
  used and no internal stock-setting writer runs for this synthetic setting.
- The original bank checkpoint/restore routines preserve the upstream generic
  item contract: OFF preview requests generation 1; cancel restores ON and
  requests generation 2; another OFF preview and commit keep generation 3.
  Repeated application/commit and an invalid row do not add a request. Reopen
  computes its cursor from the restored value. The original owner serializes
  the committed value as `{"date_card_name":false}`.

These are explicit stock checkpoint calls; physical MENU/OK and DISP/BACK
message routing is not inferred from them. The native open/close events and
directional packet processing are executed separately and recorded precisely.

The first bare-fixture open and refresh failed through the unregistered DCF
interface (`cece10`); adding the actual existing `cec598` constructor resolved
it. No drive table, ready byte or successful callback was supplied manually.
The declared existing calibration/REC globals and uncontended transport fixture
remain. Two compiler errors in the selected declarations and checker-only
budget/void-result/observation-stop issues were corrected; old logs remain.

## Settings integration and related checks

`verify_full_storage_guard.py --menu-flow` also runs this menu on the existing
policy-started, catalog/SETTINGS-loaded machine. It keeps REC mode 3 to isolate
the `menu_open` gate from the independent SETUP-mode gate. The real native open
sets the flag; preview/cancel/commit produce the expected owner generations.
During 363 native ticks with the menu open, no file API runs. Native close
clears the flag; the next timer serializes committed OFF together with ETERNA
and issues the existing settings write. The real missing-driver branch then
returns error 5, the correct generation fails, and existing resources retire.
No successful native write is substituted or claimed.

Owner-flow report:
`menu-native-storage-check-unverified/restore/eterna/save-data-0-1/menu-owner-flow/valid.json`.
The separate native storage suite includes callback, dispatcher, file-error,
restore and serialization regressions; follow its own checkpoint/freeze.

`verify_save_data_menu_dependencies.py` reruns the earlier formatter/codec,
native calendar/lock, thunk fifth-argument/callee-saved ABI and actual native
BSS/heap tests on this new ELF. All 14 formatter and four codec cases pass in
`save-data-menu-dependencies-unverified/verification.json`. Its old absent-menu
assertion is replaced with the actual linked consumer, and word count is 72;
numeric and boundary checks are otherwise unchanged.

The lead's exact-ELF checks pass in `save-data-menu-regressions-unverified`:
NR 43 cases/three menu bindings, JPEG-max 33/three, six films 356 transfer and
99 identity cases/three native lists/six captions. A separate actual native
custom-slot pre-journal check is in `save-data-menu-custom-slot-check-unverified`;
it is not storage persistence evidence. Previous ELF results were not copied.

## Memory, reproducibility and commands

The measured new region is 245120 bytes. It fits the existing
`0x1380000..0x13c0000` reservation, leaving 17024 bytes. No new reservation or
heap/mapping/BSS operand is introduced. The exact new payload survives the
native BSS split and the original `_sbrk` crossing allocation is rejected.
The earlier full-span pattern/native-mapping proof still describes this same
unchanged reservation geometry; it does not execute these new UI hooks during
a complete startup. Full stack high-water and later lifetime are still open.

Fresh-directory build `save-data-menu-rebuild-unverified` reproduces the ELF,
region and both SD files byte-for-byte. Report:
`save-data-menu-check-unverified/rebuild.json`. GNU map text embeds temporary
object paths and is explicitly not byte-identical.

```sh
PYTHONPATH="$PWD/.toolchains/fujimod-944d5c8-source/bindings/python/python" \
PYTHONPYCACHEPREFIX=/private/tmp/xt2-save-menu-fresh-pycache \
XPP_SEGMENT_LOADER_TOOLCHAIN="$PWD/.toolchains/arm-gnu-13.2-darwin-arm64/bin" \
ports/fujimod-xt2/.venv/bin/python -u \
  ports/fujimod-xt2/build_save_data_menu_candidate.py --output NEW_DIRECTORY

LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" .venv/bin/python -u \
  ports/fujimod-xt2/verify_save_data_menu_candidate.py --build NEW_DIRECTORY \
  --output NEW_UI_REPORT_DIRECTORY

LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" .venv/bin/python -u \
  ports/fujimod-xt2/verify_save_data_menu_dependencies.py --build NEW_DIRECTORY \
  --output NEW_BOUNDARY_REPORT_DIRECTORY
```

The builder uses pinned local baseline inputs and restores all temporary
target/library metadata. Existing TCI execution outside the macOS sandbox was
used; no camera or network action occurs in these checks.

## Remaining gap and next step

SAVE DATA scalar item publication, native list/value paths and the original
settings request contract are now software-tested. Positive native settings
write/readback, complete ROM/SD/UI startup, scheduled lifecycle/capture work,
real rendering/display, cache/DMA and camera behavior remain unproved.
Other upstream menu capabilities are still software work, not hardware-only
unknowns. In particular this selected closure must be expanded and tested when
another list or Fn/Q assignment mod is added.

The next minimal reusable function is date-folders using this same save_data
owner/menu closure. Its X-T2 still-name doorway, real storage-context owner and
field layout need independent evidence; neither another device pointer nor
the X-T20 member offsets may be reused by analogy.

Generated `save-data-menu-inputs/*.c`, native reports, binaries and upstream
inputs stay private. `prepare_save_data_menu.py` contains substantial selected
engine templates and should also be excluded from an original-only public
publication without a separate license/source review. Original verification
tools and these notes can be reviewed for the permitted public subset.
