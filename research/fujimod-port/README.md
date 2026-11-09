# FujiMod X-T20 → X-T2 adaptation

AI-assisted independent port work, targeting X-T2 firmware 4.41. The current
objective is to adapt the existing FujiMod/X-T20 modules through their ordinary
XPP builder and recovery composer. The earlier standalone Sepia replacement is
historical research, not the current implementation plan.

## Current candidate: corrected timer ownership

The same three ordinary mods now include one corrected XPP timer source. Active
restart cancels the old native handle; cancellation failure keeps `running` set,
propagates through lifetime cleanup and prevents a replacement start. The old
ELF reproduces3callbacks after cleanup; the new ELF produces0. Native10ms
one-shot/300ms periodic behavior also passes using explicit logical tick calls.
This borrows a scheduled UI1 context, not an actual running timer task or IRQ.

New common ELF SHA-256:
`06ab09771172acde5d7e330066ad4f8679083a751767f80701d225ee5e43b85d`.
Footprint148,944 /196,608 (+32bytes), same23C/13libraries/63delivery edits.
Exact artifact passes33 JPEG,356film+99identity,3film lists/6captions, NR43/3
and ELF→SD correspondence. No camera or whole service/startup qualification.
[Original adaptation, builder, checker and dependency/evidence limits](TIMER_RESTART.md).

## Existing loader: parser and native retry

The existing film loader now builds with its actual parser/schema/publisher and the X-T2 cardio/timer adapters. A shared-parser XPP icon-reference compile failure is corrected using the existing XPP constants. Three parser cases and the native timer → directory error → loader failure → ten-tick retry chain pass in a separate component. Scratch stacks, explicit REC/device fixtures and native logical tick calls are not timer-task scheduling or mounted FAT; card rows/mutable processing and the common SD remain unchanged. [Original tools, executed chain and exact limits](FILM_LOADER_COMPONENT.md).

## Separate components: directory listing and UI callback queue

The directory component now preserves native listing/readiness errors instead of
accepting failed I/O as an empty or partial catalog. Native handler-driven error
callbacks, eight bounded100-byte details-writer cases and all78 status mappings
pass; only end/no-match6 becomes successful completion. The actual semaphore
bootstrap loop makes the initial wait pass, while worker entries and positive
FAT frames remain harness-invoked. Mounted FAT, scheduled task ownership and full
loader/mutable integration remain open; the common SD candidate is unchanged.
[Original status adapter and native callback/details evidence](CARDIO_NATIVE_CALLBACK.md);
[prior transport/bank/hold adaptation](CARDIO_LISTING.md).

The X-T2 active UI transport needs68 payload bytes (76-byte packet), where the
X-T20 source provides44 (52-byte packet). The adapted original queue now passes
18 callbacks through native kernel transport in a borrowed native-scheduled UI1
context,16-slot saturation, stale-generation rejection and one coalesced native
UILIB redraw submission. Native registration/queue creation/scheduling execute
without internal stubs. This is an isolated Clang-built component; the common
ordinary SD package is unchanged. Full UI loop/rendering, global event collision,
custom pages and card storage/mutable lifetime remain open.
[Original builder/checker and precise limits](UI_POST_TRANSPORT.md);
[earlier packet-copy ABI evidence](UI_POST_ABI.md).

## Earlier common candidate: six films, NR and JPEG Max

The original JPEG Max XPP module is now the third ordinary mod. Only its quality
property and target/menu bindings change. The new common ELF passes 33 native
JPEG selection/table cases, the reused 356 film + 99 identity cases, three film
lists/six caption boundaries, and NR43/3. All 63 ELF/region/SD edits match.
Footprint is 148,912 / 196,608 bytes (+3,824). Exact ELF SHA-256:
`8bea01979955b1e751643cb1201975adc553e9efe2eafa5ef327fdc990c013eb`.

On that same ELF, a further check runs five native caller/setup prefixes and 15
first submissions. Native code creates tag/kind/attempts and sets index; only
the two selected primary requests receive scale16. The worker header and geometry
are declared fixtures, and execution stops before the encoder. Request fields
are not host-supplied. Full capture/worker/retry/encoder/overlay/service lifecycle
and camera remain unqualified, as does the whole film-context lifecycle.
[Exact artifacts, evidence, original tools and dependencies](JPEG_TABLES.md).

