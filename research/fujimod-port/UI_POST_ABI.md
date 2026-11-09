# X-T2 UI post message extent

AI-assisted original model adaptation, 9 November 2026. This qualifies a packet
copy ABI needed by the existing upstream UI callback queue, a prerequisite for
card-film publication. It does not add a queue/service or change the common SD
candidate. No camera operation was performed.

## Concrete model difference

The X-T20 `post.c` message contains two 32-bit words followed by44 payload bytes:
52 bytes total. The corresponding X-T2 active transport copies **68 payload
bytes from message+8**, producing a **76-byte packet**. Using the original
X-T20 stack structure therefore reads24 bytes past it on that X-T2 path.

The located public dispatch wrapper is X-T2 `0xcf8da8`, through slot `0xfae35c`.
Its stock initial value names the early deferred-header routine `0xcf8988`.
The active message routine is `0xcf8a18`; its payload-copy block begins at
`0xcf8a9c` and copies68 bytes through the original memcpy. Static initialization
of the deferred slot is not evidence that active runtime registration occurred.

The matching receiver setup is at `0x14da7ac`. It requests code/argument/payload
destinations at offsets0/4/12 and uses request ID `0x11c`, where X-T20 uses
`0x11a`. This is bounded setup/layout evidence, not qualification of every
receiver mode, filter or UI dispatcher branch.

## Executed evidence and adapter

`verify_ui_post_message_abi.py` runs the original X-T2 copy block with an explicit
borrowed native frame. Source messages end exactly at a mapped page boundary:

- The old52-byte message reaches an unmapped read immediately beyond its end.
- The adapted76-byte message supplies all68 payload bytes; the destination and
  its trailing canary match, with all CPU writes within the borrowed stack/output.

Both checks pass their expected outcomes. Execution stops at `0xcf8aac`, before
queue submission. No device response, queue success or callback is invented.

`xt2_ui_post_message_reference.h` is an original layout reference: payload
offset8, payload68 and total size76, checked by ARM C static assertions.
`prepare_ui_post_message.py` applies only that extent to the pinned locally
supplied original X-T20 `post.c`, preserving its queue algorithm. The generated
private C was compiled successfully into an ARM32 object with Clang. A separate
GNU standalone compile terminated137 and is not counted as a passing GNU build.
The common ordinary GNU-built ELF is unchanged.

## Dependencies and limits

The standalone copy checker requires Python, Capstone, an operational ARM
Unicorn library, and locally extracted original X-T20 2.11 / X-T2 4.41 main
streams plus manifests. It validates their recorded hashes; no firmware or
instruction listings are distributed. Our run used the existing Unicorn TCI
library, whose hash is recorded in the local report.

```sh
LIBUNICORN_PATH=/path/to/unicorn-tci python verify_ui_post_message_abi.py \
  --reference /path/to/xt20-211/extracted \
  --target /path/to/xt2-441/extracted \
  --output /tmp/xt2-ui-post-abi.json
```

The preparation tool additionally requires the authorized original upstream
`lib/menu/xpp/post.c` Git blob `8de17ec8f98fd55fdfc9df04f074c161573d9390` and the
reference header next to the tool. It emits a private source derivative, which
is not included here. Compiling that source also requires the locally supplied
upstream mod/menu/hook headers. This is not a standalone public FujiMod build.

The subsequent [native transport/component check](UI_POST_TRANSPORT.md) now
qualifies active registration, callback delivery in a borrowed native-scheduled
UI context, and redraw submission. It does not change this copy-only report's
scope. Global event collision, ordinary common integration, full card loading,
mutable recipe lifetime, startup/storage/timer execution and camera remain open.
