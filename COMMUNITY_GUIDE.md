# X-T2 developer findings worth reusing

Updated 12 November 2026. Target: Fujifilm X-T2 firmware 4.41.

We do not have access to a physical X-T2. This is an index of software-tested
findings, original adapters and regression tools from an ongoing FujiMod port.
There is no camera-tested firmware release here. The useful contribution is a
set of concrete failure cases and model differences that other developers can
review before repeating the same work.

## Start with these findings

| Finding | Evidence in this project | Useful to |
| --- | --- | --- |
| UI post packet is larger on X-T2 | A 52-byte donor packet overruns its source boundary; a 76-byte packet passes the native copy check | XPP menu and UI ports |
| Directory failure can look like a successful empty catalog | Native handler error is reproduced; only normal end/no-match is normalized | Card-file loaders and error handling |
| Timer restart can leave the old timer alive | Original leak and cancellation refusal are reproduced; corrected wrapper retains ownership correctly | XPP timer wrapper users |
| An inline callback can disappear during request issue | Native SDK fault/control pair reproduces a stranded job; recorded delivery retires it and permits caller retry | Asynchronous storage adapters |
| Cancelling WB import can revive stale metadata | Primary-only invalidation fails; invalidating both active and shadow records passes | Custom-record and WB ports |
| SETTINGS can be written and recovered in the software board | Native timer/task/storage chain writes JSON; an independent fresh board restores it | Developers checking settings integration |

These rows refer to separate pinned artifacts. They are not a single combined
camera result, and a passing check is not a general proof of firmware safety.

## UI packet extent

The X-T20 source packet is 52 bytes. The reviewed X-T2 transport copies
68 payload bytes after an 8-byte header, requiring 76 bytes total. Reusing the
donor stack structure causes a 24-byte source overread on this path.

The boundary regression places the source at the end of mapped memory: the
old extent faults, while the corrected extent passes with the destination
canary intact. It stops before queue submission. A separate transport check
covers callback delivery in a borrowed native UI context.

- [Finding, local inputs and copy-only command](research/fujimod-port/UI_POST_ABI.md)
- [Original layout reference](research/fujimod-port/xt2_ui_post_message_reference.h)
- [Extent adapter](research/fujimod-port/prepare_ui_post_message.py)
- [Boundary verifier](research/fujimod-port/verify_ui_post_message_abi.py)
- [Separate transport evidence](research/fujimod-port/UI_POST_TRANSPORT.md)

This is an X-T2 model difference, not a universal XPP packet size.

## Directory errors and request ownership

The previous listing callback treated every nonzero result as normal end of
directory. A real native error could therefore produce a successful empty or
partial catalog. The X-T2 adapter preserves errors and normalizes only native
end/no-match status 6. The native status-mapping assay covers 39 internal
statuses for each of two commands, or 78 mappings.

The native worker reaches the compiled callback. Positive directory records
still use explicit post-FAT fixtures; these tests do not establish a mounted
physical card. The related listing work also covers late callbacks and
serialization around the existing single directory cursor.

- [Native callback cases and exact boundary](research/fujimod-port/CARDIO_NATIVE_CALLBACK.md)
- [Original status reference](research/fujimod-port/xt2_cardio_status_reference.h)
- [Status adapter](research/fujimod-port/prepare_cardio_status.py)
- [Native worker verifier](research/fujimod-port/verify_cardio_native_worker.py)
- [Listing ownership and late callbacks](research/fujimod-port/CARDIO_LISTING.md)

## Timer restart and callback alignment

The timer restart regression reproduces an old periodic handle firing after a
restart and after cleanup of its replacement. The adapter cancels before
restarting; a cancellation refusal preserves the old handle and running state
rather than claiming successful cleanup. The check uses explicit native tick
calls, not elapsed camera time or concurrent shutdown.

- [Restart counterexample and fixed contract](research/fujimod-port/TIMER_RESTART.md)
- [Original restart adapter](research/fujimod-port/prepare_timer_restart.py)
- [Restart verifier](research/fujimod-port/verify_timer_restart.py)

A separate production-callback regression checks the X-T2 native dispatcher
stack: original entry is 4 modulo 8, corrected entry is 0 modulo 8, with outer
stack and sentinels preserved. This is an X-T2 adaptation of the shared
dispatcher-stack method, with the upstream authors credited in
[FULL_TIMER.md](research/fujimod-port/FULL_TIMER.md). It is not a new discovery
of the general XPP issue. See the
[dispatcher verifier](research/fujimod-port/verify_full_timer_dispatch.py).

## Inline storage completion

On the original eight-mod composition, an open callback immediately issued a
read while its callback bank was still running. A native synchronous read
refusal then tried to claim that bank, was treated as stale and disappeared.
The recorded result was a busy job with an open handle and no outstanding
callback.