## Previous context-bound candidate — native lifecycle OPEN

The reproduced cross-context mixing is fixed in the new X-T2-specific adapter:
after constructing ETERNA context A and Classic Neg. context B, A retains its
ETERNA output. Six retained contexts preserve all eight checked outputs after
later stock construction. Identity is stored as an immutable index and two
marker bytes at +145..147 within the inspected 0x148-byte processing class.
Only two verified native mapper return sites permit that write; byte-only foreign
calls and malformed identity data stay stock. The global diagnostic is not a
recipe source. This adds 120 resident bytes, with no side table, allocator,
service, loader or emulator.

Exact ELF SHA-256:
`0758d9955992eb3073785997229a8032dcd73df0783549a90a792d4c07f271ae`.
SD boot SHA-256:
`a444dabba10a5d38185beccbf35c8de5b8bfaae5b3c9ea84343181378f501b70`.
Footprint is 145,088 / 196,608 reserved bytes. The same two mods, 12 libraries,
21 C files and 54 delivery edits remain selected.

The exact artifact passes all previous 356 processing/guard cases, three film
lists and six caption boundaries, plus **99 identity checks**: six retained
contexts, original full-size memcpy, the second real mapper caller block,
native clear/write extents with canaries, unqualified byte-only calls,
invalid-marker fallback and independent reset. The same ELF separately passes
43 NR cases and three NR menu bindings. ELF→region→SD, all 54 words and both SD
hashes match. These remain bounded functions with supplied configuration and
transport, not continuous capture or an actual scheduler-overlap observation.

`xt2_context_recipe_reference.h` publishes only our original lookup and
qualified-writer logic. Its exact bodies match those inlined in the tested
private C; the header is a review/reference excerpt, not an additional linked
unit. ARM32 Clang syntax was checked against the locally supplied upstream type
header. Private upstream group handlers, generators, coefficients, hook records
and original firmware instructions are excluded. It requires that local type
header (six immutable recipes, no card films), existing selector/diagnostics and
the unchanged XPP hook ABI. Do not add the header alongside identical inlined
definitions. `verify_context_films_candidate.py` explicitly selects this
artifact through the reused parameterized case engine.

**The native-lifetime gate is still OPEN.** The original base initializer clears
exactly 0x148 bytes; the automated case checks that extent and adjacent canaries.
The inspected native constructor's final named field is byte +144. The tag and
borrowed caller/copy cases do not prove every other native writer, every real
capture copy or global padding ownership. No custom settings/C1-C7/flash bytes
were assigned. The entire native aggregate constructor still reaches a parameter
read at key/index1a3d40 outside the supplied processing-calibration window.
Unrelated flat RAM/firmware bytes or invented ready values were not substituted.
Complete producer/service/storage startup, mutable/card films, WB, full boot and
hardware remain unfinished. Neither native X100VI color equivalence nor camera
acceptance is claimed. The private candidate remains `accepted=false`.

The older counterexample and candidates below are preserved as history. In the
shared case engine the default still checks the old shared-latch artifact;
the new wrapper enables the context-identity expectations. Its reports distinguish
bounded isolation success from the remaining native-lifetime requirement.

## Earlier six-film experiment — original shared-latch counterexample

All six original built-ins now compile and execute in a separate ordinary
two-mod candidate: ETERNA, Classic Neg., Bleach Bypass, Nostalgic Neg., REALA ACE
and Neutral. The original recipe initializer is unchanged. Model adaptations
include the two live/still RGB hooks, existing X-T2 scale/gain/forced-curve fixes,
six choice rows/stable names/captions, and the existing chroma caller temporary
carrying a validated immutable recipe pointer. Card/mutable films are still absent.

Exact ELF SHA-256:
`9c0ed58d1b0aa13b8fbd90218f4a83277aa8300a236e6533a3573993b28f5cb7`.
SD boot SHA-256:
`2cff74c9e478aa84c5e2783c03ac7132f7a647fecfe824e2d635b2045727d109`.
Footprint is 144,968 / 196,608 reserved bytes, with 54 edits. ELF→region→SD
correspondence, all edited words and both SD file hashes are checked.

