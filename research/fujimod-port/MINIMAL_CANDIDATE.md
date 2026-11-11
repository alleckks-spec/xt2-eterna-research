# Single-ETERNA X-T2 4.41 candidate

AI-assisted original work, November 11, 2026. A minimal integrated candidate is
prepared for the first hardware trial. **No camera was available.** All execution
results below are bounded ARM emulation or host artifact checks, not hardware.

The existing FujiMod/XPP builder and recovery composer compiled one film-sims
module: ETERNA, I.Q./Fn/Q stock-choice menus, caption support, stock return, and
the existing late policy hook. NR, JPEG-max, card films, WB and OTA are excluded.
Nineteen C sources and twelve libraries remain in the compilation dependency
graph. Selection is deliberately volatile: menu transactions update RAM; the
settings service is not started and commits do not request SD saves. The linker
removes the mod storage and timer implementations. RAM JSON codecs may remain.
This does not fix the complete card-backed port's capture admission or persistence.

## Timer dispatcher and profile lifetime

The X-T2 dispatcher switches to its own stack, then saves one word before calling
a compiled callback. The stock top gives callback SP4mod8. The candidate's one
literal adjustment gives SP0mod8. The native constructor fills 8 KiB, while the
observed downward dispatcher stack occupies the lower 4 KiB page. The same final
ELF's menu-enrollment function was registered as a diagnostic timer callback;
it is not scheduled that way by the production candidate.

`verify_timer_dispatch.py` executes native start and dispatcher code, observes
every BL/BLX alignment, stack writes, sentinels and restoration of the outer SP.
The stock-literal control reproduces SP4mod8; the candidate gives SP0mod8, with
144 bytes maximum observed depth and 142 stack stores inside the checked page.
A simulator fault is not required to detect the ABI violation. Ticks are explicit,
the outer task is borrowed UI1, and IRQ delivery or timer-thread scheduling is
not claimed. Other callbacks' worst-case stack depth remains unqualified.

New profile analysis identifies a real 0x148 clear before selection, and two
post-mapper field copies ending before the three identity bytes. Native clear/
default and actual post-mapper copy fragments preserve the documented bounds.
No conflicting writer was found on these named paths; a whole-object copy was
not invented. Indirect owners, all copies and continuous capture lifetime remain
open. `verify_profile_native_transfers.py` checks the actual fragments with explicit
input frames; it does not pretend to execute the complete input-object builder.
The instruction inventory and generated firmware analysis are not distributed.

## Exact candidate checks

- ELF, region, all 48 delivered words and SD file hashes correspond. A second
  build reproduces the ELF, region and both SD files byte for byte.
- The native policy body returns nine times, with one init and one late-init.
  Forbidden modes start nothing. Every row in all three native lists is reached
  using native cursor packets. Cancel restores the previous selection and repeated
  commit is deduplicated. Physical buttons and complete rendering are untested.
- There are 117 processing function cases on this exact ELF, retaining the
  existing explicit calibration/mode and three uncontended transport fixtures.
- The actual still parameter body executes PROVIA -> ETERNA -> PROVIA on the
  **same profile object, without intermediate host clear/defaults**. The native
  stock path removes the prior ETERNA marker. Four ETERNA groups match the linked
  recipe, and stock output before/after matches. This is not a JPEG or color test.
- Delivered BSS/heap edits preserve the reserved payload; crossing allocation
  fails. Mapping arguments are observed without claiming installed MMU/cache state.
- `audit_minimal_storage.py` verifies selected source hashes and finds no live
  mod storage/timer implementation, direct native branch (including conditional
  branches), or aligned native API pointer word. This is not a general indirect
  whole-firmware call-graph proof. Stock JPEG writes remain active.

The ETERNA menu key remains in RAM; native film storage contains PROVIA0. An
unrecognized reader retains the native key. The custom-setting editor film table
is not bound. C1-C7 snapshots of ETERNA are not supported, and complete native
C1-C7/power-off serializers have not been executed.

A separate native X-T2 token assay allocates sixteen handles, observes zero on
exhaustion, releases one and allocates a new handle in its slot. A real successful
open callback with handle0 was **not** reproduced. The larger cardio source does
not reject that combination. Its own watchdog is excluded in XPP, and the settings
BUSY watchdog only counts ticks. Those paths are absent from this minimal ELF,
not declared fixed or capture-safe. No X100F timing limits are asserted for X-T2.

## Artifact identity and use

| Local artifact | SHA256 |
|---|---|
| ELF | 477de045122f204f070292fe75139840ff3dcfb4db60a041108c29a208568d47 |
| Region | dd268535357619fbc4ea2ed76cae842fa047b71e6de747854c7e36fe8407342e |
| ffboot.bin | b519e6f76697eda0769d6a3c6a45886f34e570738a13e9d1af3751e9dd98feea |
| ffsys.bin | b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351 |

The region is 74,856 bytes. The local package contains the two composer-produced
SD files, exact ELF, SHA256SUMS, build command, evidence and a short staged test
protocol. Firmware, binary patches, extracted coefficients, disassembly, generated
source derivatives and private upstream material are not distributed here.

The published Python files are original orchestration and checks. They require
the locally prepared adapters, existing assay dependencies, authorized firmware
inputs, pinned FujiMod SDK/toolchain and TCI backend. This is not a standalone
source release. `build_minimal_candidate.py` uses the existing private preparation
step; it does not replace the builder or composer. `audit_minimal_package.py`
binds the resulting evidence to the final ELF and a separate rebuild without
rerunning ARM checks. Output directories must not already exist.

Full ROM/SD startup, scheduled startup order, hardware MMU/cache/lifetime, sensor
capture, encoder/JPEG, color accuracy, shutdown and persistent settings integrity
remain unproven. The candidate remains **accepted=false**. The next single camera
action is one SD start to observe ETERNA in the menu, without taking a picture.
Early carrier LED alone does not prove mod initialization; ETERNA rows and Fn
caption provide later milestones. Only after a normal first start does the local
protocol proceed to stock/ETERNA/stock JPEGs and an ordinary restart without SD.