The X-T2 backport of the existing PR471 recorded-delivery mechanism separates
recording from callback-body execution through the existing poll. Under the
same transient fault it reports failure, closes, retires resources and permits
one explicit successful caller retry. This does not establish automatic
recovery of lost queue requests or a permanently refused close.

The shared mechanism is credited to Taylor Chapman (heytchap) and Claude
(Anthropic); our contribution here is the X-T2 adaptation and native regression.

- [Counterexample, fixed artifact and remaining limits](research/fujimod-port/CARDIO_TASK_ISSUE.md)
- [Adaptation of the pinned mechanism](research/fujimod-port/prepare_cardio_task_issue.py)
- [Recorded-delivery verifier](research/fujimod-port/verify_cardio_recorded_delivery.py)
- [Integration verifier](research/fujimod-port/verify_cardio_task_issue_integration.py)

## WB import cancellation and stock serialization

X-T20 custom-record offsets cannot simply be copied to X-T2: existing X-T2
writers occupy them. The reviewed X-T2 extension was checked through native
SAVE, cache, recall, edit and import paths.

A useful negative control is import followed by bank cancellation: clearing
only the primary marker lets the native shadow revive stale WB metadata.
Invalidating both active and shadow markers prevents that in the tested
seven-record paths. Six import formats cover 42 slot copies; the exact fixed
WB artifact also passes 84 SAVE/cache/reload/recall/edit chains.

- [WB ownership, counterexample and limits](research/fujimod-port/WB_SHIFT.md)
- [Import lifecycle verifier](research/fujimod-port/verify_wb_import_lifecycle.py)
- [Recall/edit lifecycle verifier](research/fujimod-port/verify_wb_recall_edit_lifecycle.py)

The separate custom-record film serializer check covers exactly seven records
and 49 choice/record combinations. It verifies stock film values at the native
journal-descriptor boundary and stops before journal transport. It does not
prove NAND persistence or independent extra-film recall in C1-C7. An earlier
eight-block fixture was corrected because its eighth block was UI/backup memory.

- [Serialization evidence and fixture correction](research/fujimod-port/CUSTOM_SLOT_FILM.md)
- [Serializer verifier](research/fujimod-port/verify_custom_slot_film_serialization.py)

## Native settings write and independent recovery

The native SDK chain executes real timer/IRQ/task and file-worker code to write
166 bytes of named ETERNA settings, read them back and retire resources. An
independent fresh software board receives that file through the existing SDK
FAT32 formatter and restores the choice through native reads and the linked
decoder, without a selection setter or host settings decoder.

The software board still supplies its declared environment and inputs. This is
not physical SD retention, a camera power cycle, complete ROM-to-UI startup,
sensor development or an encoded JPEG.

- [Exact prerequisites, artifact and boundaries](research/fujimod-port/NATIVE_SETTINGS_PERSISTENCE.md)
- [Native write/readback probe](research/fujimod-port/probe_sdk_native_fs_settings_commit.py)
- [Independent restore probe](research/fujimod-port/probe_sdk_native_fs_settings_restore.py)

## What can be reproduced from this repository

The notes, failure mechanisms and small layout/status reference headers can be
reviewed directly. Most execution tools require authorized local firmware,
pinned upstream sources, built ELF inputs and earlier workspace helpers.
**A public clone alone is not a complete build or test environment.**

Each linked note describes its own inputs and boundaries. Follow that note
rather than treating script names as a standalone installation sequence.
Common requirements include Python, pyelftools, Capstone, an operational
ARM Unicorn or the existing FujiMod SDK, and the appropriate Arm toolchain.
Some wrappers intentionally depend on private-input transformers that are not
distributed here.

To reproduce a result:

1. Select one finding and its pinned artifact; obtain its inputs lawfully.
2. Match the firmware, upstream and checker hashes in that finding's note.
3. Run the original/fixed controls where provided and retain all failures.
4. Record the exact tested ELF, supplied boundaries and remaining gaps.
5. Requalify affected paths after changing the composition or target body.

A green verifier exit can mean a documented counterexample was reproduced.
Read its assertions and scope, not just its exit code.

## Scope and attribution

The current direction is adapting existing FujiMod/X-T20 work to X-T2 4.41.
The older standalone Sepia-to-ETERNA experiments remain historical research.
No camera boot, real photograph, color-equivalence claim or hardware acceptance
is established by this index. The aspect/capture work is still a descriptor
boundary, not an image-output result.

This project and these notes are AI-assisted using OpenAI Codex. Existing
FujiMod/X-T20 modules and the upstream authors' mechanisms retain their credit;
our X-T2 qualification does not make those modules original work of this project.
Check the applicable licenses and provenance before copying or submitting code.

No firmware images, installable SD packages, extracted coefficient tables,
disassembly corpus, private upstream sources or community chat logs are included
in this publication.

For collaboration, start with a focused source review or reproduction of one
listed case. Useful reports identify the body/firmware, exact artifact,
supplied test boundaries and observed mismatch. Please do not treat this index
as a request to install an experimental image on a camera.

