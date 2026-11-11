# Production film-loader callback stack in the four-mod configuration

AI-assisted original glue/checkers, November 11, 2026. No camera access.
This closes the dispatcher-stack regression left when returning from the
minimal volatile configuration to the existing four-mod common platform.
It does not close capture admission, storage hardening or the full port.

## Artifact and exact change

`full-timer-build-unverified/` and its `-card` sibling contain the existing
film-sims, noise-reduction, jpeg-max and card-films configuration: the same
33 C sources and 14 libraries as the frozen card-processing build.
`build_full_timer_candidate.py` checks every source digest and restores all
temporary target/library metadata after building with the existing composer.

Only the native software-timer dispatcher literal changes: the X-T2-qualified
stack top is moved down one word so its saved outer-SP push leaves callbacks
8-byte aligned. The literal, preimage and stack bounds are checked against
the authorized stock image. The existing 66 delivery edits remain exact; the
new package has 67. The complete ffboot comparison permits only that one word.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| mods.elf |183584|208845640d4745ff9384911b2f0f38459f830fa87d29adce7c42674d532e9b69|
| region.bin |225892|ca55a1f99aacac92eba1295b278adf7debaf374a8757d221ebd91f4db3ac3070|
| ffboot.bin |46505984|baae4d8d125a50c380161c1c3b4683ac0a101c3445097b3194f7b8c98dd6e372|
| ffsys.bin |2048|b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351|

ELF and region are byte-identical to the earlier card-processing artifact;
the native literal is outside the ELF. Existing resident range, BSS/heap
reservation and branch targets are unchanged. The 225892-byte image still
occupies the existing 229376-byte reservation with 3484 bytes spare; this is
the four-mod footprint, not a reservation claim for further added mods.

## New execution evidence

`verify_full_timer_dispatch.py` reuses the existing native UI1 constructor
fixture and the real compiled callbacks. It invokes `film_loader_boot`,
which registers `film_loader_tick` through the linked lifetime wrapper and
the actual native timer API. Explicit native ticks (121 then120) deliver two
periodic callbacks; each executes the actual `film_cards_tick` observer.
No supplied timer record, diagnostic replacement callback or API success
stub is installed. Provided mode0 keeps file admission closed; no native
file API is reached. The loader remains WAIT and its tick count becomes2.

- Original-literal control: callback SP is4mod8; observer SP is4mod8.
- Delivered-literal run: callback and observer SP are0mod8; all observed
  calls in the dispatcher interval are aligned.
- Fixed maximum observed stack depth88bytes; original84bytes. This is the
  tested mode0 callback path, not a bound for JSON parsing or every callback.
- Native outer task SP and both dedicated-stack sentinels survive.

Reports: `full-timer-check-unverified/dispatch-{original,fixed}.json`.
`verify_full_timer_package.py` verifies ELF/region/SD correspondence, all67
delivered words, the one-word ffboot delta and fresh-build equality for all
four binary artifacts. Rebuild directory: `full-timer-rebuild-unverified/`.
Report: `full-timer-check-unverified/package.json`.

The package checker also pins the existing central-processing, native-still,
NR and JPEG reports by their matching exact ELF hash. Their numeric evidence
is reused for this identical ELF; these checks were not rerun and do not
become timer/scheduler evidence. Earlier artifacts/reports are preserved.

## Upstream comparison and credits

[x70view PR470](https://github.com/justjake/x70view/pull/470), head
`e007961f2a9ad32b96f1136433f91b4ab2597270`, contributes the same dispatcher
stack-word method for X100F. Work by Taylor Chapman (heytchap) and Claude
(Anthropic); that credit is retained here. [PR480](https://github.com/justjake/x70view/pull/480),
head `b92e74a17a122bb9d37f25b3533709cfb8b46a79`, applies it to X-T20.
Both were draft/unmerged when checked by the parent task. Their target
addresses are not used. The X-T2 word and native negative/fixed dispatcher
controls already existed in the minimal-candidate work; this stage places
that proven fix in the active-timer common configuration and exercises a
real production callback instead of the diagnostic menu initializer.

## Reproduction

From the workspace root, with the already prepared authorized local inputs:

```sh
PYTHONPATH="$PWD/.toolchains/fujimod-944d5c8-source/bindings/python/python" \
PYTHONPYCACHEPREFIX=/private/tmp/xt2-full-timer-pycache \
XPP_SEGMENT_LOADER_TOOLCHAIN="$PWD/.toolchains/arm-gnu-13.2-darwin-arm64/bin" \
ports/fujimod-xt2/.venv/bin/python -u ports/fujimod-xt2/build_full_timer_candidate.py \
  --output "$PWD/ports/fujimod-xt2/full-timer-new-build"
```

Runtime checks use `.venv/bin/python`, `PYTHONPATH="$PWD/scripts:$PWD/ports/fujimod-xt2"`,
`LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci"` and `UC_IGNORE_REG_BREAK=1`.
Run the dispatcher checker with `--build ... --output ...`, then again with
`--original-stack` and a distinct output. Run the package checker after a
fresh second build with `--build ... --rebuild ... --output .../package.json`;
the dispatcher outputs beside it must be named `dispatch-fixed.json` and
`dispatch-original.json`. The first sandbox runtime attempt exited132;
the approved local unsandboxed TCI runs completed and produced the reports.

## Open boundary and next step

The check borrows UI1 and supplies logical ticks, REC/settings/calibration
inputs and existing native initialization. It does not schedule the timer
thread, advance hardware time/IRQs, execute a shot, prove capture admission,
exercise JSON parsing at peak stack depth, qualify all timer callbacks,
teardown/concurrent cancellation/cache/MMU or physically write an SD card.
No firmware-ready or hardware-safe claim follows. `accepted=false` remains.

Next: carry this dispatcher word into each further active-timer composition,
then adapt the confirmed X-T2 storage request/callback contracts using the
published guarded implementation. Independently continue the remaining mods;
do not repeat this mode0 stack assay as capture-window evidence.
