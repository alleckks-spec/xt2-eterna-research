# FujiMod X-T20 → X-T2 adaptation

AI-assisted independent port work, targeting X-T2 firmware 4.41. The current
objective is to adapt the existing FujiMod/X-T20 modules through their ordinary
XPP builder and recovery composer. The earlier standalone Sepia replacement is
historical research, not the current implementation plan.

## Current modular candidate

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
