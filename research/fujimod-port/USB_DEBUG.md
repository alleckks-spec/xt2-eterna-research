# Volatile XPP USB debug variant on X-T2

The selected existing X-T20 implementation is now adapted and built as a
separate six-mod configuration. It consumes Fn action10 (upstream IMAGE SIZE),
enables the live F7 byte in unplugged REC, and restores it only after the native
closed-debug class state is supplied. Physical Fn assignment/routing, an actual
USB connection and the host debug protocol remain unverified.

Exact ELF: `d0ed134c0a6ed84ec81d7728b17238154f2d765e830fc64600a6c3aceef49345`.
Canonical build: `usb-debug-pinned-build-unverified`, fresh build:
`usb-debug-pinned-rebuild-unverified`.39sources,14libraries,6mods,73deliverywords;
region245720bytes in the existing262144-byte reservation,16424bytes spare.
ELF, region, ffboot and ffsys reproduce byte-for-byte. ffboot SHA256:
`3052a117dd345af24b4c2fb42d6c5d4266d3615644428db6e00ba610eca4dc08`.

Source is pinned to x70view9d22f1b41c70c20407158e699f2583ac4907ff16:
debug.c blobc9bc0cf012b7d073d0c225fb2752b483df388ab0 and
entry.S blob350477743ab9d8b69307562bc06bc388e4073ff6. These private inputs,
adapted upstream C and native binding disassembly stay local. The original
public verifier requires the prepared local workspace/artifacts; no firmware or
upstream redistribution permission is inferred.

X-T2 bindings were qualified from native callers/producers, not address deltas.
The physical VBUS getter actually reads GPIO1/pin14; its native debounce path
feeds the USB context bit0. Native driver/context disconnected states are2;
native cable-decision and class fields have separate owners. F7 native getter
and RAM-only setter share the native initialized cache pointer. The adaptation
uses byte width for the class because its native producer/consumers are byte
operations; the donor reads a whole word. Adjacent nonzero class bytes are a
positive control. The donor assembly entry is retained, with target branch and
native epilogue bindings and its existing instruction preimage check.

`usb-debug-pinned-check-unverified/verification.json`:16controls PASS, plus four
native GPIO reads. Controls cover non-REC no-private-write, all eight refusal
guards, enable plus16repeat entries, restore plus16terminal entries, explicit
post-store memory corruption/readback failure, and delivered Fn branch through
the native epilogue. The native RAM setter/getter execute; no successful API
reply is substituted. The native cache-pointer initialization prefix executes,
while cache contents and USB state are declared function inputs. This is not
complete USB initialization, full startup, cable detection timing or security
qualification of the debug protocol.

On the same exact ELF: native SAVE DATA UI8+1rows/ON/OFF/cancel/commit PASS;
seven-record film SAVE49cases PASS; formatter14/codec4/BSS/heap PASS; film
processing356/identity99, NR43 and JPEG33 checks PASS. Existing native timer
original/fixed controls and24callback controls PASS. Commit/cancel/deduplication
and actual missing-driver error retirement PASS with explicit card_1 initial
choice and merged save_data false. The newer positive native SDK filesystem
work is separate and is not silently transferred to this USB artifact.

Early builds had an extra final newline introduced when materializing the
private inputs. Canonical builds validate exact Git blob hashes; all four
binaries are identical to those exploratory builds. An early write-check CLI
invocation supplied the wrong initial choice; its failure is retained separately,
and the required card_1 invocation passes. No firmware fix was inferred from
either fixture issue.

The existing five-mod menu package remains available. This USB variant does not
preserve the ordinary IMAGE SIZE behavior on the consumed Fn action. Shared
usb-debug-menu is a different unresolved upstream variant; it is not included.
Next verify native USB startup/connection contracts where software permits and
combine only compatible completed mods. Physical host connection, persistence,
power-off, ROM-to-SD boot and camera acceptance remain open. Full port unfinished.
