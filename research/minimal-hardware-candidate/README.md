# Fixed ETERNA / SEPIA: narrowed parameter reads and safety limits

Original code and research developed with OpenAI Codex assistance. Current scope is fixed X-H1 2.15 ETERNA replacing SEPIA on X-T2 4.41. No additional slot, profile file loader or live replacement is required.

The current local image is `47a9376657501fec7805c0fa17b958dea2b100bfc13652d764a7b73401723751` (46,505,984 bytes). It supersedes the previous `0f142449...` candidate; the previous ZIP is retained locally as legacy. No new ZIP was produced.

## Concrete changes

- Removed two experimental presentation-record replacements and embedded captions. All stock menu records/icons/labels stay intact: select **SEPIA**.
- Removed the global parameter-reader hook. Only 18 checked direct calls in the known color functions now use private byte/halfword/signed-halfword readers. Misses call the original reader; the general parameter entry and shared scalar wrappers remain byte-identical to stock. This is callsite isolation, not a new global current-profile flag or a task-scope framework.
- The builder verifies each original call target and independent fixed write bounds. Its checks are not merely an allowlist derived from its own emitted writes.
- The SD-test directory contains only the two boot files plus local notes/manifest. The builder no longer includes an update DAT; the integrity gate rejects any `.dat` in this directory. The official DAT remains a pinned local reference. This removes an avoidable updater input, not the firmware's ability to write flash.

## Verification

The exact current image passed 1,350 tone/gain cases, 90 aggregate checks, 15 development checks and 120 matrix/four-coefficient cases. ETERNA outputs match X-H1 in the declared contexts; 14 other supported profiles preserve tested results. Each of 145 overridden/sample keys was checked twice: private reader behavior and original stock behavior through the shared reader. Three stock menus still commit/read back public ID5 and live value5 with explicit settings-snapshot/synchronization fixtures; the capture/development producer handoffs remain unproved.

All 1,036,469 observed CPU stores during these numeric/selector checks stayed within declared laboratory context/output/stack RAM. No MMIO or flash devices were modeled successful. This bounds these calls; it does not monitor DMA or the full boot/capture pipeline. These checks were repeated because parameter routing and safety instrumentation changed, not to repackage previous results.

## What is not implemented or established

There is **no global internal-flash write inhibition** and no boot-time integrity gate/automatic stock fallback if the carrier is overwritten. The native storage/updater paths remain present. Earlier synthetic erased-store execution reached native page programming and sector erasure; this is a counterexample to calling SD boot read-only, not a physical observation on this candidate.

Original ROM transfer, carrier lifetime, continuous native UI-to-capture/development propagation, sensor/ISP/JPEG behavior, reboot and card-removal recovery remain unverified. Low loader, inspected flash-driver region and shared parameter readers are unchanged; unchanged bytes do not prove unreachable flash writers or overall hardware safety. No zero-brick guarantee or ready-for-camera safety certification is claimed.

The external [X-T2 stock SD boot report](https://github.com/justjake/fujimod/pull/163) supports the boot method, not this patch. FujiMod's [recovery procedure](https://www.fujimod.com/recovery/) explicitly includes a separate flashing step; recovery has not been demonstrated on our setup. Use [the revised hardware notes](HARDWARE-CHECK.txt) only after accepting these limits. Keep DAT files off the experiment card, and do not enter firmware update mode.

## Original source / local inputs

The adjacent standard-library integrity gate is runnable with locally supplied inputs:

```sh
python3 audit_eterna_minimal_package.py /path/to/eterna-minimal-sd-candidate /path/to/stock/ffboot.bin
```

The candidate needs `ffboot.bin`, `ffsys.bin` and its private `manifest.json`; the stock directory must also supply the original `FWUP0010.DAT` reference. No firmware, coefficients, raw manifest or copied firmware instructions are published.

The adjacent numeric verifier is original source for inspection, not a standalone build. In the complete workspace it needs the updated local minimal builder/private-read integration, shared parameter overlay installer, profile/table/development/aggregate helpers, locally extracted X-T2/X-H1 inputs, prior measured dependency reports and Capstone/Unicorn TCI. The private scalar wrappers are constructed from locally supplied stock instructions and are deliberately excluded here. Local command:

```sh
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_eterna_minimal_sd.py
```
