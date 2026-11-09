# Ordinary card-films build and native menu publication

AI-assisted original integration. **Card processing is still incomplete.**
The new experimental ordinary candidate includes `card-films` alongside the
six built-ins, NR and JPEG Max, but the context adapter still declines card
recipe pointers. Selecting a card row currently leaves stock Provia processing.
This is not a working card simulation or a camera-ready release.

The existing loader, parser/schema, table, publisher, registration, UI queue
and previous cardio/timer adaptations now compile together through the ordinary
FujiMod builder: four mods,14 libraries,33 C files. No replacement loader,
runtime service, task registry or emulator was introduced. The publisher and
choice now use X-T2's film property `0x1fc` instead of X-T20's `0x1d4`;
the original six-plus-ten choice rows/labels are retained.

## Placement and artifact evidence

The first complete link exceeded the existing192KiB reservation by28,644 bytes.
The failed linker map identifies a225,252-byte footprint. The existing reservation
mechanism is expanded downward32KiB, keeping its upper BSS boundary unchanged:
`0x1388000..0x13c0000`,229,376 bytes,4,124 bytes remaining. Five existing target
words change the heap ceiling, mapping start and BSS-prefix count; no new
allocator, map service or BSS-clear implementation is added.

Nine bounded native `_sbrk` cases distinguish the new ceiling from stock and
preserve errno/cursor behavior. Heap capacity becomes1,264,900 bytes; camera
heap usage is not qualified. The reused two-core startup-prefix check reaches
`0xcf8214` in83 rounds with actual native mapping/cache routines: the pattern
and shim survive, reserved pages are identity RWX/AP3, surrounding pages remain
RW/XN. This uses an explicitly preloaded pattern, not the module or SD delivery.

New common ELF SHA-256:
`db56c69c993a30e9fbdfb024ad766e005234b50f76684082b29683a526dd3754`.
ELF→region→SD correspondence and all64 words pass. The exact ELF also passes
the existing NR43 register/3 menu and JPEG33 table/3 menu cases. Their calibration,
manual four-init and uncontended transport assumptions remain unchanged.
The earlier356-film/99-context numerical results have not been rerun on this ELF.

## Native menu evidence

The new menu checker uses native pool/UI/UILIB constructors, the original
semaphore bootstrap, native scheduling to UI1 and native gate clearing. Calls
borrow that task's allocated stack, which does not overlap the reservation.
All four module init records execute. Six built-in selections return their
immutable recipes. A supplied post-parser document is parsed/stored and passed
to the actual publisher; its post goes through the native UI queue and receiver
thunk to `show_now`. The card row appears in all three list arrays, property
`0x1fc` succeeds without a show refusal, and key38 selects its converted recipe.
The actual native Fn name lookup returns the publisher's `Card menu` text
record. Removing the entry through the original table API and publishing again
hides its row in all three lists through a second native UI callback.

The actual qualified context mapper then rejects that card pointer and leaves
the stock slot/tag. This records the outstanding processing gap rather than
silently treating a visible row as a ported simulation. Native lazy-VFP faults
use the existing architectural exception transport and original UND handler;
FPEXC or successful API replies are not forced to skip them.

Calibration, REC/settings pointers and the post-parser record are explicit
fixtures. This is not a complete UI event loop/render, actual card-file read,
card recipe processing/lifetime, full startup or physical camera result.
The older [file-boundary chain](FILM_LOADER_FILE_BOUNDARY.md) belongs to its
separate component and is not relabeled as a read on this new ordinary ELF.

## Original tools and local dependencies

- `build_card_films_candidate.py`: existing ordinary builder/composer with
  temporary, restored metadata selections and targeted model adaptations;
  failed link evidence is retained without bypassing its failure.
- `prepare_card_films_reservation.py`: consume the failed link footprint,
  adjust the existing target/shim and optionally run the existing native prefix.
- `verify_card_films_heap.py`: native ceiling boundary cases.
- `verify_card_films_regressions.py`: parameterize the existing NR/JPEG engines
  for this region,64 words and four init records.
- `verify_card_films_menu.py`: actual native UI publication and explicit
  processing-decline check.

These need the authorized pinned x70view sources/headers/schema/tables, previous
local target/reservation/candidate preparations, GNU13.2 toolchain, FujiMod
Python binding, Unicorn TCI, pyelftools and the existing local native startup,
NR/JPEG/menu/clock helpers. The exact preparation paths are explicit in the tools;
put prepared `scripts` on `PYTHONPATH`. Private inputs, firmware, binary targets,
instruction manifests, coefficients and raw reports remain local. This is not
a standalone public build. Target layout, source/library graph and dependencies
must be preserved when rebuilding; source presence is not hardware admission.
