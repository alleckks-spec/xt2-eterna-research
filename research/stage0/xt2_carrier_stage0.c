/* Proposed early carrier entry support. Isolated research only: loading,
 * residency, initial stage0 RX/cache visibility and real media remain unproven.
 * Fixed carrier layout is trusted build data, never user profile content. */
#include <stdint.h>
#include "xt2_early_bootstrap.h"
#define CODE 0x781000u
#define DATA 0x784000u
#define CONFIG (DATA+0x5000u)
#define WORK (DATA+0x5100u)
#define MASK (DATA+0x5200u)
#define RESULT (DATA+0x5204u)
static void barrier(void) { __asm__ volatile("dsb sy\nisb sy" ::: "memory"); }
static int protect(uint32_t a,uint32_t n,uint32_t f) {
    return ((int (*)(uint32_t,uint32_t,uint32_t))0xcf2100)(a,n,f);
}
static int affinity(uint32_t mask) {
    return ((int (*)(uint32_t,uint32_t))0x566d8)(0,mask);
}
/* Returns only success. Any uncertain publication/transaction state stops at
 * this early boundary, with all allocations and diagnostic cells retained. */
int xt2_carrier_stage0_main(void) {
    volatile uint32_t *mask=(volatile uint32_t *)MASK;
    volatile uint32_t *result=(volatile uint32_t *)RESULT;
    const struct xt2_bootstrap_config *config=(const void *)CONFIG;
    uint32_t cpsr;
    __asm__ volatile("mrs %0,cpsr":"=r"(cpsr));
    if ((cpsr&31)!=19 || config->magic!=XT2_BOOTSTRAP_MAGIC ||
        config->manifest!=DATA || config->manifest_size!=17276 ||
        config->code_start!=CODE || config->code_size!=0x2000 ||
        config->data_start!=DATA || config->data_size!=0x6000 ||
        config->workspace!=WORK) goto failed;
    if(protect(CODE,0x2000,5) || protect(DATA,0x5000,1) || protect(DATA+0x5000,0x1000,3)) goto failed;
    if(((int (*)(uint32_t,volatile uint32_t *))0x56618)(0,mask) || !*mask || (*mask&~3u)) goto failed;
    for(uint32_t core=1;core<=2;core<<=1) {
        if(affinity(core)) goto failed;
        barrier();
        ((void (*)(uint32_t,uint32_t))0x58f8c)(CODE,0x2000);
        ((void (*)(uint32_t,uint32_t))0x58f8c)(DATA,0x6000);
        barrier();((void (*)(void))0x58f9c)();barrier();
    }
    if(affinity(*mask)) goto failed;
    *result=(uint32_t)((int (*)(const struct xt2_bootstrap_config *))CODE)(config);
    if(*result) goto failed;
    return 0;
failed:
    /* Do not guess rollback ownership or resume with a partially held state. */
    for(;;) __asm__ volatile("wfe" ::: "memory");
}
