# Loaded profiles reach native color consumers

Original research and verification code developed with OpenAI Codex assistance. This is a bounded ARM integration check, not working camera firmware or a standalone reproduction package.

The existing native file-queue check stopped after validating and preparing a private candidate. The new verifier carries two different laboratory containers through that path and then executes the original tone/gain consumers in the same emulator instance. Both containers are authored perturbations of the locally supplied canonical reference; they are not independently authored coefficient tables or recommended camera presets.

## Result and supplied boundary

Native public file APIs, queue copies, open/read/close workers and private preparation execute with the existing declared lower-storage, mounted-context and RTOS fixtures. The mode word remains 1; each reader receives exactly 3,008 bytes and reaches READY, and the audited resource fields are cleared. The harness releases routing after worker return. This does not implement the unfinished autonomous owner/tail protocol.

After preparation, the **host explicitly copies the prepared candidate to its declared placement and writes its 29 hook words in isolated emulator memory**. This supplies the missing activation boundary. The firmware does not perform this transition itself. No consumer exclusion, runtime cache publication, mounted-card read or physical execution is proved.

With that boundary supplied, the check verifies:

- Six custom tone/gain/bounds output comparisons match a separate direct-RAM reference: two containers, three synthetic contexts each.
- Changing the container changes both tone and gain in all three contexts.
- Six comparisons for stock public profile 3 match an untouched stock reference; its output is unchanged between the two containers.
- Per container, one custom tone record, three custom gain records and two parameter reads match independently sliced container bytes. Stock tone/gain record zero also match original local inputs.
- Traces enter the original numerical functions and read the staged tables. The prepared buffers and original parameter backing remain unchanged.

The numerical comparison shares original ARM arithmetic with the reference and is differential, not an independent mathematical oracle. The contexts are `(mode, channel, adjustment)` = `(0,0,4)`, `(0,3,4)` and `(3,2,8)`; adjustment fields remain correlated. This small selection establishes data sensitivity, not exhaustive correctness, numeric safety or image fidelity. No pixels or peripheral outputs are tested.

## Evidence integrity

The successful sequential run exited 0. It pinned 66 local inputs before execution and checked them again afterward, including source/header dependencies, extracted firmware streams/layout and local reference inputs. The linked code has no undefined symbols. The private report retains exact instruction/data-read traces and source snapshots; it is intentionally not uploaded because it contains vendor-derived data.

Local report SHA-256: `3dff1478ce9bb7d56808820b10d01cf4b03f25e0d5e782bad333fe9bedbbae47`.

The earlier reader-pipeline report and its exact source snapshot are preserved. Its verifier now has an optional observer after successful preparation; the historical report should not be described as a run of that subsequently edited source. A first attempt stopped with SIGILL under the sandbox; the successful run used the existing tested Unicorn backend with approved execution outside that sandbox. No emulator rebuild or old regression rerun was needed.

## Source and dependencies

The two adjacent Python files are reviewed original verification source. They are provided for inspection, **not as a standalone runnable package**. They expect the local research workspace layout, with the files under `scripts/`. Required components include Python, Unicorn with the tested TCI backend, Capstone, pyelftools, Clang targeting ARMv7 and LLD; the imported local firmware, table, interpolation, relocation, container and native-filesystem helpers; eight C/assembly translation units listed in `pipeline.SOURCES`, their headers and generated schema; a locally generated runtime relocation template; locally supplied X-T2 4.41/X-H1 2.15 extracted inputs; two prior parameter-reference reports; and the historical pipeline source snapshot named in the verifier. These dependencies are not all publicly released. No firmware, generated manifest, coefficient table, binary patch or raw execution report is included here.

Local command from that complete research workspace:

```sh
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_xt2_loaded_profile_consumption.py
```

The remaining implementation gap is an actual file-loading owner and a proven safe activation boundary. A successful callback or candidate-eligibility query cannot substitute for worker completion or exclusion of image consumers. Full boot, SD delivery, lifetime, preview/JPEG/movie output and physical camera validation remain open.
