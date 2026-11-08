# Fixed ETERNA / SEPIA candidate

**Later engineering result:** the [protected 274de1d2 variant](../minimal-data-protection/README.md) establishes data RO/XN in an image-contained native early-root check and rejects tested failures. The c1 image below is its historical base. Full camera boot is still HOLD; the separate early delivery probe remains the first proposed hardware step.

**Update (2026-11-08):** this HOLD concerns the full active ETERNA image and is an intermediate result. A separate [early delivery/power-request probe](../delivery-probe/README.md) now limits the first experiment before native startup/persistence. Its first-test proposal and residual risks do not qualify the full image or close the development goal.

**Admission: HOLD (2026-11-08). Do not offer the current candidate for hardware testing.** See [safety decision](SAFETY-DECISION.md) for blockers and evidence, and [deferred first-test protocol](HARDWARE-CHECK.txt). First qualify boot/return before any ETERNA capture.

Original research and source developed with OpenAI Codex assistance. Scope: fixed X-H1 2.15 ETERNA in the existing SEPIA slot on X-T2 4.41. No extra slot, profile file loader or live replacement is required.

Current local image SHA-256: `c1aee308e0b6c54dfede3de4c48885223365b2b8e90c282c74d87a112d58fc10` (46,505,984 bytes). It is **not camera-tested or certified safe**. No new ZIP was produced.

## Implemented

- Stock menu labels/icons/records remain intact: select **SEPIA**.
- ETERNA tone, gain and color-parameter changes are fixed in the image. The general parameter reader remains stock; 18 checked color-call sites use private readers.
- Independent builder bounds constrain writes. The SD experiment excludes update DAT files, and its host integrity gate rejects them.
- A 168-byte stackless check in existing unused early-entry space checks every functional patch span before the original reset continuation. Three clean-state comparisons and 98 injected failures pass in bounded execution. Failure masks interrupts and stops before the original LED body/startup; it does not fabricate successful flash writes or attempt rollback.

The numeric body is byte-identical to the preceding `47a93766...` image. That body passed 1,350 tone/gain, 90 aggregate, 15 development, 120 matrix/four-coefficient checks and private/stock reader comparisons. Its observed numeric CPU stores stayed within fixture RAM. Those are bounded checks, not full image processing or physical output.

[Early gate source, reverse engineering of Fuji practices, exact verification and limitations](BOOT-GUARD.md) distinguish what the check establishes from what it cannot.

## Missing qualification

There is no global internal-flash write prohibition or automatic stock rollback. The early checker/entry must themselves work, and it does not monitor later CPU/DMA overwrites. ROM file delivery, real cache/watchdog/multicore conditions, continuous UI-to-capture/development propagation, full boot, ISP/JPEG output and recovery after card removal remain unverified. Ordinary stock persistence/update paths still exist; SD boot is not a read-only sandbox.

The [external X-T2 stock SD report](https://github.com/justjake/fujimod/pull/163) supports the method, not this image. See [hardware notes](HARDWARE-CHECK.txt); keep DAT off the experiment card and do not enter firmware update mode.

## Local tooling

```sh
python3 audit_eterna_minimal_package.py /path/to/eterna-minimal-sd-candidate /path/to/stock/ffboot.bin
```

This standard-library gate requires local `ffboot.bin`, `ffsys.bin`, private `manifest.json`, and the stock directory's original DAT reference. It does not distribute or build firmware.

The adjacent numeric verifier and guard sources need the full local workspace and its private inputs/dependencies, detailed in BOOT-GUARD.md. No firmware, coefficients, raw manifest or copied firmware instructions are published. This is not a standalone firmware reproduction package.

The original `audit_eterna_minimal_admission.py` freezes identities and checks entry/branch destinations, static BSS separation, packaging consistency and byte equality of the unchanged numerically tested body. Run it from the original workspace layout, with Python 3 and the private candidate/stock/prior images, manifest, extracted layout, local reports, builder sources and FujiMod generated recipe. It does not fetch inputs, build firmware, trace ROM or establish recovery; the public directory alone cannot run it. Its output is local evidence, not a public patch manifest.
