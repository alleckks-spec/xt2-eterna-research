# X-T2 binding for the existing X-T20 JPEG Max module

AI-assisted original analysis, 9 November 2026. This is a newly qualified native
function binding, not a linked JPEG Max mod or a camera result. The current
six-film/NR SD candidate is unchanged.

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

The X-T2 quality property is `0x1f1`, rather than the X-T20 module's `0x1ca`.
Its menu headers have been located separately. Next adapt the original JPEG Max
module and quality-menu binding, include them in the ordinary common package,
then verify enrollment, native selection, first-attempt guards and unchanged
retry/preview paths on that exact ELF. Qualify the real descriptor producers and
overlay delivery/lifetime before claiming a working capture path.

This check proves no JPEG file, compression ratio, camera startup, SD/settings
operation or physical-camera compatibility. No new SD candidate is accepted.
