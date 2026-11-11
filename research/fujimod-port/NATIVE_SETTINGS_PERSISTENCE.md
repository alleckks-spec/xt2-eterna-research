# Native settings commit, SD-fixture write and fresh-board restore — November 12, 2026

Completed software chain on exact menu ELF
`892f6d3b5cafb9ac86c4f32e9a625220d58593a7b2c7c6310fcf739c46fe482e`:
actual native bank checkpoint/cancel/commit → real periodic settings callback →
original async storage workers → create/write/count/close → read/compare →
fresh independent board restore without a selection setter.

Canonical original checkers and local evidence:

- `probe_sdk_native_fs_settings_commit.py`;
  `sdk-native-fs-settings-commit-unverified/probe.json` and `freeze.json`.
- `probe_sdk_native_fs_settings_restore.py`;
  `sdk-native-fs-settings-restore-unverified/probe.json` and `freeze.json`.
- Native-generated166-byte JSON:
  `sdk-native-fs-settings-commit-unverified/settings-readback.json`, SHA256
  `82daddf400b7e2dcb6db80d61c4d67a059c25286f291a243bb889cf2e566316c`.

Older reports, source/checkpoint freezes and packages are preserved. The
intermediate declared linked-change notification probe is superseded for the
native commit/cancel claim by the final checker above.

## Verified behavior

The first nativeB51088→BBC924 checkpoint records the original choice0.
Native setter154B700 previews key33; native restore1 returns key0 without
requesting a save. Native setter32 followed by checkpoint0 commits ETERNA,
requesting generation1. Repeating checkpoint0 keeps generation1.

Real timer8→IRQ56→CE0198→native task34/CE02E8→CDF968 executes exact linked
settings tick13833DC. Original SDK storage workers and the linked cardio
callbacks complete the166-byte `FUJIMOD\SETTINGS.JSN` write. Owner
requested=completed1/failed0. Original async read then reads back the JSON
`stock_choices.current.values=[{setting:film_simulation,value:eterna}]`.
After native restore1 the committed key remains32 and requested remains1.
Final native open-count0, four callback banksFREE, active/hold/callbacks0.

A separate fresh board receives those exact166bytes through the existing SDK
FAT32 formatter, not through a substituted file API. Native policy/timers,
original file reads and the linked decoder restore key32; restored-count1,
owner registered2, requested=completed=failed0, callbacks/open-count0.
There are no selection setters or host decoder calls in this restore run.
The file stores a named mod choice, not a nonstandard internal firmware film
code. This does not extend the separate C1–C7 serialization proof.

## Actual prerequisites retained

The same existing SDK two-cortex-a7 board and SD node are used, revision
944d5c865d4def32663c1dad24d54ac3001f3f6e, native extension SHA256
6666b9fab6f832c966a1deef6a33df47a578349a2cbf566b373ced9fd2025d0e.
Stock SHA256 is
fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2.

Native boot exception-stack/VBAR prefix, lazy VFP registration, kernel-list
constructor41E50, first dispatch400C8, UI1 and full root-start5593C precede
storage. Native mount command969348 owns E000000/1MiB, constructs SDK context
and derives lower workspace through96C0B0; it runs mount96BF88 and966CFC.
Native callbacks and registration stores execute; no host ready/context,
registration or VFP-enable writes are supplied.

The existing SD node uses4GiB FAT32, partitionLBA2048,64-sector clusters,
IRQ83/reset-channel0, unchanged transfer10/clock2/reset3. Original native DMA
and cross-core cache maintenance execute. Existing DriverHarness parking
alternates cores with10000instruction and10000guest-tick caps; no new scheduler
or device model. The guest-tick cap bounds WFI windows, not SD transfer timing.
Actual caller-derived cache pools remain within the unchanged1MiB buffer:
8192×4,dataE023578..E02B578 and16384×2,dataE02B5CC..E0335CC. No extra56bytes
are mapped to satisfy the constructor's raw budget endpoint.

The periodic wire is qualified from native initialization: logical43 maps to
physical timer8; its SDK interrupt maps toIRQ56. Earlier fixture only wired
kernel timer15→IRQ63, so it could not deliver settings timers. Both routes now
use the existing timer node; native timer task/callback registration executes.
No ticks, callbacks, successful API replies or worker frames are injected.

## Limits and next step

Native bank snapshot/restore calls are explicit checkpoint inputs. Physical
MENU/OK/BACK event mapping and a complete rendered UI/ROM boot remain open.
Fresh-board restore is software-fixture initialization, not a physical SD
power-cycle or camera test. Real MMU/cache coherency, SD persistence after
power loss, capture-time contention and hardware timing remain unverified.

The next software integration is to reuse these genuine mounted-board
prerequisites for the current full composition's remaining settings owners and
menu-open/capture admission interactions. Preserve the existing failure,
retry, cancellation and retirement reports; this positive chain does not
replace them or prove full-port completion.

## Publication scope

Publish the two final original Python checkers and this note; optionally the
original native roundtrip checker/note as a separate bounded milestone. The
small generated settings JSON is an original test document and may serve as a
fixture. Do not publish firmware, ELF/region/SD binaries, raw probe reports,
extracted tables/disassembly, private upstream source, or exploratory logs.
