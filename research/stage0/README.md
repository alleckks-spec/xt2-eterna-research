# Experimental early entry support

Original research source, developed with OpenAI Codex assistance, targeting X-T2 4.41 only. These files are not a complete firmware build or a camera-tested release. They contain no vendor instructions, coefficients or binary image.

The entry wrapper preserves r0-r12, LR, SP and condition flags, performs native publication calls through C, then tail-calls the original routine. Link entry at 0xdf7900 and define xt2_carrier_original_call = 0xcf83cc. The separately linked bootstrap must have entry 0x781000 and fit 0x2000 bytes. The trusted template and configuration are absent here; do not attempt to run these sources on a camera.

Dependencies: ARMv7-A ARM-state freestanding C11/assembly compiler with soft-float, the accompanying interface headers, the unpublished bootstrap implementation and generated trusted runtime manifest, locally supplied matching firmware, and the research execution harness. This source subset does not reproduce a full image. No runtime code or pointers come from user profiles.

Local validation: 488-byte wrapper; eleven intercepted-boundary cases check call order, register preservation and failure stop. A separate host-preloaded-image native prefix executed this wrapper and the 8,112-byte C bootstrap, checked generated payload and 29 hooks, and observed return through the original call. The prefix stops there. Original SD transfer, physical cache visibility, long-term memory ownership, full startup and profile-file loading remain unproven. On failure the wrapper stays at the early boundary; recovery behavior on hardware is untested.
