# X-T2 ETERNA backport research

Independent research targeting Fujifilm X-T2 firmware 4.41, using X-H1 2.15 as the ETERNA reference. Research and this report were developed with assistance from OpenAI Codex. This directory contains publication-ready notes; it is not a complete standalone build or a camera-tested release.

## Current result — 8 November 2026

An experimental SD boot image has been built locally. It reuses the existing SEPIA selection (public ID 5) for an ETERNA path rather than extending the camera's profile enumeration. The prototype redirects the relevant selection and parameter reads and uses donor tone/gain tables. Two menu descriptors label the replacement `ETERNA (TEST)`; other display or metadata paths may still identify it as SEPIA.

Bounded execution of selected ARM functions produced passing comparisons:

| Check | Cases |
| --- | ---: |
| Tone/gain comparison | 1,350 |
| Aggregate blocks | 90 |
| Development selection | 15 |
| Parameter reads | 145 |

In the tested functions and modes, ETERNA matches the donor reference and the other 14 profiles retain stock behavior. These checks do not prove end-to-end image processing or full camera operation.

The candidate modifies 8,705 bytes. Its SHA-256 is `0f14244971768d783e09d4eb21fe59e60262ea183b938d31ff1fff170caceddf`. No modified flash-update DAT has been produced for this candidate. The local SD package contains an unchanged official update alongside the experimental boot image.

## Unverified behavior

No physical X-T2 was available for this work. Booting this candidate, memory lifetime, menu behavior, JPEG output, preview, movie processing and return to stock operation remain unverified. Code and data currently occupy section alignment/allocation padding; absence of overlap in the inspected image does not establish that these areas remain available throughout camera operation.

The next development task is to validate placement against startup and runtime writes and prepare a narrowly scoped hardware experiment. Full peripheral emulation is not a prerequisite for this work. Computer-editable recipes and additional film simulations remain separate future tasks, not implemented features of this prototype.

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
