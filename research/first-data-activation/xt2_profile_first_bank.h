#ifndef XT2_PROFILE_FIRST_BANK_H
#define XT2_PROFILE_FIRST_BANK_H
#include "xt2_profile_pipeline.h"
struct xt2_profile_bank;
struct xt2_profile_operation { const struct xt2_profile_bank *snapshot; uint32_t admitted; };
/* Serialized trusted caller only. Sources immutable/disjoint throughout call;
 * fresh eligibility is identity/state evidence, not callback exclusion. READY
 * and all bytes are retained to reboot. No replacement or numerical-safety claim.
 * Release/acquire orders CPU memory; actual cache/coherency is caller's duty. */
int xt2_first_extract(const struct xt2_materialize_request *, uint32_t generation);
int xt2_first_publish(void);
unsigned xt2_first_state(void); /*0 EMPTY,1 PREPARING,2 SEALED,3 PUBLISHING,4 READY,5 FAILED*/
void xt2_first_end(struct xt2_profile_operation *);
void xt2_first_begin(struct xt2_profile_operation *);
int xt2_first_admit(struct xt2_profile_operation *, uint32_t public_id);
int xt2_first_parameter(const struct xt2_profile_operation *, uint32_t key, uint8_t *value);
const uint8_t *xt2_first_tone(const struct xt2_profile_operation *, uint32_t id);
const uint8_t *xt2_first_gain(const struct xt2_profile_operation *, uint32_t id);
#endif
