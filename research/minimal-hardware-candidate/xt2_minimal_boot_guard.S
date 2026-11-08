/* Original fixed-image corruption check. No stack, MMIO, flash commands,
 * allocator, file loader or installer. Runs while the existing LED entry has
 * saved r0-r4, ip and flags; all other registers, including LR/SP, are untouched.
 * Trusted entry/instructions are a precondition, not a secure-boot root.
 */
.syntax unified
.arm
.section .text,"ax",%progbits
.global xt2_minimal_guard_entry, xt2_minimal_guard_failed
.global xt2_minimal_guard_ranges, xt2_minimal_guard_expected
xt2_minimal_guard_entry:
    adr r0, xt2_minimal_guard_ranges
    movw r3, #0x9dc5
    movt r3, #0x811c
    movw r4, #0x0193
    movt r4, #0x0100
1:
    ldmia r0!, {r1,r2}
    cmp r2, #0
    beq 3f
    adds ip, r1, r2
    bcs xt2_minimal_guard_failed
    cmp ip, #0x03000000
    bhi xt2_minimal_guard_failed
2:
    ldrb ip, [r1], #1
    eor r3, r3, ip
    mul r3, r4, r3
    subs r2, r2, #1
    bne 2b
    b 1b
3:
    ldr r2, [r0]
    cmp r3, r2
    bne xt2_minimal_guard_failed
    adr r0, xt2_minimal_led_config
    b xt2_minimal_led_body
xt2_minimal_guard_failed:
    cpsid aif
4:
    b 4b
xt2_minimal_guard_ranges:
    /* Fixed 2-word descriptors; the builder supplies all seven entries. */
    .space 7*8
    .word 0,0
xt2_minimal_guard_expected:
    .word 0
