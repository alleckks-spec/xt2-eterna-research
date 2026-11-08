/* Original diagnostic only: verify inert profile placement, show stock LED,
 * request supply release before native reset/startup. No stack or flash API.
 * Source and trusted entry are preconditions; not an authenticated boot root.
 */
.syntax unified
.arm
.section .text,"ax",%progbits
.global probe_entry, probe_failed, probe_poweroff, probe_idle
.global probe_ranges, probe_expected, probe_delay
probe_entry:
    cpsid aif
    adr r0, probe_ranges
    movw r3, #0x9dc5
    movt r3, #0x811c
    movw r4, #0x0193
    movt r4, #0x0100
1:
    ldmia r0!, {r1,r2}
    cmp r2, #0
    beq 3f
    adds ip, r1, r2
    cmpcc ip, #0x03000000
    bhs probe_failed
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
    bne probe_failed
    adr r0, probe_led_config
    b probe_led_body
probe_failed:
probe_poweroff:
    mov r2, #0x200000
probe_delay:
    subs r2, r2, #1
    bne probe_delay
    mov r0, #4
    movt r0, #0xfff1
    ldr r1, [r0]
    bic r1, r1, #1
    str r1, [r0]
    dsb sy
probe_idle:
    b probe_wait
probe_ranges:
    .space 3*8
    .word 0,0
probe_expected:
    .word 0
