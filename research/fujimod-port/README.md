# FujiMod X-T20 → X-T2 adaptation

AI-assisted independent port work, targeting X-T2 firmware 4.41. The current
objective is to adapt the existing FujiMod/X-T20 modules through their ordinary
XPP builder and recovery composer. The earlier standalone Sepia replacement is
historical research, not the current implementation plan.

## Existing ordinary candidate

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

The combined intermediate module is not the completed modular port. Additional
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
