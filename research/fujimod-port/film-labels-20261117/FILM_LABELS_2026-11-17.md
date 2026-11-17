# Six profile captions: software-checked camera-test build

The added film names already existed, but all six labels left their icon,
Q tile and menu badge fields zero, retaining PROVIA's STD artwork. A second
X-T2-specific issue was confirmed by native record reads: Q consumes word 0,
whereas the transferred binding selected word 4.

The experimental builder replaces exactly two of the baseline's 79 sources:
private copies of the film labels and film binding. It supplies 18 original
GVFF resources (150x42 menu badges, 36x36 pickers, 80x48 Q tiles), selects Q word
0 and keeps existing text/descriptions. Classic Neg., Bleach Bypass, Nostalgic
Neg. and REALA ACE retain `(approx.)` in text and `APPROX.` in artwork.
No private source, extracted graphics or vendor coefficients are released.

The other 77 source hashes, all six recipe byte arrays, the text section size,
20 prior mod icon IDs and the 130 stock patch sites/preimages are unchanged.
No idle/power-transition fix is included. Frozen main/stable branches, checkpoint
inputs and the Nov12/Nov17 tested packages are not rewritten.

## Exact candidate and software checks

- ELF SHA256: `acff8de426d856b99cb3a845dc64d11f66eb7979adf12955d6f5d6b93067ae85`.
- `ffboot.bin`: `431f47fe3c1c91215d19027996bb7c7d5142a8601b3da13b1eefd074c6992e1a`.
- `ffsys.bin`: `b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351`.
- All six profiles across menu/Fn/Q: 18 cases, native icon/resource readers,
  actual Fn lookup, native cursor moves both ways and 198 extra-to-stock returns.
  Stock records remain byte-identical; choice/row status remains zero.
- Native delivered-SD reservation/BSS/heap checks pass: payload preserved,
  prefix/suffix zeroed and crossing allocation refused. Map operands observed;
  installed MMU state and full boot are not proved.
- Native menu: 19/24 entries, 2/4 pages, status zero, table IDs disjoint.
- Exact-image timer: callback stack aligned, native dedicated-stack sentinels intact.
- ELF -> resident payload -> SD equality and all 130 applied words pass.
- All 18 original glyph vectors round-trip through the existing parser and have
  been visually inspected with the host Cairo renderer. This is host geometry
  evidence, not the camera's raster/display result.

The first measured link exceeded the previous region by 9,912 bytes. Existing
measured-map rounding adds one 32KiB granule: reservation 589,824 bytes, payload
566,968 bytes, headroom 22,856 bytes. The original upper boundary stays fixed.
The existing delivered-SD memory assay checks this exact new allocation.

## Owner-local package and next hardware step

`artifacts/xt2-441-ui-labels-20261117-camera-test.zip`, 8,562,975 bytes,
SHA256 `0461342293c0ac62c90f40a12e235547bc4a340634e43c94598fbb6bbf18e94f`.
Every archive member was CRC checked and compared with its staged file.
The package includes both SD files, Russian instructions, checksums, software
reports and an explicitly unaccepted camera result form. No SD card was written.

Hardware status for this candidate: **not tested**. The earlier startup/menu/
persistence reports apply to the frozen baseline, not this ELF. Next: on the
prepared FAT32 card, test all six names in menu, assigned Fn and Q, retain the
four approximation markers, return to PROVIA/other stock choices, then verify
ordinary stock startup without the test SD. Follow the package instructions.
No capture, color accuracy, JPEG/Exif, continuous workload or broad hardware
stability acceptance. Idle loss remains unresolved and outside this change.

## Reproduction

Use the owner's complete local workspace on experimental/*, including pinned
private inputs/SDK and GNU 13.2.Rel1. These original scripts belong in
development/xt2-firmware-lab/tools. This public source is not a standalone
firmware distribution. The builder uses fresh private input/output directories
and shadow metadata; it never rewrites the selected baseline sources/target.

First build without growth to preserve a measured failed map. Then build with
new input/output directories and `--grow-from-map <first>/failed-mods.map`.
`--toolchain-bin` may select a local copy of the same pinned GNU tools; normal
per-stage hash verification remains active. The verified official archive used
here has SHA256 `39c44f8af42695b7b871df42e346c09fee670ea8dfc11f17083e296ea2b0d279`.

Run verify_film_labels.py plus the existing native memory/menu/timer and SD
correspondence checks on that exact ELF. package_film_labels.py requires all
those passes, rechecks scope/recipe/icon IDs and source/SD hashes, rejects the
old baseline and verifies every ZIP member. It never accepts a camera result.

Local build: ports/fujimod-xt2/experimental/ui-labels-20261117-v8-build.
Earlier v1-v7 preparation/measurement failures remain separate and unqualified.
The iCloud input-read delays were an environment issue; they are not camera or
firmware failures. No community message is sent as part of this work.
