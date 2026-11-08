# Minimal SEPIA-to-ETERNA selection regression

Original research and verification code developed with OpenAI Codex assistance. This is a bounded native ARM regression, not camera-tested firmware or a standalone reproduction package. It tests the existing local SEPIA-alias image, separately from the newer custom-profile loader.

Image SHA-256: `0f14244971768d783e09d4eb21fe59e60262ea183b938d31ff1fff170caceddf`. The test did not change the image.

| Transition or check | Result | Scope |
| --- | --- | --- |
| Actual menu tables, input routing, original conversion/dispatch, RAM setting write/readback and live value | PASS | 17 selections; public SEPIA ID5 retained |
| Other supported profiles | PASS | 14 flat-menu profiles retain tested behavior |
| Native getter value to actual capture/development producer | UNVERIFIED | Test explicitly supplies the getter byte to capture inputs |
| Original context-call block and patched selector | PASS | Getter-derived ID5 produces processing9; stock produces3 |
| Patched development selector | PASS | Getter-derived ID5 produces16; stock produces10 |
| ETERNA tone/gain outputs | PASS | 90 vectors match X-H1 public18 in matching declared contexts;18 is used only in the reference machine |
| Menu mode visibility | PASS | Six mode32/36 cases; hidden mode32 row is not forcibly selected |
| Global parameter branches | PASS | Five B5/F740 combinations; normal ETERNA tone51/51, forced branches46/45; native priority retained |
| Selector byte inputs | PASS | All256 checked;255 non-alias inputs preserve stock fallback/output/register/flag behavior |
| Invalid menu dispatch, durable storage, full image pipeline and physical output | UNVERIFIED | No broader claim from selector-only or RAM-only checks |

Normal gain record77 is observed in the declared mode0/channel0/adjustment4 context. Forced global branches select gain2. These tests use official update default parameter bytes, not a per-body calibration dump. They do not establish numerical safety of arbitrary profiles.

The conversion row `(5,4,5,10)` contains several interface representations: its value4 is not the processing-context enum. Native execution establishes stock context3 and patched context9. This distinction is why directly testing downstream functions is insufficient to verify menu selection.

The native lower capture blocks separately transport a cache byte through an object and capture global into context. The missing link from the live/menu value into that cache remains explicit. This is not a continuously executed UI-to-image pipeline.

Two native synchronization functions are declared successful fixtures; menu globals and input packets are synthetic. The flat menu still has its SEPIA caption; only two other menu descriptors were relabelled in the existing candidate. SD loading, carrier lifetime, physical buttons/rendering, reboot persistence and actual JPEG/video/preview remain unverified. No firmware, extracted coefficients, disassembly or raw output buffers are included here.

## Reproduction dependencies

The published Python file is the original verifier, supplied for review. It depends on the local research harness modules named in its imports, pinned extracted X-T2 4.41 and X-H1 2.15 inputs, the separately built minimal image, Unicorn with the project's tested backend, and prior baseline reports. Those dependencies are not all published, so this directory is not a standalone build.

Local command, from the research workspace root:

```sh
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_eterna_minimal_menu_chain.py
```

The local JSON report records twelve helper-source hashes, image/artifact hashes, donor stream/default-parameter hashes and PASS/UNVERIFIED per transition. The full local report contains vendor-derived parameter outputs and is intentionally not published.
