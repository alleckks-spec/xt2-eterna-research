# Native invalid-open-handle control and bounded upstream backport

This stage implements only the open-handle validation subset of published
[x70view PR471](https://github.com/justjake/x70view/pull/471), pinned at
`2e2aa8af51526f81ec22036502b02881507dcd00`. Credit: Taylor Chapman
(heytchap) and Claude (Anthropic). The source transformation preserves the
earlier X-T2 listing/bank/native-status adaptation and keeps its upstream pin.
Generated upstream derivatives and binaries remain local.

## New evidence

The original component `f8f3e010a033176c95ef39802d3546718e2607595873c9f605c5f44bca43a765`
and fixed component `49b3cdede1b7871f386a3016fe37c21c808055e6fd0f725511e7ad72f5e146d8`
each pass24 controls in `cardio-open-guard-check-unverified/{original,fixed}.json`.
These are explicit callback-boundary controls, not successful filesystem opens.
Real compiled begin/claim/finish/retirement and native wrapper instructions run.

For read, write and write-at, a supplied status0 with handle0,0x10000000 or
0xffffffff reaches the corresponding native wrapper trap in the original
artifact. The fixed callback returns FAILED/-23 without calling a file wrapper;
its bank is FREE, active pointer/hold are clear and callback lifetime count is0.
The already-supported error5 remains5. Handles1 and0x0fffffff reach the expected
read/write/seek entry with the exact handle; execution stops there, before I/O.

Late zero opens were already dropped by the original code. Late invalid-range
opens previously reached the native close trap; the fix retires that orphan
without attempting close. This does not prove that stock has no leaked token
or filesystem slot: the callback boundary cannot establish that.

The A: handle range is checked against X-T2's actual wrapper tests; no X100F
address or readiness input is used. The library always opens drive A. The
second native drive range is not an admitted A: token for this adaptation.

## Boundaries

The existing native-worker Assay supplies device presence and scratch calls,
executes native constructors/semaphore configuration, and enables host
CPACR/FPEXC as already declared by that assay. This is not the SDK native-FS
bootstrap probe and does not qualify its CPU/VFP prerequisites. Reports pin
the actual TCI library path/hash. No filesystem success reply, request token
or native API success stub is installed. Native task scheduling, real open
completion and physical SD have not been demonstrated.

The initial checker attempts exposed dead-stripped busy getter and a wrong
seek-trap observation address; both harness errors were corrected. Initial
linker path was an expired temporary dependency, replaced by the explicit
existing Rust-toolchain LLD. Sandboxed runtime exited132; the approved local
unsandboxed TCI controls completed. None of these attempts altered old evidence.

## Reproduction

Use the workspace Python environment and existing toolchain:

```sh
.venv/bin/python ports/fujimod-xt2/build_cardio_open_guard_component.py \
  --output ports/fujimod-xt2/cardio-open-guard-new \
  --linker .toolchains/rustup/toolchains/1.89.0-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/gcc-ld/ld.lld
```

Repeat with `--original` in a different directory for the negative control.
Run `verify_cardio_open_guard.py --component DIR/component.elf --output REPORT`
with `PYTHONPATH="$PWD/scripts:$PWD/ports/fujimod-xt2"`,
`LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci"`, `UC_IGNORE_REG_BREAK=1`.

## Remaining work

The full PR's builder-token identity, lost-request accounting, orphan reuse,
callback-to-poll task issue, drive/admission gates, watchdog and DMA/cache
maintenance remain software gaps. A nonzero foreign handle is not rejected
by this bounded backport. Do not describe it as complete storage hardening.
Next integrate this exact source into the active-timer common candidate and
check its native file/restore/error chains and exact delivery/rebuild.

No camera was used. The full port and positive settings write chain remain open.
