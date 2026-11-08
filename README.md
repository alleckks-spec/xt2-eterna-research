# X-T2 ETERNA backport research

Independent research targeting Fujifilm X-T2 firmware 4.41, using X-H1 2.15 as the ETERNA reference. Research and this report were developed with assistance from OpenAI Codex. This directory contains publication-ready notes; it is not a complete standalone build or a camera-tested release.

## Current research — 8 November 2026

The current development target is an additional ETERNA slot and loading user-editable color profiles on X-T2 firmware 4.41. This is unfinished firmware research, not a downloadable working release. No physical X-T2 was available.

A bounded emulator run now executes one compiled C bootstrap in the original root task. It uses original firmware allocation, page protection, cache-maintenance and scheduler functions. The generated runtime and all 29 installed hooks match the offline reference; original page flags, core affinity and stack position are restored. The run stops immediately after bootstrap success, before continuing startup. It does not demonstrate full boot.

The bootstrap used 428 bytes of the existing root stack, leaving 480 bytes to the inspected allocation boundary. Its code and immutable manifest were preloaded by the host into declared laboratory memory. No calls to the observed host memory-write binding occurred during the C call; this instrumentation does not cover previously cached bindings. This is not proof of physical cache coherence or delivery from SD.

The profile path has a strict 3,008-byte container, validation, runtime relocation and staging into a private candidate. Firmware-function tests cover tone, gain and parameter consumers. The file adapter handles inline and deferred callbacks and keeps primary errors separate from cleanup errors. Generation tokens prevent a previously completed candidate from becoming eligible again when the same buffers are reused.

Latest bounded checks include:

| Check | Evidence |
| --- | --- |
| Native C bootstrap prefix | One successful call; 29 matching hooks; eight original page policies restored |
| Reader adapter | 58 host cases, 58 ARM cases and seven native-address ABI fixtures |
| Private profile pipeline | 33 cases |
| Generation reuse | 18 cases, with consumer checks at three runtime bases |
| Failed-open recovery | 10 cases; prior error preserved before retry |

The file tests use explicit filesystem boundary fixtures. They are not successful reads from a mounted camera card. Failed-open retry is permitted only after the audited normal read-only path reports a nonzero status and zero handle, under its exact-once callback contract. Ambiguous handles, pending operations, protocol errors and uncertain cleanup remain quarantined.

## Remaining integration work

The loader still needs a real resident owner task, a proven way to exclude filesystem mode changes throughout asynchronous operations, and integration of validated candidates with live activation. Read-only mode snapshots do not establish exclusion. Arbitrarily delayed callbacks from an earlier generation are outside the audited native lifecycle contract.

Carrier placement also remains unproven. Static analysis shows that the original raw-section flash request includes the proposed padding, while the existing SD preload helper skips that later transfer and assumes bytes are already resident. Existing runs preload the image from the host. Neither the original SD file-to-RAM transfer nor continuous preservation of the proposed carrier through startup has been demonstrated.

Full startup, end-to-end image processing, preview, JPEG/movie output and physical camera behavior remain unverified. Selected-function comparisons do not establish numerical safety of arbitrary user coefficients.

## Earlier prototype

An earlier local SD experiment replaced SEPIA (public ID 5) with an ETERNA test path. It passed 1,350 tone/gain comparisons, 90 aggregate-block checks, 15 development-selection checks and 145 parameter-read checks in bounded execution. That prototype is separate from the current additional-slot and custom-profile work, and was never camera-tested. It is not the requested completed custom-profile firmware.

## Reproduction and publication boundary

The full local workspace currently holds the builder, execution harness, original firmware inputs and donor-derived data. This directory deliberately contains no firmware, extracted coefficients, disassembly corpus, binary patch or private community conversation. It does not yet contain everything required to reproduce the candidate. A later source release should extract original tooling, document locally supplied inputs, and respect the destination project's contribution rules.

Do not copy the entire parent workspace or the local SD ZIP into a public repository.

## Collaboration

Maintain project-specific research in an independent repository. Send reusable locators, host-tool fixes and focused tests as small pull requests to [justjake/fujimod](https://github.com/justjake/fujimod), following its current contribution instructions. Work involving the project's private research repository belongs there under its own rules. Access was requested through the community's standard contribution thread; development does not depend on a reply.

Community updates should describe a concrete result, how it was checked and what remains unverified. No repeated pings or requests for developers to reconstruct our work. Attribute AI-assisted text and work explicitly, as requested by the maintainer.

## Public references

- [X-T2 SD boot report, PR #163](https://github.com/justjake/fujimod/pull/163): external hardware evidence for stock SD boot; not evidence for this patched candidate.
- [X-T2 service-mode work, PR #170](https://github.com/justjake/fujimod/pull/170).
- [X-T2 research, issue #171](https://github.com/justjake/fujimod/issues/171).

This is an independent project, not an official FujiMod or Fujifilm release.
