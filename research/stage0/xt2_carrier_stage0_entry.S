.syntax unified
.arm
.section .text.entry,"ax",%progbits
.global xt2_carrier_stage0_entry
.type xt2_carrier_stage0_entry,%function
xt2_carrier_stage0_entry:
    push {r0-r12,lr}
    mrs r0,cpsr
    sub sp,sp,#8
    str r0,[sp]
    bl xt2_carrier_stage0_main
    ldr r0,[sp]
    msr cpsr_f,r0
    add sp,sp,#8
    pop {r0-r12,lr}
    /* Preserve original call's LR and arguments; original routine returns to
       cf8218. This entry must be called in place of the original BLcf83cc. */
    b xt2_carrier_original_call
.size xt2_carrier_stage0_entry,.-xt2_carrier_stage0_entry
