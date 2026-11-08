/* Original early-root wrapper. Success tail-calls the displaced original BL
 * destination with the original incoming registers/flags/SP/LR intact.
 */
.syntax unified
.arm
.section .text.entry,"ax",%progbits
.global xt2_minimal_data_entry, xt2_minimal_data_failed
.global xt2_minimal_data_power_request, xt2_minimal_data_wait
xt2_minimal_data_entry:
    push {r0-r12,lr}
    mrs r0, cpsr
    push {r0,r1}
    bl xt2_minimal_data_prepare
    cmp r0, #0
    bne xt2_minimal_data_failed
    pop {r0,r1}
    msr APSR_nzcvq, r0
    pop {r0-r12,lr}
    b xt2_minimal_original_root_call
xt2_minimal_data_failed:
    cpsid aif
    cmp r0, #1
    beq xt2_minimal_data_wait
xt2_minimal_data_power_request:
    mov r0, #4
    movt r0, #0xfff1
    ldr r1, [r0]
    bic r1, r1, #1
    str r1, [r0]
    dsb sy
xt2_minimal_data_wait:
    wfe
    b xt2_minimal_data_wait
