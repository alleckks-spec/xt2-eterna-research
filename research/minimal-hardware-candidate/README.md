# Fixed ETERNA / SEPIA hardware candidate

Original research and tooling developed with OpenAI Codex assistance. The current MVP scope is fixed X-H1 2.15 ETERNA replacing SEPIA in X-T2 4.41. Additional slots, user profile files and live replacement are deferred; earlier work is retained.

The existing local image is unchanged: SHA-256 `0f14244971768d783e09d4eb21fe59e60262ea183b938d31ff1fff170caceddf`, 46,505,984 bytes, 8,705 changed bytes relative to the pinned stock SD carrier. Rebuilding from current sources reproduced the delivered image and the complete edit sequence. Only an overconfident builder comment was corrected: the preload helper skips a later raw reload; this does not establish original ROM delivery or retained padding lifetime.

A new standard-library integrity gate replays all 25 sequential manifest writes, checking each preimage, then compares the whole resulting image. It checks the original SD header and official update identities, unchanged carrier controls and the existing public-ID conversion table. The local handoff ZIP was refreshed with the hardware procedure, both earlier bounded reports, current build evidence and checksums; archive CRC and all member hashes passed. This closes package/rebuild ambiguity, not a boot or capture gap. No earlier ARM regression was repeated.

Run with locally supplied inputs:

```sh
python3 audit_eterna_minimal_package.py /path/to/eterna-minimal-sd-candidate /path/to/stock/ffboot.bin
```

The candidate directory must contain `ffboot.bin`, `ffsys.bin`, the original `FWUP0010.DAT` and the private `manifest.json`. Those files and donor-derived data are deliberately not published. The gate checks this one pinned candidate; it is not a builder or a standalone firmware reproduction package. Reports and checksums are provenance, not a signature or proof of camera safety.

Use [the short hardware procedure](HARDWARE-CHECK.txt): establish stock SD boot first, replace only `ffboot.bin`, compare SEPIA/PROVIA/SEPIA under fixed settings, repeat startup, then verify stock behavior after removing the card. The boot gesture is based on the external [X-T2 stock report](https://github.com/justjake/fujimod/pull/163), not our own hardware evidence. A colored result demonstrates a changed path, not exact X-H1 rendering equivalence.

The next useful integration result requires a camera: original SD-to-RAM transfer, patch survival, selected-profile propagation through capture and actual JPEG output remain unverified. The existing [menu regression](../minimal-menu-chain/README.md) explicitly supplies capture/development handoffs. No new host fixture is being treated as a substitute for that missing evidence. No modified flashable DAT, camera-tested claim or guaranteed recovery is provided.
