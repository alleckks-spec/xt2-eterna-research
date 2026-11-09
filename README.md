# X-T2 FujiMod port and earlier ETERNA research

## Current direction — 9 November 2026

The active goal is to adapt the existing FujiMod/X-T20 modules to X-T2 4.41 through the ordinary XPP builder and recovery composer. The standalone Sepia→ETERNA direction below is historical and has been superseded.

The current ordinary X-T2 candidate contains six immutable films, NR and the existing JPEG Max XPP module. Its exact ELF passes 33 native JPEG selection/table cases, 356 film cases, 99 context-identity regressions, three film lists/six caption boundaries, NR43/3 and 63-word ELF→SD correspondence. JPEG Max needs only the X-T2 quality property and target/menu bindings; footprint is 148,912 / 196,608 bytes. Complete capture/overlay/writer/copy/service lifecycle and hardware remain unqualified; this is not a completed or camera-accepted port. [Current evidence, original tooling and limitations](research/fujimod-port/README.md).

The underlying original X-T2 table-preparation function separately passes 18 bounded native cases, including all-ones tables at scale 16. [JPEG Max adaptation, binding evidence and original standalone checker](research/fujimod-port/JPEG_TABLES.md).

This update and its original test tooling were prepared with OpenAI Codex assistance. No firmware images, vendor coefficients, private upstream source or binary patch manifests are published.

## Historical research (superseded scope)

**First-stage readiness:** the unchanged `c136d6d7` diagnostic is engineering-admitted for its [single limited first test](research/delivery-probe/FIRST-TEST.txt), subject to the owner's acceptance of the stated residual risks. This is separate from the active ETERNA HOLD. The active image now uses an [81,440-byte compact check](research/minimal-data-protection/README.md), reduced from 780,916 bytes within the same 168-byte reservation; 110 targeted cases pass. No camera test is claimed. Offline placement and live-to-capture integration remain development tasks, not automatically blocked by camera availability.

**Active-candidate memory hardening:** a [new fixed data-protection variant](research/minimal-data-protection/README.md) now executes an image-contained early-root RO/XN step in bounded native startup, preserves the original call and keeps protection through its return. The revised failure path rechecks context even after API errors before authorizing a power request. Full camera boot remains HOLD; the early diagnostic is still the first proposed hardware step, and the goal remains active.

**Next engineering step:** a separate [early delivery/power-request probe](research/delivery-probe/README.md) now avoids native reset and persistence code. Five bounded paths and four original X-T2 power-bit comparisons are checked. This supports proposing a limited diagnostic test, not admission of the active ETERNA image. Physical supply release/ROM behavior remain untested; the development goal remains active.

Independent research targeting Fujifilm X-T2 firmware 4.41, using X-H1 2.15 as the ETERNA reference. Research and this report were developed with assistance from OpenAI Codex. This directory contains publication-ready notes; it is not a complete standalone build or a camera-tested release.

## Current research — 8 November 2026

**Active ETERNA hardware admission decision: HOLD. Do not offer the current Sepia→ETERNA candidate for hardware testing yet.** The offline review freezes its identity and separates bounded checks from unknown ROM delivery, stock persistent writes and unqualified recovery. [Decision, evidence limits and conditions for reconsideration](research/minimal-hardware-candidate/SAFETY-DECISION.md). The prepared protocol first checks boot and return before any ETERNA capture; it is deferred, not permission to test.

A 168-byte early corruption gate now checks every functional patch span before the original reset continuation. Three clean entry comparisons and 98 injected-failure checks pass in bounded execution; the numeric body is unchanged. It is not a global flash lock or a no-brick guarantee. [Original implementation, Fuji practice review and limits](research/minimal-hardware-candidate/BOOT-GUARD.md).

The current MVP target is fixed X-H1 ETERNA replacing the existing SEPIA slot on X-T2 4.41. Additional slots, user profile files and live replacement are deferred; earlier work is retained. The existing local candidate rebuilds byte-for-byte and now has a checked handoff package and [short hardware procedure](research/minimal-hardware-candidate/README.md). It has not booted on our camera and is not a camera-tested release. No physical X-T2 was available.



The safety revision supersedes the earlier candidate: shared parameter reads remain stock, 18 color callsites use private readers, stock menu presentation is restored, and update DAT files are excluded from the SD-test directory. Bounded numeric/store checks pass; full boot, physical capture and global flash-write protection remain unproved or absent. [Current changes and precise safety limits](research/minimal-hardware-candidate/README.md).

