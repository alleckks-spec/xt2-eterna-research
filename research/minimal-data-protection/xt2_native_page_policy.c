#include "xt2_native_page_policy.h"
#define WORD(a) (*(volatile uint32_t *)(uintptr_t)(a))
void xt2_capture_mmu(struct xt2_mmu_snapshot *s) {
    __asm__ volatile("mrc p15,0,%0,c1,c0,0":"=r"(s->sctlr));
    __asm__ volatile("mrc p15,0,%0,c2,c0,2":"=r"(s->ttbcr));
    __asm__ volatile("mrc p15,0,%0,c2,c0,0":"=r"(s->ttbr0));
    __asm__ volatile("mrc p15,0,%0,c2,c0,1":"=r"(s->ttbr1));
    __asm__ volatile("mrc p15,0,%0,c3,c0,0":"=r"(s->dacr));
    s->table=WORD(0x5bacc);
}
int xt2_native_page_policy(uint32_t address,const struct xt2_mmu_snapshot *s,uint32_t *flags) {
    uint32_t first,raw,physical,ap,xn,kind,domain,attribute[2],native_ap,type;
    unsigned i,cls;
    if(!s || !flags || (address&4095) || s->ttbcr ||
       !(s->sctlr&1) || !(s->sctlr&(1u<<23)) ||
       (s->sctlr&((1u<<29)|(1u<<28)|(1u<<20)|(1u<<19))) ||
       !s->table || (s->table&0x3fff) || (s->ttbr0&0xffffc000u)!=s->table ||
       (s->dacr&3)!=1)return 1;
    first=WORD(s->table+(address>>20)*4);
    domain=(first>>5)&15;
    if(domain)return 2;
    if((first&3)==2) {
        if(first&(1u<<18))return 3; /* supersection is deliberately unsupported */
        raw=first;physical=raw&0xfff00000u;
        if((physical|(address&0xfffffu))!=address)return 4;
        ap=((raw>>10)&3)|((raw>>13)&4);xn=(raw>>4)&1;kind=0;
        attribute[0]=0x11000;attribute[1]=0x14004;
        native_ap=ap==3?0xc02:0x8c02;
    } else if((first&3)==1) {
        uint32_t table=first&~1023u,index=(address>>12)&255;
        if(first!=(table|1u))return 5;
        raw=WORD(table+index*4);
        if((raw&3)==1) {
            physical=raw&0xffff0000u;
            if((physical|(address&0xffffu))!=address)return 4;
            ap=((raw>>4)&3)|((raw>>7)&4);xn=(raw>>15)&1;kind=1;
            attribute[0]=0x1400;attribute[1]=0x4404;
            native_ap=ap==3?0x31:0x231;
            for(i=index&~15u;i<(index&~15u)+16;++i)if(WORD(table+i*4)!=raw)return 6;
        } else if((raw&2)==2) {
            physical=raw&0xfffff000u;
            if(physical!=address)return 4;
            ap=((raw>>4)&3)|((raw>>7)&4);xn=raw&1;kind=2;
            attribute[0]=0x440;attribute[1]=0x504;
            native_ap=ap==3?0x32:0x232;
        } else return 7;
    } else return 8;
    if(ap!=3 && ap!=7)return 9;
    for(cls=0;cls<2;++cls) {
        type=physical|native_ap|attribute[cls]|(xn?(kind==0?16u:kind==1?0x8000u:1u):0u);
        if(raw==type) {
            *flags=1u|(ap==3?2u:0u)|(xn?0u:4u)|(cls==0?8u:0u);
            return 0;
        }
    }
    return 10; /* all unrecognized attributes, NS/nG/etc fail closed */
}
