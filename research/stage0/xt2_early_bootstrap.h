#ifndef XT2_EARLY_BOOTSTRAP_H
#define XT2_EARLY_BOOTSTRAP_H
#include <stdint.h>
#include "xt2_native_page_policy.h"
#define XT2_BOOTSTRAP_MAGIC 0x58423231u
/* Caller owns and retains BOTH preloaded regions: executable linked code and
 * writable resident data (manifest/config/workspace). They are lab prerequisites,
 * not inferred scratch addresses. Never load these from a user profile.
 * Native RTOS/root early boundary and pinned firmware identity are prerequisites.
 */
struct xt2_bootstrap_config {
    uint32_t magic,manifest,manifest_size,code_start,code_size,data_start,data_size,workspace;
};
struct xt2_bootstrap_workspace {
    uint32_t magic,attempted,result,native_errno,allocation,allocation_size,payload_base,metadata_base,install_result,control_plan_ready;
    struct xt2_mmu_snapshot mmu;
};
/* One-shot canonical template only. Retains allocation on success AND failure.
 * A nonzero control held/written state means caller must not resume startup;
 * recover at the same early boundary or stop. This is not generic exclusion.
 * Code/data and the native allocator's error cell remain resident indefinitely.
 */
int xt2_early_bootstrap(const struct xt2_bootstrap_config *config);
int xt2_early_bootstrap_rollback(const struct xt2_bootstrap_config *config);
#endif