The sections below preserve earlier expanded-scope milestones. Their owner/task/file-loading obligations are not prerequisites for this fixed-profile MVP.

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

## Image-contained bootstrap milestone

A new local research image now contains a 488-byte entry wrapper and the C bootstrap linked at its proposed carrier address. Fifteen relocation cases and eleven wrapper ABI/failure cases passed in isolated fixtures. A bounded run from that host-preloaded image executed the wrapper and original native publication/allocation services without a host installer, matched the runtime and all 29 hooks, and preserved the original call's registers, stack and flags. It stopped explicitly at the original return boundary. The active mapping allowed wrapper execution, and monitored immutable carrier bytes survived from host preload to entry.

This narrows the previous placement gap but does not prove original SD transfer, physical cache visibility or lifetime beyond the prefix. The image does not load user profile files. A separate 10,000-round continuation reached an unresolved flash-completion wait before UI initialization; absence of reported emulator faults was not treated as successful full boot.

Reviewed original entry sources and dependency limits are in [research/stage0](research/stage0/README.md). No binary image, vendor data or complete firmware release is published.

## First data-only publication

A new compiled C bank now extracts validated profile data from the file pipeline and publishes it once through an immutable pointer. In the bounded integration fixture, an operation keeps its original snapshot even when publication occurs between the two bytes of a coefficient and between gain and tone. Later custom aggregate/incremental outputs match the direct-data reference; stock output remains unchanged. Revoking candidate eligibility after sealing prevents publication and custom admission.

The fixture no longer copies an executable profile or writes the 29 planned native hook words after loading. Its dispatchers and operation transport are still supplied by emulator callbacks, and the additional bank memory does not fit the frozen resident layout. Native task/exception propagation, cache coherence, resident allocation, development/public admission and reload remain unfinished. [Original C source, verification and limits](research/first-data-activation/README.md) document this implementation milestone without claiming camera readiness.

## Loaded profile consumption

A new bounded integration check carries two laboratory profile files through native queue workers, validation and private preparation, then executes the original tone/gain consumers in the same emulator instance. Six custom comparisons and six stock comparisons passed; both custom outputs change with the loaded container in all three selected contexts, while the tested stock profile stays unchanged.

The host explicitly supplies the prepare-to-consumer transition by copying the candidate and writing hooks in isolated memory. Automatic safe activation, an integrated owner lifecycle, mounted-card access and physical output remain unproved. [Reviewed source, exact scope and dependency limits](research/loaded-profile-consumption/README.md) distinguish the executed path from this supplied boundary.

## Deferred expanded-scope integration work

The loader still needs a real resident owner task, a proven way to exclude filesystem mode changes throughout asynchronous operations, and integration of validated candidates with live activation. Read-only mode snapshots do not establish exclusion. Arbitrarily delayed callbacks from an earlier generation are outside the audited native lifecycle contract.

Carrier placement also remains unproven. Static analysis shows that the original raw-section flash request includes the proposed padding, while the existing SD preload helper skips that later transfer and assumes bytes are already resident. Existing runs preload the image from the host. Neither the original SD file-to-RAM transfer nor continuous preservation of the proposed carrier through startup has been demonstrated.

Full startup, end-to-end image processing, preview, JPEG/movie output and physical camera behavior remain unverified. Selected-function comparisons do not establish numerical safety of arbitrary user coefficients.

## Historical minimal selection regression

The existing SEPIA-alias image now has a bounded native menu-chain regression: 17 menu selections, 14 preserved profiles, 90 ETERNA output vectors, six mode-visibility cases, five global-parameter branches and 255 preserved non-alias selector inputs. Original conversion and RAM setting readback execute; the actual selected public ID remains5. Patched downstream selectors produce processing9 and development16, with explicit fixture handoffs into their capture inputs.

The native live-value-to-capture producer, durable persistence and physical output remain unverified. The image is unchanged, and these results do not complete the custom-profile-loading firmware. [Verifier, per-transition results and reproduction limits](research/minimal-menu-chain/README.md) are published without firmware or vendor-derived outputs.

## Earlier prototype

An earlier local SD experiment replaced SEPIA (public ID 5) with an ETERNA test path. It passed 1,350 tone/gain comparisons, 90 aggregate-block checks, 15 development-selection checks and 145 parameter-read checks in bounded execution. That candidate is now the fixed-profile MVP baseline. It remains separate from the deferred additional-slot and custom-profile work and has never been camera-tested.

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
