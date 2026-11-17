# X-T2 4.41 first-camera package: upstream comparison

The selected candidate is the complete ordinary Nov12 configuration, ELF
`2b0eb7506be88d6eafdf17dafb1e2abced2981187e79b30d5c794fcd332d3619`.
No feature or firmware code is changed for this packaging step. It remains
unverified on physical hardware. This is not a newly accepted firmware release.

## Findings against fresh upstream fixes

| Upstream finding | Exact local selection | Decision |
| --- | --- | --- |
| [5cecc2682c](https://github.com/justjake/x70view/commit/5cecc2682cb8ccc7bb2f4c308f9a41851b6b5a7d): timer dispatcher callback stack alignment | The final manifest and delivered ffboot already replace the dispatcher stack literal with the aligned value. Existing `build_full_timer_candidate.py` introduced it before this newer X-T2 report. Fresh `timer-fixed.json` runs the exact final ELF's production loader callback through native registration and dispatch. | Already covered; do not apply twice. |
| Same commit and [651d6109ee](https://github.com/justjake/x70view/commit/651d6109eeb2fafe24c6c65c9dd793f06ffe52a8): new release selection exceeds menu capacity | Our selected engine is a different pinned version with 24 entries, 16 values and 4 pages. The actual final selection is checked by native prepare, status zero, counts within capacity and entry/page table IDs disjoint (`menu.json`). | No expansion needed for this selection. Upstream's larger selection must not be imported without its matching capacities. |
| Same commits: HIDE FEATURES row has no SET-UP parent | Neither `lib/features/features.c` nor its `fm_features_*` declarations are selected in our 79-source image. | Not applicable. |
| [46c8e38ec6](https://github.com/justjake/x70view/commit/46c8e38ec612c8fe37b6b4536e5b5f43a74f45e0): choice records changed from two to three words | Our selected settings header and engine both use `{name,value}`. The exact-ELF date/volume and control-choice checks remain relevant; adding a third word to only one side would create the defect. | Keep matched ABI. |
| [87146874b1](https://github.com/justjake/x70view/commit/87146874b18f0168760369b2c36a9a649d1ac1ea): wrong X-T20 directory message codes on X-T2 | Selected cardio uses the existing X-T2 reference header with correct FIND_FIRST/NEXT codes. Exact-image FAT/recipe and SETTINGS commit/restore reports are in the Nov12 final audit. | Already covered. |
| [254c6b3daa](https://github.com/justjake/x70view/commit/254c6b3daa9c8dadcf0058ccbbb4455e77c93e8b): HIDE FEATURES relayout and BACK routing | HIDE FEATURES and SNAP FOCUS are not selected. | Not applicable. |
| [PR845](https://github.com/justjake/x70view/pull/845): Clarity L64px fix and SNAP FOCUS limitations | Clarity, Color Chrome and Snap Focus are not selected. | No new effects in first-camera package. |
| [PR861](https://github.com/justjake/x70view/pull/861): stored film values18/19 | Experimental alternative to card-films, with explicit stock C1–C7 recall tests outstanding and no author camera run. Our current processing/storage composition is retained. | Do not substitute this alternative. |
| [Nov17 SD boot v2 announcement](https://discord.com/channels/939580734140719214/1565483015973507092/1572189087065047153) | X-T20 author report; not a verified replacement for our exact X-T2 delivery chain. | Retain matched ffboot/ffsys pair. |

Sources were inspected through the connected GitHub tools on Nov17. These are
comparison decisions about the selected package, not independent reproduction
of the upstream authors' physical-camera results. No new upstream source change
is incorporated; the package retains the original firmware-derived binaries.

## Evidence and delivery

`first-camera-preflight-20261117/timer-fixed.json` and `menu.json` must both
pass for the exact ordinary ELF before the new packager runs. Timer checks
native callback entry alignment and stack sentinels; the menu check executes
the real selected menu prepare and checks actual occupancy. Their initialized
UI/mode inputs do not establish whole ROM boot, scheduled task/IRQ behavior,
physical keys, display, workload or shutdown safety.

The new packager verifies all79 selected source hashes and every old package
member hash, preserves all original18 deliverables, adds first-pass instructions
and preflight evidence, then reads back every ZIP member and validates CRC.
Both SD files and the ELF/region remain byte-identical to the Nov12 package.
The package receipt records its final ZIP hash; no card has been written.

Read START-HERE.txt first. The first pass is only REC/menu and stock reboot,
without shooting or changing settings. The existing staged HARDWARE-CHECK.txt
remains for subsequent tests after that pass succeeds. A camera-specific full
backup and demonstrated recovery remain physical prerequisites to establish;
another owner's successful backup is not our backup or recovery proof.
