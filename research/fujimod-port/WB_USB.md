# Compatible WB + volatile USB composition

`wb-usb-build-unverified` combines the completed custom-WB pair layer and the
existing volatile Fn action10 USB variant on their shared frozen native-menu
base892f. The builder checks identical shared metadata/source owners, merges
only agreeing target symbols and uses the existing ordinary linker/composer
conflict checks. USB still consumes its upstream Fn action; this compatibility
configuration does not claim physical Fn routing or an actual USB connection.

Exact ELF: `c4e87e6dff6031c9e67e1caec317480e52796ebc07acd3ea7bbeef0aa30d6353`.
40 sources, 14 libraries, seven mods, 77 SD words, payload246744bytes within
262144bytes at0x1380000;15400bytes spare. The fresh `wb-usb-rebuild-unverified`
reproduces ELF, payload, ffboot and ffsys byte for byte. Delivered SD bytes match
the exact ELF/region. Shared target memory operands are unchanged from892f.

All relevant checks were rerun on this exact ELF: WB84SAVE/cache-readback/
recall/edit chains, two guards, seven reset cases and six import formats with
42slots and coherent primary/shadow invalidation; native volatile USB controls;
49native custom film SAVE cases; native SAVE menu and formatter/codec checks;
21native storage/timer/settings/menu-flow reports; films356/identity99, NR43/
three menus, JPEG33/three menus. Delivered native BSS and allocator checks pass.
The map-service arguments are recorded, not an assertion of installed MMU state.

The new `verify_composed_sdk_settings.py` adapts only artifact/output/input
paths and verified ELF identity in the existing final SDK probes. Original SDK
source files and their frozen reports remain byte-exact. It records original,
adapted and wrapper source hashes. The existing two-A7 board, native mount,
timer8/IRQ56, native tasks and original asynchronous storage workers execute.
The combined artifact successfully commits ETERNA, writes SETTINGS.JSN through
the real native filesystem path and reads the produced166bytes back. A separate
fresh software board consumes those exact bytes and restores key32 without a
selection setter. No API substitution, registration/VFP enable write, injected
tick or successful callback is used. Earlier intentionally unregistered-driver
refusal/error cases also remain passing independently.

The SDK medium is a RAM-only software SD fixture. Physical SD/NAND persistence,
power-loss behavior, camera reboot, full ROM/UI boot, real MMU/cache/DMA timing,
physical button routing and USB host exchange remain unverified. WB extension
ownership retains the reviewed-path limits in WB_SHIFT_CHECKPOINT_2026-11-12.md.
This is a software composition milestone, not full-port or camera acceptance.

`wb-usb-check-unverified/integration.json`, `delivery.json` and `freeze.json`
pin exact evidence and source snapshots. Generated derivatives, firmware bytes
and private reports remain local. Original builder/adapters/checker and this
note are publication candidates. Next: separately compose the now-qualified
dual-slot date-folders layer and rerun affected exact-artifact checks, using
its two-item SAVE menu property mapping.

## Later negative-control discovery

A subsequent explicit native media-error fixture on18d06d6a exposes an inline
read callback while its cardio bank is RUNNING. The original callback is
classified stale and the request stays BUSY with an open handle. The passing
normal chains and listed bounded checks do not cover this newly reproduced
path. Existing upstream PR471 recorded-callback/task-issue adaptation is being
qualified in a separate successor. This frozen candidate does not contain
that fix and is not a completed or camera-accepted port. The raw local failure
report is cardio-task-contract-original-unverified/probe.json and is not
published. Private upstream inputs/generated C and all binaries stay local.
