# Existing film loader: parser compatibility and native error retry

AI-assisted original adaptation and checks. This is a separate component;
the ordinary timer candidate and SD files are unchanged.

The supplied shared parser failed to compile with the XPP film header: it
referenced the X70-only `film_custom_icons` object. XPP already supplies
`FILM_CUSTOM_ICON_PICKER` and `FILM_CUSTOM_ICON_Q` (both zero: no artwork).
`prepare_film_parser.py` selects those constants in the pinned parser, rather
than introducing an icon registry or a substitute parser.

The component builds the existing loader, parser, generated schema codec,
film table and XPP publisher, together with the previously checked cardio,
timer and UI-packet adaptations. Original `cardio/unpaced` keeps the loader
on its own timers. The small AAPCS helpers call the supplied libc. The build
uses Clang17 ARM soft-float and LLD20; the known ignored GNU `long_call`
attribute warning remains. It is not an ordinary GNU/SD integration result.

Component ELF SHA-256:
`82b1a840f7d8adecac712f26ba86b9cda55e418c871931a2a3057a8b232aacae`.
The synthetic placement starts at `0x2100000`. Immutable recipes and the
six-row menu implementation are imported from the existing common ELF;
this does not add card rows or qualify mutable processing.

## Executed evidence

- The actual parser and schema accept a supplied document with `custom` and
  `provia` icons, preserve the film ID/name and produce the XPP zero icon IDs.
  An unknown icon returns `-4`. Documents are supplied in RAM, not read from SD.
- The upstream `film_loader_boot` starts its actual periodic timer. Explicit
  calls of the native software-timer handler deliver the first loader tick,
  which sends a directory request through the adapted cardio implementation.
- The actual native queue workers and callback return status5. The loader's
  10ms poll records `FAILED`, `last_error=5`, `failures=1`, `retry_ticks=10`;
  the catalog remains unknown and publishes no card recipe.
- Nine more periodic callbacks leave one retry tick. The tenth changes the
  loader back to `LISTING` and submits another real native queue request.
  No host write sets the retry state or delivers the C callback.

The native semaphore bootstrap, worker-entry boundaries and diagnostic clock
come from the existing `verify_cardio_native_worker.Assay`. Constructors and
worker entries are harness-invoked. Calls use scratch stacks with current-task
ID0, not a scheduled timer-task stack. Logical ticks are explicit native-handler
calls, not elapsed physical time or interrupts. REC-idle bytes and device
presence are explicit fixtures. A temporarily absent device context causes the
native handler failure; the same context is restored before the loader poll
to test the listing-error path independently of a media-epoch change.

There is no successful mounted-FAT file read, full loader success, card-row UI,
mutable recipe lifetime, full startup or physical camera result here. The run
ends after observing the new pending retry request. The common SD remains
unaccepted for camera use.

## Locally supplied dependencies

`build_film_loader_component.py` needs authorized x70view inputs pinned at
`9d22f1b41c70c20407158e699f2583ac4907ff16`, including the original loader,
X-T20 film headers/tables, schema-generated film codec and their headers.
These private sources and vendor-derived data are not distributed. It also
needs the already published cardio/timer preparation tools and reference
headers, Clang, LLD, pyelftools, the local X-T2 target description/API header,
and the exact common timer ELF (`06ab0977…`). Generated private C stays local.

The checker additionally needs Unicorn, the existing TCI library, the
published native-worker checker, locally supplied
`scripts/kernel_timer_initialization.py`, stock X-T2 flat image and the
previous cardio-status component (`dd6a2add…`). Build dependency hashes are
checked before execution. This is not a standalone public build.
