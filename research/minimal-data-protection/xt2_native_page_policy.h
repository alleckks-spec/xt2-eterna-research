#ifndef XT2_NATIVE_PAGE_POLICY_H
#define XT2_NATIVE_PAGE_POLICY_H
#include <stdint.h>
struct xt2_mmu_snapshot { uint32_t sctlr,ttbcr,ttbr0,ttbr1,dacr,table; };
void xt2_capture_mmu(struct xt2_mmu_snapshot *out);
/* Restricted identity-mapped domain0 native-compatible descriptors only.
 * Returns nonzero on unsupported configuration; never changes page tables.
 * table and all referenced L2 tables must be readable resident kernel memory.
 */
int xt2_native_page_policy(uint32_t address,const struct xt2_mmu_snapshot *mmu,uint32_t *flags);
#endif
