# X-T2 directory requests and listing ownership

AI-assisted original adaptation, 9 November 2026. This transfers another part
of the existing XPP card-film dependency. It changes directory command IDs and
reuses the existing callback banks/queue hold; no new loader, resource registry,
buffer pool or hardware model is introduced. The ordinary timer-fixed common
SD candidate remains unchanged.

## Model difference and native transport

X-T20 listing sends first/next commands0x1370/0x1371. X-T2's original builders
use **0x1377/0x1378**, with the same60/8-byte payloads. Correcting addresses
alone would leave the wrong request codes in the port.

The bounded checker executes native pool initialization, storage dispatch-table
publication and both media constructors. The primary media queue is120, the
secondary123; each native queue entry is88 bytes. The native sender at0x969f24
and kernel transfer execute. The compiled component's callback/details pointers,
NUL-terminated path/pattern and option agree with original native builder
packets. Undefined string-field tails in the native stack are not compared.
The original absent-device state is refused. The subsequent positive transport
checks explicitly supply a device-context fixture satisfying the native guard;
this is not evidence of a mounted card.

## Reproduced callback defect and minimal correction

The original XPP listing callback reads the global active job rather than its
own callback bank. After abandoning listing A and starting B, A's late callback
adds the synthetic `STALE.TXT` entry to B. B finishes with both `STALE.TXT` and
`GOOD.TXT`, and A's bank remains orphaned even after callback accounting reaches
zero. This counterexample runs compiled original C through real native queues.

The correction uses the already existing `BANKED1` callback convention, claim/
unclaim and stale-drop paths. An abandoned listing retains the existing queue
hold until its callback retires. This also preserves serialization of the native
single directory cursor. A new listing is refused during that interval; after
the old callback releases its bank/hold, B starts and contains only `GOOD.TXT`.
All four banks and outstanding-callback accounting then return to zero.

The original single details buffer is retained. No additional per-bank payload
or details arrays are needed with this serialized lifecycle. If an abandoned
callback never returns, the XPP hold remains; this change does not invent a safe
timeout or prove native cancellation. Concurrent callback/abandon execution is
not qualified by the sequential counterexample.

## Original tools and local requirements

- `xt2_cardio_listing_reference.h`: original transport constants/bindings.
- `prepare_cardio_listing.py`: validates original local `cardio.c` blob
  `7b77be6ea3513e5822baa2493a89e1ef1466c3c9`, then applies only the XPP changes.
  Generated C is a private upstream derivative and is not distributed.
- `build_cardio_listing_component.py`: original/adapted component using locally
  authorized upstream cardio, lifetime, libc and headers. Unused file operations
  are garbage-collected. This is an isolated Clang ARM component, not an ordinary
  SD build or a replacement production module.
- `verify_cardio_listing.py`: Python, Capstone, pyelftools, operational ARM
  Unicorn and locally supplied original stock flat image/component ELF. Native
  API success returns are not stubbed. Source/dependency/preparation hashes must
  match the successful build, so a failed rebuild cannot validate a stale ELF.

```sh
python build_cardio_listing_component.py \
  --source-root /local/x70view/decomp/mods --linker /local/bin/ld.lld \
  --output /tmp/xt2-cardio-list
LIBUNICORN_PATH=/local/unicorn-tci python verify_cardio_listing.py \
  --stock /local/xt2-stock/ffboot.bin \
  --component /tmp/xt2-cardio-list/component.elf \
  --output /tmp/xt2-cardio-list/verification.json
```

Use builder `--original` and checker `--expect-original-defects` for the control.
Final tested ELF SHA-256 is
`d2faea6b75dcf877dd75febef0375f77afaaa72eead1e20ab91872a577a3a44c`;
the control is
`a4e5e690d4729f76049caedf152a20f4746592273cc43df7f4ed1ac36cf1fe82`.
Both expected outcomes pass. Clang ignores the original GNU `long_call`
attribute; actual native calls at this synthetic placement execute successfully.
An existing LLD20 binary was copied byte-for-byte outside FileProvider after
the toolchain wrappers were killed; the linker hash is recorded. No binary is
published and no GNU production build is claimed for this component.

## Remaining evidence

Directory records and callback delivery are explicit fixture inputs. The
upstream100-byte details buffer and its field interpretation have **not** yet
been qualified against the native X-T2 FAT writer. A supplied nonzero terminal
callback preserves upstream end-of-list handling; it is not proof of physical
EOF or correct classification of every storage error. Actual storage workers,
mounted FAT reads, startup/scheduling, concurrent abandonment and cancellation,
full teardown, mutable recipe lifetime and hardware remain open.

Next qualify the native details writer/worker boundary, then connect the existing
film loader and its real consumer. Do not add an unused production module merely
to retain listing code. Private source, firmware, generated tables/ELF and raw
patch manifests are excluded from publication.
