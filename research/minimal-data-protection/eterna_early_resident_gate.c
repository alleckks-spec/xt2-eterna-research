/* X-T2 4.41 early-resident fixture guard. No task is stopped here.
 * Valid only at the pinned cf8214 boundary before application task creation.
 * Firmware identity and absence of asynchronous task creators are external
 * prerequisites; this is not a generic runtime or camera installation API.
 */
typedef unsigned int u32;
int eterna_early_resident_gate(void) {
    volatile u32 *registry=(volatile u32 *)0x7a548;
    volatile u32 *current=(volatile u32 *)0x5bf90;
    u32 i,core,root=registry[136];
    if(!root || !registry[134] || !registry[135]) return -1;
    for(i=0;i<250;i++) if((i<134 || i>136) && registry[i]) return -2;
    for(i=134;i<=136;i++) {
        volatile u32 *task=(volatile u32 *)registry[i];
        if(task[0]!=0x54485244 || task[0xcc/4]!=i+1 ||
           task[0xe4/4]!=(i==136?0xcf8060:0xcf7c50)) return -3;
    }
    __asm__ volatile("mrc p15,0,%0,c0,c0,5":"=r"(core));
    core&=3;
    if(core>1 || current[core]!=root ||
       (current[1-core]!=registry[134] && current[1-core]!=registry[135])) return -4;
    return 0;
}
