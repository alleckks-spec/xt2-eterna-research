# Existing callback queue through X-T2 native transport

AI-assisted original adaptation and bounded verification, 9 November 2026.
This extends the [packet ABI result](UI_POST_ABI.md). It reuses the locally
supplied X-T20 queue and input implementation; no new service or hardware model
was added. The ordinary three-mod SD candidate is unchanged.

## What now passes

The native pool initializer, UI constructor, active-post registration and UILIB
constructor return successfully. The native UI constructor supplies a queue of
48 slots, each84 bytes: an8-byte kernel envelope plus the76-byte UI packet.
Registration itself changes the dispatch slot to the active routine; the host
does not set that slot or fabricate a queue result.

The native scheduler selects UI task1 at its original entry with a6144-byte
allocated stack. The assay then calls individual functions while borrowing that
context and stack. It does **not** execute the UI initialization/event loop.

The compiled original queue, reached through its actual entry-hook thunk,
passes:

- 18 callbacks via native post → kernel queue → native event receiver → decoder;
  each callback observes task1 through the native current-task function.
- All16 software slots occupied, with the seventeenth post returning busy.
- A stale generation replay while the slot holds a newer callback: stale event
  consumed, new callback retained and subsequently executed exactly once.
- An ordinary event and all68 payload bytes passed through unchanged, with an
  output canary intact.
- Redraw skipped in REC; two SETUP requests coalesced into one callback and one
  native UILIB queue46 packet. Native command is0x1424; the supplied16-byte last
  screen request arrives unchanged. This is transport, not rendered pixels.

Five native event-name lookup families return no name for0x6100. The native
receiver preserves this event. These checks do not prove that no unnamed stock
producer can ever emit0x6100; global event collision remains open.

## Minimal source changes and dependencies

`build_ui_post_component.py` validates original post/input Git blobs, applies the
76-byte message extent, and makes the custom-page activation handler weak and
guarded. That handler is absent because this component does not include the
X-T20-specific full custom-page engine. The queue algorithm and original
`input.c` are preserved. An explicit test callback and compiler memory-clear
helper accompany them. No fake menu handler or successful native API stub is
linked.

The builder requires locally authorized `decomp/mods` sources at the existing
x70view pin, the reference header alongside it, ARM-targeting Clang and LLD.
Its generated upstream derivatives, ELF and reports remain private. The checker
requires Python, pyelftools, an operational ARM Unicorn library, a locally
prepared original X-T2 flat image and inverted calibration input. Their hashes
are checked. It imports no other project Python modules.

```sh
python build_ui_post_component.py \
  --source-root /local/x70view/decomp/mods \
  --linker /local/bin/ld.lld --output /tmp/xt2-ui-post
LIBUNICORN_PATH=/local/unicorn-tci python verify_ui_post_component.py \
  --stock /local/xt2-stock/ffboot.bin \
  --inverted /local/xt2-441/inverted.bin \
  --component /tmp/xt2-ui-post/component.elf \
  --output /tmp/xt2-ui-post/verification.json
```

Exact tested component ELF SHA-256:
`6a2645dcea36e3f7b0932c4834bb3a299266c0e98163cea2366a7dc224ca5548`.
Apple Clang17 and the existing Unicorn TCI library were used. This is a synthetic
component placement, not a camera installation or standalone public port build.

Manual constructor ordering, calibration pointer, UI mode and last-screen block
are explicit fixtures. The scheduler initializer is stopped at the first UI
entry before it returns. Full startup ordering, concurrent producers, post
failure cleanup, the custom-page engine, visible rendering, card storage/timer
execution, mutable recipe lifetime and physical camera behavior remain open.

Next connect this existing component to an actual selected card-film consumer
after qualifying its mutable recipe ownership and storage dependencies. Do not
add a production module merely to retain otherwise unused queue functions.
