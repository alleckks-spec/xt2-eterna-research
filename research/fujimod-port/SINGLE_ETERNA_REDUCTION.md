# Reduced single-ETERNA candidate for X-T2 4.41

AI-assisted work, November 11, 2026. User request: remove interventions without
an established need and stay close to the working X-T20 approach. No camera
was available. This is bounded software evidence, not hardware acceptance.

## Decisions

| Difference from the pinned X-T20 source | Decision and evidence |
|---|---|
| Global timer-dispatcher stack literal change | Removed. The minimal mod has no linked timer implementation or native timer request. The whole checked constructor/dispatcher range matches stock SD bytes. The earlier diagnostic callback is not a production dependency. This does not fix or disprove the stock callback ABI observation. |
| Profile identity in +0x145..147 | Removed. Multiple-film identity is unnecessary for one immutable ETERNA. Reuse the already existing single-film adapter: native slot9 identifies ETERNA, stock uses slots0..8. No new processing implementation or side table. |
| RGB live/still curve hooks | Removed. The existing ETERNA-only source explicitly excludes them; its recipe does not require the multi-film RGB paths. Native still parameters and existing processing/copy tests pass without them. |
| Heap ceiling and split BSS clear | Retained for the existing placement. On the delivered candidate, restoring the original clear erases the reserved payload. Restoring the original allocator ceiling admits an allocation from0x138ffc0 to0x13900c0, overlapping the module. These edits are necessary for this placement, not proven necessary for every possible X-T2 port. |
| Boot memory mapping | Retained. As in the pinned X-T20 target, the resident mod needs executable memory; addresses/operands differ for X-T2. Existing checks observe intended mapping arguments, not actual MMU/cache behavior. No new placement search or peripheral model. |
| Per-invocation chroma temporary instead of per-core arming | Retained after a new negative control. Restore only the original X-T20 per-core mechanism in a separate diagnostic ELF: native caller A is paused after selection, B runs on another scratch stack on the same emulated core, then A resumes. A's output differs from uninterrupted execution. The final adapter preserves it with output canaries intact. This is an explicit counterexample ordering, not observed camera preemption. |
| X-T2 processing offsets, native bindings and missing donor gain inputs | Retained. They adapt concrete firmware/layout differences; exact-candidate stock and donor comparisons exercise them. No new sensor or encoder behavior is claimed. |
| Volatile choice instead of card-backed settings | Retained. No new persistence subsystem; unresolved card-backed paths remain excluded. Native stored film stays PROVIA0, custom ETERNA choice stays in RAM. |

The old shared recipe latch is not restored: an earlier bounded X-T2 example
showed B selecting stock changes A's ETERNA output. The reused one-film adapter
avoids that shared latch without writing profile padding. Full producer lifetime
and real task ordering remain unproven. No exact hashed SD image from the reported
successful X-T20 camera trial is available here, so this is a comparison with the
pinned source, not byte identity with a tester's card. Discord was not accessed.

## Exact result

- 45 delivered word edits instead of48. Removed edit sites: timer literal and
  the two RGB entry hooks. Other branch destinations move when code is relinked;
  45 versus48 is not a measure of physical risk.
- 74,024 resident bytes, 832 fewer than the previous candidate. Same existing
  reservation and composer. One film-sims module, 19 C sources, 12 libraries.
- No writes to the three profile-tail bytes in the actual still-builder runs;
  nonzero sentinels survive PROVIA -> ETERNA -> PROVIA on the same object without
  intermediate host clear/default calls. Stock before/after and four ETERNA
  parameter groups match. These are parameters, not JPEG pixels.
- All three menu lists, native policy, cancel/commit, stock return and Fn caption
  pass the bounded native checks. No mod storage/timer calls are linked or requested.
- Existing processing assay:117 records; stock/donor/reference data assertions pass,
  retained-context and same-core nested chroma checks pass. Four incidental r0
  return mismatches from void handlers remain recorded, with matching output data.
- Exact SD BSS/heap/map-operand checks pass; removing BSS/heap protection reproduces
  destructive overlap. No MMU/cache installation or full reset boot is inferred.
- Independent rebuild: ELF, region and both SD files match byte for byte.
- All83 files in the previous candidate's freeze remain unchanged. Old package and
  reports are preserved; the new package is the current minimal candidate.

| Artifact | SHA256 |
|---|---|
| mods.elf | d8244460d1c7622ddc65e84f4c4c9d5377f40b02e8736688ca7d092a5408df40 |
| region.bin | 108650cd924483bab87c66f98d21f12cba02a9f70b5bbd45b1e71f53f13be0c9 |
| ffboot.bin | 1527a05bf534d2baf2abbc9ad03e05e54cee15a158a062a67dcfc0ce368cb0b6 |
| ffsys.bin | b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351 |

Local package: artifacts/xt2-441-single-eterna-20261111.zip, 8,496,079 bytes;
SHA256 bdc9d79f20fba7f67e210fabdfd6c1777543486506bee3384098f87c8c5b9a24.
Firmware-derived binaries, instruction manifests, private derivatives, coefficients
and Discord records must not be published. Public Python files are original
orchestration/checks and require the existing private local dependencies.

## Reproduction and limits

Build through build_single_eterna_candidate.py with the same pinned SDK/compiler
environment as the prior candidate. It uses prepare_single_eterna_candidate.py
and reuses generated/processing.c unchanged, with its hash checked. Prepared inputs
and output directories are separate. Temporary target/library metadata is restored.
The packaged REBUILD.sh gives the build command; output must not already exist.

Run verify_single_eterna_candidate.py --case all with workspace .venv/bin/python,
PYTHONPATH="$PWD/scripts:$PWD/ports/fujimod-xt2", LIBUNICORN_PATH pointing to the
existing .toolchains/unicorn-tci directory, and UC_IGNORE_REG_BREAK=1. The builder
uses ports/fujimod-xt2/.venv/bin/python, a different environment. The two chroma
controls use verify_single_eterna_chroma.py; audit_single_eterna_package.py binds
reports and hashes, checks removed edits, original timer bytes and reproducibility.

Initial attempts are retained in local logs: the first build expected47 words but
correct ETERNA source also removed two RGB hooks, so it produced45. That receipt
failure is preserved separately. A wrong test venv lacked Unicorn; sandboxed
TCI attempts exited132 and were not counted as PASS. Final ARM runs outside the
sandbox exited0. No production source was changed after the successful rebuild.

Full ROM -> SD -> REC, physical controls, actual MMU/cache/DMA/allocator lifetime,
continuous live/capture producers, sensor/encoder/JPEG/color, power-off/settings
integrity and recovery after a hard hang remain untested. accepted=false.
The full FujiMod port is unfinished. Next hardware step remains one SD start
without taking a picture under the package's staged protocol; no camera action
was performed or assumed authorized by these local checks.