The exact new artifact passes 356 bounded output/guard cases: all stock IDs,
six original recipe substitutions, ETERNA comparison with the earlier qualified
ELF and 54 gain rows, stock fallback, scale and special/forced branches. Both RGB
entries and all ten processing thunks execute. Six keys are reachable and applied
through native cursor/property calls in three lists (15/15/21 rows), and six Fn
records pass through the actual caption thunk with type/style restoration.
Caption objects are supplied; this is not full rendering or screen evidence.
The same ELF also passes three NR menu bindings and 43 register/guard cases.

**The original shared-latch contract is still unqualified.** A supplied sequence
constructs ETERNA context A, reads its matrix, constructs Classic Neg. context B,
then reads A again. A's slot remains 9, but its matrix changes to B's recipe.
This demonstrates a missing context-isolation contract, not observed camera
task overlap. Native enclosing serialization or a specific identity adapter
remains necessary. No generic reload/runtime architecture was introduced.

The adjacent context byte +0x54 is stock-owned: a constructor writes it and
original chroma, luma and matrix functions read it. Four positive accesses are
checked by the original `audit_processing_recipe_byte.py`; this makes no claim
that another byte is free. No recipe-ID byte has been assigned.

`verify_six_films_candidate.py` records both functional checks and the explicit
counterexample. Its successful exit means the stated cases and known failure
were reproduced, **not** that the open gate passed. It uses the same supplied
mode/calibration/RAM, manual enrollment, uncontended transport and borrowed
chroma-frame boundaries as the existing assays. Separate processing contexts
are not a continuous producer. No native X100VI color comparison, service
startup/storage, full boot, image quality or hardware acceptance is claimed.
The earlier one-film baseline remains preserved and is not relabeled as a
complete port.

The six-film preparation/build generators and derived C/coefficients remain
private upstream material and are not distributed. The published tools require
that locally built candidate, its manifests/source roots and the existing
workspace dependencies listed below; this is not a standalone public build.
`audit_processing_recipe_byte.py` additionally uses Capstone and the local
`build_fixture`/`firmware_analysis` helpers with locally supplied X-T2 inputs.

## Earlier modular one-film candidate

The same checked 21 C sources now build as separate ordinary `film-sims` and
`noise-reduction` mods with 12 library dependencies, each source compiled once.
Original libc, lifetime, cardio and cardio/unpaced are consumed directly; seven
X-T2 metadata selections connect the previously adapted sources/interfaces. No C
source, native binding, emulator or loader was changed for this conversion.

The new ELF SHA-256 is
`9b2b4497f0032db99e6c15459cf8c378a9241b7d52583c0572501f1ac33b2045`;
the new SD boot SHA-256 is
`50e606058e8a7fe60736d2cf982704ab7245b3455b9c836c8cfe26e0b1dcc747`.
Footprint remains 141,776 bytes. All 52 target patch addresses/preimages match the
previous candidate, with new relocation values. The exact new artifact passes
ELF→region→SD correspondence, 117 processing cases, three NR menu bindings and
43 NR register/guard cases. Both mods and all libraries pass builder availability.
This does not qualify boot, actual services, a continuous producer or the camera.

The film mod still contains only the previously adapted immutable ETERNA, and the
settings selection still contains the stock-choice codec subset. The two normal
module names are not a claim that all upstream films/settings now work. The
checked linked init order remains NR enrollment before the film initializer;
other module combinations need their own startup/dependency checks.

`build_modular_candidate.py` generates the target metadata, asserts source-set
equality/no duplicates, then calls the original mod builder and recovery composer.
`verify_modular_candidate.py` reuses the processing and NR engines on this exact
artifact. The original artifact loader and card checker now accept a selected
build directory and per-unit source roots instead of assuming one flat module.
The package remains unaccepted for camera use.

## Earlier combined ordinary candidate

