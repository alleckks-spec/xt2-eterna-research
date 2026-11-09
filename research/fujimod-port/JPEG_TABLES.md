# X-T2 binding for the existing X-T20 JPEG Max module

AI-assisted original analysis and adaptation, 9 November 2026. The existing
X-T20 JPEG Max XPP module is now linked into the ordinary X-T2 common candidate,
alongside the six immutable films and NR. Bounded native checks pass; full port,
capture lifecycle and hardware qualification remain incomplete (`accepted=false`).

## Common candidate and exact-artifact checks

The original JPEG Max C changes only its quality property, `0x1ca` → X-T2
`0x1f1`. The existing quality-list binding receives the same property change and
X-T2 symbols for the four stock headers / three shared lists. Processing guards,
request/channel offsets, scale selection and stock continuations remain the
original implementation. No new service, loader, format or peripheral model is
introduced. All previous 21 C source files are retained unchanged.

The ordinary builder/composer produces **three mods, 13 libraries, 23 C files,
63 delivery edits and 148,912 resident bytes** within the 196,608-byte reservation.
This adds 3,824 bytes to the context-bound six-film/NR candidate.

| Artifact | SHA-256 |
| --- | --- |
| `mods.elf` | `8bea01979955b1e751643cb1201975adc553e9efe2eafa5ef327fdc990c013eb` |
| `region.bin` | `31d0c9f82620f1b7d67ee35924a0418609b97fcba9f3cb8842193b1dbfa285cb` |
| `ffboot.bin` | `2f9b5adfed23cb0f6bbdd4c6cde9d433d4a1b057e5843beb5c240de537a9f60d` |

The exact new ELF passes **33 JPEG cases**: manual init/enrollment, native
quality setter/getter, both extension keys retaining stock values 0/2 underneath,
all three copied quality lists, the actual entry thunk and the original X-T2
table builder. Only the two supplied first-primary-still cases receive scale 16.
Stock choices, retry/index, kind, tag, width, option, disabled channel and mode
guards retain stock table behavior. History scale, counters, write extents and
canaries are checked. These are supplied request contexts, not requests observed
from the complete capture producer or actual JPEG files.

The same ELF separately passes the reused **356 film cases + 99 context-identity
checks**, three film lists, six caption boundaries, and **43 NR cases / three NR
menus**. ELF → resident region → delivered SD bytes, all 63 edits and both SD
file hashes match. No camera acceptance follows from byte correspondence.

`build_jpeg_max_candidate.py` and `verify_jpeg_max_candidate.py` are original
workspace integration tools, not standalone public build instructions. They
require the previously prepared local context candidate/freeze, the pinned
authorized upstream checkout, original firmware/recovery inputs, GNU toolchain,
FujiMod Python bindings and existing local helper modules. Those private/generated
inputs are not bundled here. The builder saves its candidate target metadata and
restores the frontend's prior target file after building. Use a fresh `--output`
directory to preserve previously checked artifacts. Reused film/NR checks accept
the new word/init counts explicitly; their earlier defaults remain unchanged.

## Result

The X-T20 table-preparation entry at `0x292b2e8` has a unique corresponding
entry at **X-T2 4.41 `0x2a232e8`**, in overlay 002. Both take
`(channel, scale, option, alternate)`. The complete 33-instruction preparation
body has matching roles after its explicit pointer/scaler relocations. The
native X-T2 scaler is `0x15a0dd0`.

The submitter writes `history[index].value` and supplies `request + 0xa0` as
the channel, matching the existing module's assumptions. The request initializer
and three surrounding request-setup blocks retain the relevant argument layout.
The initializer copies a caller-supplied tag into `request + 0xd8`; this alone
does not identify every real capture descriptor or prove that still capture
supplies tag 4 at the expected time.

`verify_jpeg_tables_native.py` executes the original X-T2 preparation body and
scaler with the original local tables. **18 cases pass**: four scales, two options
and both alternate-table settings, plus two disabled-channel values. Scale 16,
option 1 produces both 64-byte tables containing only ones. Other scales match
the stock calculation; disabled channels leave the outputs unchanged.

The check accounts for the stock zigzag ordering, fixed first coefficient and
63-byte auxiliary coefficient-cache write. It verifies output/cache canaries,
the allowed write extents, returned table pointers and stack restoration. It
does not use peripheral responses, a JPEG hardware model or a stock-success stub.

## Running the check

Requirements: Python, `capstone`, `unicorn`, and an operational ARM Unicorn
library. Our observed run used the existing local Unicorn TCI build; the report
records its library SHA-256. Ordinary package builds are not invoked.

Supply extracted original X-T20 2.11 and X-T2 4.41 directories locally. Each
needs its `manifest.json`, `layout.json`, main high-address stream and
`overlay-002.bin`. The tool validates the loaded units against their recorded
SHA-256 values. Extraction, firmware and coefficients are not distributed here.

```sh
LIBUNICORN_PATH=/path/to/unicorn-tci python verify_jpeg_tables_native.py \
  --reference /path/to/xt20-211/extracted \
  --target /path/to/xt2-441/extracted \
  --output /tmp/xt2-jpeg-tables-check.json
```

This tool has no imports from our private workspace or upstream project. The
locally supplied firmware inputs and a working Unicorn installation remain
explicit prerequisites.

## Remaining port work

Qualify the real capture descriptor producers, first-submit/retry chain and
overlay delivery/lifetime before claiming a working JPEG capture path. Whole
film-context writers/copies and startup/card/settings/timer lifecycle also remain
open. The six-film context gate is not erased by passing JPEG component checks.

This check proves no JPEG file, compression ratio, camera startup, SD/settings
operation or physical-camera compatibility. No new SD candidate is accepted.
