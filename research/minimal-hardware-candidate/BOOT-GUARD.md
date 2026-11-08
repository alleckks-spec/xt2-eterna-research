# Early corruption gate and Fuji safety-practice review

Original source and research developed with OpenAI Codex assistance. This is bounded research, not a camera safety certificate. The fixed SEPIA-alias image now has SHA-256 `c1aee308e0b6c54dfede3de4c48885223365b2b8e90c282c74d87a112d58fc10`. The earlier `47a93766...` image remains the numerically verified body reference. No new ZIP was produced.

## Practices inspected in existing Fuji work

- FujiMod's [download code](https://github.com/justjake/fujimod/blob/main/apps/web/src/patch/download.ts) separates a two-file SD boot from the installable format that includes an update DAT. Its [patch interpreter](https://github.com/justjake/fujimod/blob/main/apps/web/src/patch/patcher.ts) checks source identity, patch-program hash, command bounds and output hashes. These are host construction checks, not proof that the camera prohibits flash writes.
- The public [early ARM LED implementation](https://github.com/justjake/fujimod/blob/main/crates/recovery/src/early_led.rs) reserves a checked non-overlapping region before application RAM, saves incoming scratch registers/flags and resumes the original entry. Our pinned X-T2 stock carrier uses ten configuration rows. The unused fourteen-row capacity is exactly 168 bytes, ending before the existing LED loop. The new gate reuses only that existing space; it adds no file loader, allocator or new RAM reservation.
- [X-T2 hardware report #163](https://github.com/justjake/fujimod/pull/163) confirms stock SD boot and access to the official update screen. It does not qualify this ETERNA image. The [recovery page](https://www.fujimod.com/recovery/) uses a distinct official-flashing step; that is not proof of guaranteed restoration of our setup or per-body data.
- The older [FujiHack recovery discussion](https://github.com/fujihack/fujihack/issues/9#issuecomment-1126826375) explicitly lacked a demonstrated recovery path at the time. It is historical caution, not evidence against the later X-T2 stock SD report. No public success report establishes universal immunity to bricking.

Only the public installation/recovery sources and our locally supplied stock X-T2 code were inspected. This is not a reverse engineering claim for FujiMod's entire non-public modification implementation. Discord authentication had expired; no new Discord messages were read or posted and its successful cursor was preserved.

## Implementation

The existing early LED entry's internal branch now visits a 168-byte stackless ARM checker before any original LED MMIO or the original reset continuation. It hashes 80,348 bytes spanning every functional ETERNA patch span plus its own code/range table. The expected checksum word is outside its hashed range. Fixed range descriptors are checked for addition overflow and an end below the declared low RAM bound before any described byte is read.

The checksum is FNV-1a32 for accidental corruption, **not a signature or secure boot**. On success the original LED body runs, restores the saved incoming state and resumes its original reset target. On mismatch the checker masks asynchronous abort/IRQ/FIQ and loops before those operations. It does not pretend to restore stock from a partially loaded image or return a fabricated successful write status.

The host integrity gate still pins the entire image SHA-256, replays every emitted write, preserves shared parameter readers and rejects a DAT in the SD-test directory. A correct checksum says the expected bytes arrived at this checkpoint; it does not prove the bytes implement correct hardware behavior.

## Executed verification

- Compiled ARM checker matches the current source and fits the exact existing reservation.
- Three incoming flag patterns preserve r0-r12, SP, LR and flags through the entire stock LED continuation. The same explicit GPIO register-storage fixture gives identical final values for stock and guarded images. The correct original resume address is read from the pinned stock literal; no reset address is assumed.
- Ninety-eight injected failures stop before the LED body and original reset continuation. These include first/last-byte mutations of every functional edit, expected-checksum corruption, loss of the whole data allocation, zeroed resident tail, mixed stock data, invalid addresses, overflow lengths and a corrupt terminator. No MMIO reads/writes occur on these tested failure paths, and interrupts are masked.
- Full-image comparison proves that the formerly verified numeric/selector/table bytes are unchanged. The only differences from the prior image are the early internal branch and the checker in unused LED configuration space. The 1,350-case numeric grid was not repeated for an early-entry-only change.

This is a host-preloaded, bounded native entry test. It stops at the original reset continuation, before executing full stock startup. GPIO transport is a declared fixture; ROM file transfer, physical caches, watchdog timing, multicore entry, later overwrite lifetime, full boot and sensor/ISP/JPEG output are not demonstrated.

The entry branch and functioning checker remain trusted assumptions. Arbitrary checker-code corruption or bypass of its entry can defeat it; FNV has multibyte collisions. The check does not monitor later CPU/DMA writes. A failed image does not show a normal UI; physical power-off/removal behavior has not been tested. Do not leave a failed experiment powered unattended.

## Flash prohibition decision

Original X-T2 page programming and erasure use separate driver routines with four and three observed direct callers respectively. The inspected existing erased-store scenarios reach both during native storage initialization. A bounded original caller block propagates supplied native program status `-255` as an error; returning success instead would hide an operation that did not happen. This establishes a behavioral change, not a complete boot-failure or success prediction.

The public [X-T2 flash part](https://github.com/justjake/fujimod/blob/main/catalog/parts/xt2-flash/part.json) still lacks JEDEC identity, erase size and page size. MMU read-only mapping of the aperture would not disable commands issued through the controller. A software-only block at one upper call or a guessed hardware status/write-protect bit cannot be represented as complete protection. A generic denial is therefore **not installed**. The intact candidate retains ordinary stock persistence behavior; failed integrity checks prevent this tested entry from reaching it.

No whole-camera or no-brick guarantee follows. The next missing qualification is physical stock/candidate boot and output, including retained patch memory and observed nonvolatile behavior; no new emulator framework is made a prerequisite.

## Source and dependencies

Adjacent `xt2_minimal_boot_guard.S`, `xt2_minimal_boot_guard.py` and `verify_xt2_minimal_boot_guard.py` are original source. Copy them into `scripts/` in the full local research workspace. The builder invokes the helper after constructing the fixed SEPIA body; the helper checks the original early branch target and unused capacity, and the builder independently checks coverage and write bounds.

The helper needs Clang, the locally installed ARM-capable LLD and pyelftools. The bounded verifier additionally needs Unicorn TCI, the existing local builder helpers, pinned stock SD files, the new private image/manifest, and the exact prior `47a93766...` image at `research/minimal-before-boot-guard/ffboot.bin`. These private inputs and vendor instructions/data are deliberately not published; this is not a standalone firmware build package.

```sh
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_xt2_minimal_boot_guard.py
```
