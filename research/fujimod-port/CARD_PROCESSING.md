# Card recipes now reach native X-T2 parameter assembly

AI-assisted milestone, 9 November 2026. Goal remains active; accepted=false.

The existing four-mod ordinary GNU build now permits card recipes under a paired reader/publisher guard. Only processing.c and cards.c are adapted; the remaining 31 C sources, 14-library graph, existing table, parser, observer and build/composer remain the same. No service, task, allocation or recipe-version store is added. Two shared words (8 bytes) track readers and pending publication.

Exact ELF: `208845640d4745ff9384911b2f0f38459f830fa87d29adce7c42674d532e9b69`.
Resident: 225892 bytes at 0x1388000, within the existing expanded 229376-byte reservation; 3484 bytes spare. 66 delivery edits. SD ffboot SHA256: `956031ff4c01e759b705658f590baea903ca3ef4cb272f226b4cbb90d9414bc7`; ffsys remains `b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351`.

## Executed evidence

- Supplied original JSON -> actual parser/store/publisher -> native UI transport -> property selection -> native 0x1565c20 body produces a full 5748-byte parameter block. Both matrices, both tone curves, chroma and luma match independent JSON expectations; output differs from Provia. Native input class enable fields, calibration and borrowed UI1 context are fixtures, not full startup.
- Reader first: pause the actual API after earlier groups; original publisher defers without changing the table; the same output remains entirely A. Existing observer explicitly retries; next output is entirely B.
- Writer first: pause genuine partial publication; a reader begins; writer finishes mid-read. Reader stays stock-only throughout, with zero reads of the card coefficient table. Next assembly uses complete A. These are controlled single-emulator interleavings, not physical parallel cores or scheduler ownership evidence.
- Seven-argument still wrapper forwards register/stack arguments and return correctly. An explicitly declared surrogate intercepts its stock trampoline; the native 0x170cda0 body is NOT qualified.
- Exact same ELF passes NR43/register +3menu cases, JPEG33 +3menus, and all66 ELF/region/SD word checks. Previous356 film/99 identity cases are NOT transferred.

## Sources and reports

Original tools: prepare_card_processing.py, build_card_processing_candidate.py, verify_card_processing.py, verify_card_processing_regressions.py and xt2_card_reader_reference.h.
Private generated derivatives: card-processing-inputs/. Artifacts: card-processing-build-unverified/ and its -card sibling. Reports: card-processing-check-unverified/verification.json, card-processing-regressions-unverified/{nr,jpeg}/verification.json and regressions.json. Previous frozen db56c69c base remains unchanged.

Direct A32 caller analysis reaches two coherent API boundaries, 0x1565c20 and 0x170cda0. This is not proof of every indirect consumer, task, native writer/copy, cleanup, fairness, cache coherence or exposure-time recipe snapshot. Profile identity occupies hex145..147 within a hex148-byte class; this does not establish all native copy ownership.

Next concrete gap: execute the actual noncentral still body and its consumer chain with identified inputs, then qualify full storage/startup/lifetime and eventually the camera. Do not expand the emulator or claim a finished port from the wrapper surrogate. Firmware, private C, coefficient tables, disassembly and raw patch manifests stay local.

## Reproduction and publication limits

These original tools are adapters for an already prepared local `ports/fujimod-xt2` checkout, not a standalone public build. Place the Python tools/header there alongside the earlier published helpers. Required local inputs include pinned authorized upstream x70view9d22f1b, FujiMod944d5c8 Python bindings, Arm GNU13.2, licensed locally supplied X-T2 firmware, prior frozen card-films integration and its source paths, existing native assay helpers/scripts, Unicorn/Capstone/pyelftools and the initial calibration/data fixtures. Absolute paths in the local freeze must match that checkout. Prior private derivatives, target preimages, recipe constants, ELF, SD images, raw call-graph/disassembly and binary manifests are deliberately excluded.

Preparation clones two previous private derivatives; building temporarily selects those sources and two API bindings, invokes ordinary build/compose, then restores metadata. `verify_card_processing.py` validates and reuses the previous frozen UI fixture prefix; it runs native central assembly and controlled interleavings. `verify_card_processing_regressions.py` reuses existing NR/JPEG/artifact checkers with the new66-word candidate. The seven-argument still test explicitly substitutes its stock trampoline; do not interpret it as native still-body or capture proof.

No claim is made that every dependency is publicly available or that the above constitutes a reproducible standalone distribution. This publication contains original tooling and reviewed notes only, prepared with OpenAI Codex assistance.
