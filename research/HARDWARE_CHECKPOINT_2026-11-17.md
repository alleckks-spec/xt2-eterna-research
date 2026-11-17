# X-T2 4.41: first physical-camera checkpoint, 2026-11-17

The owner tested the ordinary SD package on a physical X-T2 running stock4.41.
A supplied photo shows ETERNA selected in the Russian FILM SIMULATION menu,
FujiMod overlay and repeated STD icons. Remaining results are owner reports.

Confirmed on the camera:
- SD startup and accessible menus/basic controls.
- Added film profiles visible; selecting ETERNA works and agrees with Q.
- ETERNA remains selected after shutdown and a subsequent SD startup.
- Normal startup without the test SD works and selects stock PROVIA.
- ULTRAFINE is visible; selection survives menu reopening.

Known problems:
- Several added-film icon/caption surfaces say STD/Standard rather than the film name.
- Mods reportedly disappear after several minutes idle. Sleep versus automatic
  power-off/restart has not been isolated. Disabling AUTO POWER OFF is a proposed
  temporary workaround, not a verified fix.
- An SD-start key combination used without a card was followed by an apparently
  unresponsive normal startup; removing/reinserting the battery restored operation.
  The cause and reproducibility are unknown.

No lens was available: no photos, color accuracy, JPEG/Exif output, AF or capture
stability claims. NR extras, C1-C7 persistence, complete control remapping and
physical USB remain unqualified. The guideline test was deferred because the
owner could not find the suggested menu. No overall hardware acceptance claim.

The tested card was128GB, formatted on macOS as FAT32/MBR with32KiB clusters.
This documents this card's successful startup, not proof that exFAT cannot boot.

Exact ordinary ELF:
`2b0eb7506be88d6eafdf17dafb1e2abced2981187e79b30d5c794fcd332d3619`

Exact delivered ffboot.bin:
`a61bc81e7cac2e6d4bafb48221163caf88d09538bfb0a5de03a9d31063e22ad4`

Exact delivered ffsys.bin:
`b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351`

Local package SHA256:
`12da074271b0d8cb0a55ec364016c4baa46f79697fd6a75e508cac5d32b9480d`

Firmware-derived binaries and private upstream inputs are not redistributed.
Original tooling in this repository requires the documented local inputs; the
public clone is not a self-contained build environment or installable release.

This port builds on FujiMod/X-T20 and FujiHack community research. Development
and checks were assisted by OpenAI Codex. Upstream credit remains in the existing
research notes. Next: correct labels, isolate idle/power behavior, then capture
comparisons once a lens is available. Existing source/build checks do not replace
those physical tests.
