# Existing FujiMod XPP SD backend: dependency check

AI-assisted original probe and notes, 2026-11-09. This does not qualify an
X-T2 firmware build, startup, filesystem mount, settings write or physical card.

The pinned FujiMod SDK at `944d5c865d4def32663c1dad24d54ac3001f3f6e`
already contains an XPP SD controller and FAT32 medium. The previously installed
Python extension was built without the default emulator feature. Building that
feature required no source or Cargo.lock changes and no new device model.
The ordinary firmware builder's existing extension was preserved separately.

`probe_existing_sdk_sd.py` uses the SDK's native Cortex-A7 board, strict XPP
SD device and FAT32 formatter. An original A32 program performs 11 SD commands
and reads a 512-byte MBR through PIO. The run completed 1,264 instructions;
all command completion bits were present, no command error bits were present,
the read sector exactly matched the host formatter and transfer-complete was
set. The synthetic SD base and instruction ticks are explicit test inputs,
not inferred X-T2 hardware wiring or camera timing. There are no Python MMIO
adapters, firmware bytes or success-return hooks in this probe.

A separate host-only check round-trips SETTINGS.JSN through CardMedium export
and restore. This is SDK medium serialization, **not firmware persistence**.
The current firmware package and its earlier qualified checks are unchanged.

## Dependencies and invocation

Use a locally supplied checkout of the pinned FujiMod source with its pinned
submodules. On the tested Apple Silicon host the build used Rust 1.99.1,
CMake 3.31.6, pkg-config 3.0.7, jpeg-turbo 3.1.3 and Python 3.14. The native
module is built with the default feature set, including emulator:

```sh
cargo build --locked --release -p fujimod-python-module --jobs 2
```

Set PYO3_PYTHON to the intended Python executable and ensure CMake, pkg-config
and libjpeg are discoverable. Once dependencies are cached the same build
works with --offline. Use the existing FujiMod Python package with the resulting
release native library installed as fujimod/_native.abi3.so in a separate package
copy; do not overwrite a frozen builder installation. The probe requires no
firmware, private x70view inputs or Arm compiler:

```sh
PYTHONPATH=/path/to/emulator-enabled-sdk/python python probe_existing_sdk_sd.py
```

The probe writes its small diagnostic report beside the script. Neither a
compiled SDK nor the upstream source is distributed here. Existing SDK behavior
is attributable to FujiMod, not implemented by this project. The next relevant
integration is the actual X-T2 filesystem bootstrap against this backend;
the earlier write-open driver-registration failure remains unresolved.
