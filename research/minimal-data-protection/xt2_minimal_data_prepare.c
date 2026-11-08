/* Original fixed-image safety step. Only valid at the pinned early root gate.
 * No allocation of profile storage, live activation, reload or NV transaction.
 */
#include "xt2_native_page_policy.h"
typedef unsigned int u32;
extern int eterna_early_resident_gate(void);
extern char xt2_minimal_expected_data_fnv;

static u32 word(u32 address) {return *(volatile u32 *)(unsigned long)address;}

/* Deliberately fixed 4.41 policies, not a general MMU walker. Reject different
 * attributes rather than enlarging the accepted firmware/platform contract.
 */
static int policy(int protected) {
    struct xt2_mmu_snapshot s;
    u32 first,coarse,page;
    xt2_capture_mmu(&s);
    if(s.table!=0x108000 || s.ttbcr || (s.ttbr0&0xffffc000u)!=s.table ||
       (s.dacr&3)!=1 || !(s.sctlr&1) || !(s.sctlr&(1u<<23)) ||
       (s.sctlr&((1u<<29)|(1u<<28)|(1u<<20)|(1u<<19))))return 1;
    first=word(s.table+(0xdf7000u>>20)*4);
    coarse=first&~1023u;
    if(first!=(coarse|1) || coarse<0x80000 || coarse>=0x100000 ||
       word(coarse+((0xdf7000u>>12)&255)*4)!=0xdf7736)return 1;
    first=word(s.table+(0x781000u>>20)*4);
    if(!protected)return first!=0x714c06; /* original section: RWX */
    coarse=first&~1023u;
    if(first!=(coarse|1) || coarse<0x80000 || coarse>=0x100000)return 1;
    for(page=0x781000;page<0x784000;page+=4096)
        if(word(coarse+((page>>12)&255)*4)!=(page|0x737))return 1;
    return 0; /* three original-format small pages: RO/XN */
}

int xt2_minimal_data_prepare(void) {
    u32 mask=0, value=0x811c9dc5u, i;
    int status, restored;
    const volatile unsigned char *data=(const volatile unsigned char *)0x781000;
    if(eterna_early_resident_gate())return 1; /* unknown task context: wait only */
    if(policy(0))return 2;
    for(i=0;i<0x3000;++i)value=(value^data[i])*0x01000193u;
    if(value!=(u32)(unsigned long)&xt2_minimal_expected_data_fnv)return 2;
    status=((int(*)(u32,u32 *))0x56618)(0,&mask);
    if(status || !mask || (mask&~3u))return 2;
    status=((int(*)(u32,u32,u32))0xcf2100)(0x781000,0x3000,1);
    restored=((int(*)(u32,u32))0x566d8)(0,mask);
    /* A failed API must not short-circuit the context recheck: another task
     * may now be active. Unknown context never authorizes supply release.
     */
    if(eterna_early_resident_gate())return 1;
    if(status || restored)return 2;
    if(policy(1))return 2;
    return 0;
}
