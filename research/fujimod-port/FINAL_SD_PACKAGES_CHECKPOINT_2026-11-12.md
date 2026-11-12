# Two final X-T2 4.41 SD-test packages

The requested software verification and packaging step is complete. These are
local hardware-test deliverables, not camera-accepted firmware. No camera was
connected. The wider hardware port remains unaccepted.

| Configuration | Exact ELF SHA256 | Sources / libraries / mods / words | Payload / link-region spare |
| --- | --- | --- | --- |
| Ordinary, stock Fn IMAGE SIZE | `2b0eb7506be88d6eafdf17dafb1e2abced2981187e79b30d5c794fcd332d3619` | 79 / 22 / 14 / 130 | 551864 / 5192 bytes |
| Separate USB debug, consumes Fn IMAGE SIZE | `6ae0688d90ef10b8c727da96af4469f927ba56bf2aed3a4f650abb884c3860b9` | 81 / 22 / 15 / 131 | 552496 / 4560 bytes |

The existing two-predicate lookup correction is unchanged. No firmware/mod
source, native runtime, transport model, instruction bound or API result was
changed during this final verification task. The ordinary and USB builds retain
their original separate configurations. Link-region spare is not proven camera
heap/stack or workload headroom.

## Existing evidence reused

The exact ordinary and USB numeric/function suites, WB84/2guards/7resets, original
Q/controls UI and typed codec, fresh binary reproduction and delivery checks were
already complete and were inspected rather than rerun. Function suites include
films356/identity99/three menus/six captions, NR43, JPEG33, WB import6,
custom-record SAVE49, callback8 and native stock-icon comparisons19950.
The original films report's bounded-isolation/native-lifetime limits remain.

Existing same-ELF REC pause/retry and source-bound mode/teardown reports were
reused. The mode assay loads the final six owners, then executes a pinned
isolated lifetime component: it does not establish whole-camera shutdown.
USB FAT recipe/reader-lifecycle/capture and both early-SD twelve-object icon
reports were also reused. No parent artifact's PASS was promoted to the new ELF.

## Missing exact-artifact evidence completed

- Ordinary native fresh-board restore from the already written/read merged
  SETTINGS document.
- USB genuine native merged SETTINGS commit/readback/fresh-board restore and
  native issue/refusal/callback retirement and post-capacity retry.
- Ordinary genuine FAT list/open/read/close, parser/publication, native UI and
  processing recipe admission; compaction, identity and nested still/live
  reader-retirement checks on this exact ELF.
- Both exact ELFs: nine native ASPECT dimension cases, SURROUND, stock detail
  equality, native MESSAGE18/type16 negative controls and wrong-owner cases;
  all nine control captions through actual native message consumers; thirty
  screen routes, fifteen stock controls and twelve visibility cases.

All six SETTINGS owners register/load. Five have selected nondefault values;
the unchanged default controls.function owner is intentionally omitted as an
empty section by the original writer. Native-produced bytes restore ETERNA,
DATE FOLDERS ON, FORMAT CARD NAME OFF, overlays OFF, ASPECT4:3, SURROUND LINE,
golden-ratio guideline and Fn1/Q NEXT FRAMING GUIDELINE. No successful API reply,
callback/status, ready/registration or VFP enable was supplied by the host.
Fresh-board restore uses no host settings decoder or selection setters.

The final audit `final-sd-software-audit-20261112/verification.json` validates
368 evidence/file pins and preserves 90 selected source snapshots locally.
It reconstructs ELF→region→delivered SD correspondence, checks current selected
source hashes and compares both independent builds' ELF/region/ffboot/ffsys
bytes. Checker history is preserved for the already completed settings assays;
a later Python dispatch-only adaptation does not relabel those closed runs.

Initial SDK/TCI attempts inside the sandbox terminated with signal132 before
functional evidence. Existing native engines then ran outside the sandbox.
Two Python adapter setup errors were corrected before native USB tests began;
their diagnostic logs are retained. No guest assertion was relaxed.

## Local deliverables

Under the project-root `artifacts/` directory:

- `xt2-441-full-ordinary-20261112-sdtest.zip`, 8857218 bytes,
  SHA256 `b0a06079a8f0398002a741a0627d3dcc0e19fa8a68a5a6f2e34273164c57bdf0`.
- `xt2-441-full-usb-debug-20261112-sdtest.zip`, 8861120 bytes,
  SHA256 `d66b800a2cabc502975392f26b1ff332ec332958c2b1c5c65bd64f78853b6936`.

Each has an unpacked sibling directory and eighteen files: exactly two SD-root
files under card/, SD-specific hashes, complete member hashes, Russian README,
staged hardware protocol/result template, build instructions, exact binaries,
source pins and final audit/correspondence diagnostics. No fixture recipes or
fixture SETTINGS document are installed on the test card by the package.
Every archive member was read back and compared; CRC, unique member names,
complete file coverage and deterministic byte-identical repacking pass. The
separate verification-only invocation passes without writing/rebuilding the
firmware. Receipt: `artifacts/xt2-441-final-sd-packages-20261112.json`.

## Boundaries retained

This is the selected implemented X-T20/XPP feature set, including the explicit
WB additional scope; it is not every metadata row. Unsupported providers,
F-Log/film-grain/HDMI-rec and the optional mutually exclusive legacy film UI are
not silently invented. Recipe support is initial startup loading; unselected
runtime editor/refresh/reload and optional controls.function direct-action
providers remain absent. Logical controls do not establish physical scanner
labels or optional ninth direct-action persistence.

The installed RAF→JPEG hook proves descriptor crop and ratio/pointer cleanup.
Developed source0 pixels, encoded JPEG/Exif output and a physical shot remain
absent. Full continuous capture epochs, physical concurrency/cache/DMA/load,
ROM→SD boot, display/GPU, NAND/C1–C7/power-cycle, physical USB protocol and
shutdown/recovery remain unverified. Both packages retain hardware_accepted=false.

Next hardware result: one ordinary-package SD startup to REC/menu without a
photo, recording hashes read from the card and the actual screen/control result.
Follow the included stages before single-JPEG/persistence/USB experiments.
Only original tooling and this note may be public; firmware-derived archives,
private upstream sources, raw native reports/traces and snapshots stay local.
