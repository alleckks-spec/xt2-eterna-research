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
    cmp r1, #0
    beq 3f
    cmp r2, #0
    beq xt2_minimal_guard_failed
    adds ip, r1, r2
    cmpcc ip, #0x03000000
    bhs xt2_minimal_guard_failed
2:
    ldrb ip, [r1], #1
    eor r3, r3, ip
    mul r3, r4, r3
    subs r2, r2, #1
    bne 2b
    b 1b
3:
    cmp r3, r2
    adreq r0, xt2_minimal_led_config
    beq xt2_minimal_led_body
xt2_minimal_guard_failed:
    cpsid aif
4:
    b 4b
xt2_minimal_guard_ranges:
    /* Eight address/length descriptors. Zero address terminates; the
     * simultaneously loaded second word is the expected checksum.
     * No checked range may start at zero. Saves one load and one word. */
    .space 8*8
    .word 0
xt2_minimal_guard_expected:
    .word 0
