# X-T2 FAT32 format label and original save_data codec

AI-assisted continuation, November 11, 2026. This is one software stage of the
full FujiMod port. The general mod-menu engine, real formatting and hardware
acceptance remain open.

The ordinary candidate now includes the existing X-T20 `sd-volume-name`
formatter hook and its existing `save_data` JSON owner, codec and registration,
alongside film-sims, NR, JPEG-max and card-films. It inherits the independently
checked full-timer and storage open-handle guard configuration. No new storage
service, file format, runtime or emulator was introduced.

The upstream pin is `9d22f1b41c70c20407158e699f2583ac4907ff16`.
The formatter source blob is `9598bc3883576ab7c1d0e3b4c77b0558dc06c4fe`.
Its only source change is the hook's expected X-T2 entry word. The X-T2 native
card-page-write doorway has the same five-argument ABI but a different prologue
and additional capacity/retry code; it was not located by applying an address
delta. The calendar wrapper, actual cached-date reader and lock were checked
separately. Six missing upstream owner/menu/codec files were materialized from
that exact pin and checked by Git blob identities. Those inputs are private
local dependencies, not publication material.

## Exact artifacts

Directory: `volume-name-resized-build-unverified`, card sibling with `-card`.

| File | SHA-256 |
| --- | --- |
| mods.elf | 58eab0e9177c61d00b689b4bd08ae3c52cb7215975266f7bc93d6462d0c3affa |
| region.bin | 7100b2fed021ad828c959932926b3bc56440ad5c4b4ae4aa2abd9562c84dc41a |
| ffsys.bin | b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351 |
| ffboot.bin | e4135cad07d50a1eaed6af4473667cd842d766285eb474365bf0301f715f8c5e |

Five mods, 37 C sources, 14 libraries and 68 delivered words. The native
formatter hook adds one word to the 67-word full-storage-guard baseline.
`accepted=false` remains the card status.

## New evidence

`verify_volume_name_candidate.py`, report
`volume-name-check-unverified/verification.json`, passes on this exact ELF:

- ELF/region/SD byte correspondence, all 68 words and complete SD file hashes.
- Three valid owner decode/encode cases and malformed-type rejection without
  changing the live values; the real registered owner appears exactly once.
  Default format naming is ON, and explicit OFF is preserved.
- Fourteen formatter cases: primary/backup sectors, disabled mode, multiple or
  high count, null buffer, invalid FAT32 signatures/type, unrelated block,
  write error and two boundary years. Source sector and adjacent canaries stay
  unchanged; the primary writes its root-label entry only after a zero primary
  result. The emitted sector contents, device/LBA and 64-bit page count match.
- The real native calendar wrapper, cached-date reader and lock execute using
  an explicit six-byte cached-date input and local-time mode input.
- The delivered entry branch and thunk consume the fifth stack argument and
  preserve SP and all eight callee-saved general registers.
- The delivered native BSS caller, shim and fill preserve the candidate's
  entire reserved payload while clearing prefix/suffix; the real native
  `_sbrk` refuses an allocation crossing the new heap ceiling.

The card-write data sink and its return status are supplied lower-call
boundaries. The real card-page writer body and physical medium are not executed
by these formatting tests. The upstream wrapper also discards the root-label
write's result; full error reporting for that second write is not established.

## Measured reservation and rebuild

The first actual link overflowed the existing 229376-byte reservation. The
retained failed map after the storage guard measured 229736 bytes, 360 bytes
over that boundary (`volume-name-guard-footprint-unverified/failed-mods.map`).
The existing 32 KiB-rounded heap-suffix mechanism was reused: the upper bound
stays at `0x13c0000`; start moves from `0x1388000` to `0x1380000`. Five existing
heap/BSS/map operands change. Capacity is 262144 bytes with 32408 bytes remaining;
the new native heap capacity is 1232132 bytes. No size assertion was removed or
weakened. This does not establish camera heap high-water or every task stack.

`volume-name-native-prefix-final-unverified/native-prefix-verification.json`
replays the existing two-core startup-prefix harness on an immutable copy of
that reservation. It passes after 83 rounds: pattern/shim survive, the actual
native permission API maps the entire reserved span identity/AP3/RWX and the
surrounding checked BSS pages XN. It stops deliberately at `cf8214`; its sole
recorded error is that named controlled stop. Every recorded input hash was
checked after completion. This prefix uses a pattern, not the mod ELF. Exact
candidate BSS/heap execution is the separate check above; complete ELF startup
and later ownership are not inferred from the pattern run. The older report in
`volume-name-reservation-unverified` is superseded by the immutable final run.

`volume-name-rebuild-unverified` reproduces ELF, region, ffsys and ffboot
byte-for-byte in a fresh directory with a fresh Python cache. Report:
`volume-name-check-unverified/rebuild.json`. GNU map text differs in temporary
object paths (`map_byte_equal=false`), and is not claimed byte-reproducible.

The lead's exact-artifact regression adapter is
`verify_volume_name_regressions.py`, output
`volume-name-regressions-unverified/`: NR 43 cases and three menu bindings,
JPEG-max 33 cases and three menu bindings, six films 356 transfer cases and
99 identity/interleaving cases, three native lists and six captions pass on
the same `58eab0e9…` ELF. The adapter follows the current declared labels and
the real linked film-label catalog; it does not reuse the retired standalone
ETERNA text symbol. Supplied calibration/init/transport and bounded producer
limits remain those of the original checks.

## Commands

In the prepared workspace, choose an unused output directory:

```sh
PYTHONPATH="$PWD/.toolchains/fujimod-944d5c8-source/bindings/python/python" \
PYTHONPYCACHEPREFIX=/private/tmp/xt2-volume-fresh-pycache \
XPP_SEGMENT_LOADER_TOOLCHAIN="$PWD/.toolchains/arm-gnu-13.2-darwin-arm64/bin" \
ports/fujimod-xt2/.venv/bin/python -u \
  ports/fujimod-xt2/build_volume_name_candidate.py --output NEW_DIRECTORY

LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" .venv/bin/python -u \
  ports/fujimod-xt2/verify_volume_name_candidate.py --build NEW_DIRECTORY \
  --output NEW_REPORT_DIRECTORY
```

The builder verifies the measured failed-map evidence and pinned baseline. It
temporarily applies target/library metadata and restores every original byte.
The helper requires existing authorized local firmware, upstream inputs and
toolchain. macOS sandbox execution exited 132; the existing TCI checker passed
outside the sandbox. One checker-only Python bytearray conversion failure was
fixed and the complete checker rerun; old logs are preserved.

## Remaining gap and next step

The original FORMAT CARD NAME menu declaration and its owner/value pointers
are retained in the link, but there is no X-T2 general mod-menu consumer.
Its visible row, native preview/commit/cancel and assignment are therefore
unimplemented; this stage is not a completed UI port. The owner codec is
verified directly, not claimed restored from a physical SETTINGS.JSN file.
Native file-load/startup regression checks of this larger ELF must account for
the extra owner rather than assuming the earlier registration count.

Next minimal UI step: adapt the existing XPP general menu engine for the native
X-T2 SAVE DATA list, then execute its FORMAT CARD NAME ON/OFF, cancel and commit
paths and verify that they operate this exact owner. Date-folders can reuse the
same owner/codec afterward, but still needs its own native object layout and
capture-name lifecycle evidence. Formatting/cache/DMA/task concurrency, FAT32
media behavior, settings persistence, full boot and all camera acceptance are
open. Other components' older results do not automatically apply to this
relocated ELF; follow the separate exact-artifact regression reports.