A locally built intermediate candidate contains processing for one immutable
ETERNA profile, shared stock-choice menu integration, noise reduction and the
settings/cardio/lifetime/timer source dependencies. Its 21 C sources are compiled
by the ordinary builder, not repackaged from an earlier synthetic ELF.

The candidate's ELF SHA-256 is
`947179e5c057978e5dfa683acb916990e47ec46c49026a6817d38186bd4dfc2f`;
the SD boot file SHA-256 is
`47366cfc801ab1aedad46ebcf9dee415ea1a33e552e69e737c23e7469ee8bb5d`.
ELF → resident region → SD bytes, all 52 edits and both SD file hashes have been
checked. Resident footprint is 141,776 bytes in a 196,608-byte reservation.
This is artifact correspondence, not evidence of SD transfer or camera boot.

The existing bounded NR assay on that ELF covers three native menu bindings and
43 register/guard cases. Its supplied calibration, RAM block, manual enrollment
and transport assumptions do not demonstrate a native still producer or image
quality. The exact ordinary ELF now also passes all **117 existing processing cases**,
including stock → ETERNA → stock, live/still, all supplied gain rows, zero-scale
behavior and bounded nested chroma checks. All eight processing thunks and
stock continuations executed. Selection uses the native setter/getter after a
manual two-function init registry; the host does not assign the final choice
key. Processing contexts and stored IDs remain explicit test inputs, not a
continuous native producer. Three existing uncontended transport fixtures,
supplied calibration/mode/startup pointers and a borrowed chroma frame remain
test assumptions. Incidental void-function return-register differences are
retained; output blocks match. No service startup, boot or camera is proved.

## Remaining scope

The two-mod intermediate candidate is not the complete FujiMod port. Additional
built-in films, shared/mutable/card films and existing editors remain unfinished,
as do WB ownership conflicts, service startup/storage/lifetime and other selected
X-T20 modules. A metadata dependency graph is not a working module.

No camera test is claimed; the candidate remains unaccepted. No firmware,
vendor coefficients, private upstream source or derived binary patch is included
here. The local build requires private pinned inputs and is not a standalone
reproducible public release. Public FujiMod infrastructure is available at
https://github.com/justjake/fujimod; private upstream access grants no assumed
redistribution permission.

## Published assay source and local dependencies

`verify_processing.py` is the reused original case engine;
`verify_ordinary_platform_processing.py` adapts its loader, selection and startup
boundaries to the existing candidate. These are original AI-assisted test tools,
not private upstream code or a new emulator. They are **not standalone scripts**.

To run from the prepared local workspace, provide its `ports/fujimod-xt2` and
`scripts` directories on Python's import path. Required local modules include
`build_fixture`, `verify_ordinary_platform_nr` (artifact loader),
`verify_ordinary_platform_card`, `build_eterna_payload`,
`verify_film_menu_navigation`, `verify_interpolated_profile_outputs`,
`verify_profile_selectors`, `firmware_analysis`, and their existing imports.
The loader requires the locally built ordinary ELF/region/card manifests, the
pinned source tree and local stock X-T2/X-H1 extracted inputs. Python packages
include Unicorn, pyelftools and Capstone; use the existing TCI library explicitly
via `LIBUNICORN_PATH`. None of these private firmware or upstream inputs is
distributed here. The root selection/output paths come from those local modules.

The passing run used the existing UI instruction budget (3,000,000) for native
selection; the old processing budget (200,000) stopped in bounded stock bitmap
conversion code before returning. No native code or peripheral response was
modified to complete that call. macOS sandbox execution required the same
approved outside-sandbox environment as earlier component assays.

The modular builder additionally requires the local original
`build_ordinary_platform_candidate.prepare` helper, its checked GNU source/target
inputs, pinned x70view tree, ordinary FujiMod Python extension and Arm GNU
13.2.Rel1 toolchain. It generates metadata inside the existing local target tree,
not public upstream commits. Select a new output directory for rebuilding; the
artifact checker must target that same directory. The reference verification
script's default is `modular-build-unverified`, not an arbitrary later rebuild.
The NR case engine (`verify_nr_candidate`) and resident constants/helper
(`build_resident_reservation`) remain local dependencies. No private inputs or
raw generated manifests are included here.
