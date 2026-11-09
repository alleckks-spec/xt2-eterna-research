# Native listing errors and details ABI

AI-assisted original X-T2 adaptation, 9 November 2026. This extends the existing
[listing transport/ownership component](CARDIO_LISTING.md). It fixes an error
being accepted as an empty catalog and qualifies the bounded native details
writer. No new loader, resource layer, buffer pool or hardware model is added.
The ordinary timer-fixed common SD candidate is unchanged.

## Error reaching the real callback

With a request already queued, removing the fixture device context makes the
native handler return callback status5. The previous XPP callback treated every
nonzero status as successful end-of-list: the job became DONE/status0, even
after an entry had already been returned. A loader could accept this I/O failure
as an empty or partial catalog.

The new adapter normalizes only X-T2's native end/no-match callback status6.
Other callback errors remain failures. Readiness and next-request submission
failures also retain their status instead of completing a partial catalog.
Existing job/state API, callback banks, hold and single details buffer remain.
The prior component is preserved as the exact control.

All39 native internal statuses were executed for both listing commands:78
mappings. Only internal7/8 map to callback6. Actual first/next FAT-wrapper branch
fragments distinguish the0x10a no-match condition from errors before the native
status mapper runs. No filesystem API success return is stubbed.

## Executed chain and limits

After the native pool constructor, the harness invokes the original bootstrap
fragment `0xcf8134..0xcf8154`: firmware creates semaphore IDs1..131 with initial
count1, and every creation returns0. Native dispatch/media constructors follow.
The worker's initial semaphore wait now returns0; the earlier setup lacking
that fragment returned-42 and was not counted as successful startup. No host
kernel semaphore/worker-ready flag or synthetic ready-post is used. Positive
device-context fields remain explicit test fixtures.

Native worker entries are invoked with scratch stacks: queue120's worker
forwards the packet through the real kernel queue to worker39; its dispatcher
and first/next handler call the compiled component callback. Initial gate and
message handling execute, but scheduling, full startup order and actual worker
stack ownership remain unqualified.

Five checks pass, with the prior error reproduced by the control:

- Removal before the first handler: native5 now produces FAILED/5.
- Abandoned request retires through the native callback, releasing hold/bank.
- Removal before the next handler preserves count1 and reports FAILED/5.
- Readiness refusal before next submission also preserves FAILED/5.
- Native details writer feeds the actual C reader, then the native end mapper
  completes it with DONE/0 and one entry.

Positive details checks begin after the FAT call with a borrowed frame and
synthetic80-byte FAT record. Both original first/next writers execute, including
date-formatting helpers: eight cases check names, all attribute bits, size,
allocation rounding and two dates. Their100-byte output has97 written bytes
and untouched padding49..51; canaries and input record stay intact. The compiled
reader consumes native-written name/attributes/size. This qualifies the selected
record ABI, not a successful FAT read. The EOF check supplies a raw internal end
status at the handler tail; native code performs mapping and callback invocation.

## Original tooling and local inputs

`xt2_cardio_status_reference.h` contains original end-status normalization.
`prepare_cardio_status.py` extends the frozen listing adapter; generated private
C is not distributed. `build_cardio_status_component.py` reuses the existing
component builder with that preparation function and pins extension dependencies.

`verify_cardio_native_worker.py` requires Python, pyelftools, operational ARM
Unicorn, local original stock flat image and component ELF. It reuses the
workspace's unchanged `scripts/kernel_timer_initialization.py` on `PYTHONPATH`
only for diagnostic timestamp reads at reset count0; no time advancement/IRQs.
Clang/LLD and authorized pinned upstream sources/headers are required to build.
This is not a standalone public FujiMod build or ordinary GNU production image.

```sh
python build_cardio_status_component.py \
  --source-root /local/x70view/decomp/mods --linker /local/bin/ld.lld \
  --output /tmp/xt2-cardio-status
PYTHONPATH=/local/workspace/scripts LIBUNICORN_PATH=/local/unicorn-tci \
python verify_cardio_native_worker.py \
  --stock /local/xt2-stock/ffboot.bin \
  --component /tmp/xt2-cardio-status/component.elf \
  --output /tmp/xt2-cardio-status/verification.json
```

Use checker `--expect-masked-error` with the frozen prior listing ELF as control.
New tested ELF SHA-256:
`dd6a2add2213fd6c3a59486148db009e19203f33d65ef4c27e28bcfbb0a57712`.

Mounted FAT, actual file contents, service/task lifecycle, concurrent cancel,
full film-loader integration, mutable recipe ownership, WB and camera operation
remain open. Only original tooling/notes are published; private C/ELF, firmware,
vendor tables and raw patch manifests remain local.
