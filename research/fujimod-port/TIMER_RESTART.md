# Correct timer restart in the ordinary X-T2 candidate

AI-assisted original adaptation, 9 November 2026. The existing XPP timer wrapper
now cancels an active native handle before restarting it. The same three mods,
13 libraries and23 C files remain selected; no new timer service or emulator
model was added. This change is integrated into an ordinary GNU-built SD
candidate, unlike the separate UI-post component.

## Reproduced defect and correction

The previous wrapper started a second native timer and overwrote its sole saved
handle. The earlier periodic timer remained active. A bounded run of the exact
previous common ELF reproduced three callbacks over five logical ticks after
restart, then three more after cleanup of the new handle.

The corrected wrapper first cancels the active handle. Over the same interval
only the new callback fires once; after cleanup there are no further callbacks.
The lifetime registration is reused. On a native cancellation refusal it keeps
`running` set, returns the failure from its lifetime cleanup callback and refuses
to start another timer. The old wrapper instead cleared `running` and reported
cleanup success. A failed restart now preserves the timer object's handle/hold/
running fields. The X70 branch is left unchanged and is not qualified here.

The checker also executes the loader's10ms one-shot and300ms periodic durations.
For300ms, the first callback occurs after121 explicit native tick-handler calls,
then every120 calls. No callback count, timer handle or native success return is
supplied by the host. Native initializer, allocator, start/cancel/tick functions
and compiled callback all execute.

## New common artifact and validation

- ELF SHA-256: `06ab09771172acde5d7e330066ad4f8679083a751767f80701d225ee5e43b85d`.
- Resident region:148,944 /196,608 bytes, an increase of32 bytes.
- SD boot SHA-256: `bad95c97de182d0f135f9147b34758fa59511b8a31a11c483514e0e797cf2204`.
- Original timer defect reproduction and corrected regression both pass.
- Exact new ELF passes356 film cases,99 identity cases, three film lists/six
  captions, NR43/3, JPEG Max33 and all63 ELF→region→SD patch correspondences.

The previous JPEG producer-prefix checks belong to the older ELF; they were not
rerun or silently relabeled for this artifact. No physical camera was used, and
the package remains unaccepted.

## Original tooling and local inputs

`prepare_timer_restart.py` checks original timer Git blob
`f872a416c84fd5639547213ecf4dd3c6e1633db4`, then applies only these XPP wrapper
changes to a private generated C file. Original sources come from the existing
authorized local x70view pin. Generated private C, firmware, coefficients,
manifests and ELF files are not distributed.

`build_timer_candidate.py` reuses the ordinary builder/composer and the prepared
three-mod baseline. Exactly one source is replaced; target/library metadata is
temporarily selected and restored afterward. It depends on the existing local
`build_modular_candidate`/`build_ordinary_platform_candidate` helpers and their
prepared private inputs, original FujiMod Python extension and Arm GNU toolchain.
This is not a standalone public reproducible build.

`verify_timer_restart.py` needs Python, pyelftools, operational ARM Unicorn,
locally supplied original stock flat image, both locally built ELF inputs and
the existing workspace `scripts/kernel_timer_initialization.py` on `PYTHONPATH`.
The callback component is built with the already published
`build_ui_post_component.py`. The timer-register helper is unchanged: only its
fixed reset counter is read for a diagnostic timestamp in the negative case;
there is no time advancement or IRQ delivery. Its hash is recorded.

```sh
PYTHONPATH=/local/workspace/scripts LIBUNICORN_PATH=/local/unicorn-tci \
python verify_timer_restart.py \
  --stock /local/xt2-stock/ffboot.bin \
  --candidate /local/timer-build/mods.elf \
  --callback-component /local/ui-post/component.elf \
  --output /tmp/xt2-timer.json
```

Use `--expect-original-leak` with the previous ELF to reproduce the defects.
The harness registers and executes the original lazy-VFP exception handler;
architectural UND entry and its stack are supplied, not an invented ready flag.

## Evidence boundary

Native scheduling selects UI1 and its allocated stack. Function calls borrow
that context; the callback's observed task1 is **not** evidence of execution on
the actual timer task. Logical ticks are explicit native handler calls, not
elapsed camera time. The scheduler initializer has not returned. An original
native initialization-clear function induces the cancellation refusal; this is
an isolated negative path, not a qualified shutdown order.

Actual timer-task startup, IRQ routing, concurrent callback/cancel behavior,
complete teardown, mounted-card/storage execution, full late-start ordering,
mutable recipe ownership, WB and camera boot remain open. Existing lifetime
registration handles mod teardown; it does not by itself protect recipes being
rewritten during processing.
