/* Original first-only data bank. Never accepts code or live hook addresses. */
#include "xt2_profile_first_bank.h"
#include "xt2_native_profile_reader.h"
#include "xt2_profile_container.h"
struct xt2_profile_bank { uint8_t tone[72],gain[1680],parameters[149*8]; };
static struct xt2_profile_bank bank;
static const struct xt2_profile_bank *ready;
static unsigned state;
static struct xt2_materialize_request prepared_request;
static uint32_t prepared_generation;
static uint32_t le32(const uint8_t *p) {return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int same(const uint8_t *a,const uint8_t *b,size_t n) {size_t i;for(i=0;i<n;++i)if(a[i]!=b[i])return 0;return 1;}
static void copy(uint8_t *a,const uint8_t *b,size_t n) {size_t i;for(i=0;i<n;++i)a[i]=b[i];}
int xt2_first_extract(const struct xt2_materialize_request *r,uint32_t generation) {
 const uint8_t *data; const uint8_t *p;size_t n=0;struct xt2_profile_view v;
 if(__atomic_load_n(&state,__ATOMIC_ACQUIRE) || __atomic_load_n(&ready,__ATOMIC_ACQUIRE))return 1;
 if(!xt2_profile_candidate_eligible(r,generation))return 2;
 data=xt2_reader_data(&n);
 if(xt2_profile_validate(data,n,&v))return 3;
 p=(const uint8_t *)r->payload;
 if(!same(p+0x1e58,v.tone,72)||!same(p+0x2e70,v.gain,1680)||!same(p+0x3600,v.parameters,149*8))return 4;
 /* Recheck immediately before copying. This does NOT exclude callbacks. */
 if(!xt2_profile_candidate_eligible(r,generation))return 2;
 {unsigned expected=0;if(!__atomic_compare_exchange_n(&state,&expected,1,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))return 1;}
 copy(bank.tone,v.tone,72);copy(bank.gain,v.gain,1680);copy(bank.parameters,v.parameters,149*8);
 prepared_request=*r;prepared_generation=generation;
 __atomic_store_n(&state,2,__ATOMIC_RELEASE);
 return 0;
}
int xt2_first_publish(void) {
 unsigned expected=2;
 if(!__atomic_compare_exchange_n(&state,&expected,3,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))return 1;
 if(!xt2_profile_candidate_eligible(&prepared_request,prepared_generation)){__atomic_store_n(&state,5,__ATOMIC_RELEASE);return 2;}
 __atomic_store_n(&ready,&bank,__ATOMIC_RELEASE);__atomic_store_n(&state,4,__ATOMIC_RELEASE);return 0;
}
unsigned xt2_first_state(void){return __atomic_load_n(&state,__ATOMIC_ACQUIRE);}
void xt2_first_end(struct xt2_profile_operation *op){if(op){op->snapshot=0;op->admitted=0;}}
void xt2_first_begin(struct xt2_profile_operation *op) {
 if(!op)return;
 op->snapshot=__atomic_load_n(&ready,__ATOMIC_ACQUIRE);op->admitted=0;
}
int xt2_first_admit(struct xt2_profile_operation *op,uint32_t id) {
 if(!op || id!=18 || op->snapshot!=&bank || __atomic_load_n(&ready,__ATOMIC_ACQUIRE)!=&bank){if(op)op->admitted=0;return 0;}
 op->admitted=1;return 1;
}
static const struct xt2_profile_bank *active(const struct xt2_profile_operation *op) {
 return op && op->admitted && op->snapshot==&bank && __atomic_load_n(&ready,__ATOMIC_ACQUIRE)==&bank ? op->snapshot : 0;
}
int xt2_first_parameter(const struct xt2_profile_operation *op,uint32_t key,uint8_t *out) {
 const struct xt2_profile_bank *b=active(op);unsigned lo=0,hi=149;
 if(!b || !out)return 0;
 /* Validator guarantees149 strictly ordered exact keys: at most8 probes. */
 while(lo<hi){unsigned mid=lo+(hi-lo)/2;uint32_t k=le32(b->parameters+mid*8);
  if(k==key){*out=b->parameters[mid*8+4];return 1;}
  if(k<key)lo=mid+1;else hi=mid;
 }
 return 0;
}
const uint8_t *xt2_first_tone(const struct xt2_profile_operation *op,uint32_t id) {
 const struct xt2_profile_bank *b=active(op);return b && id==51 ? b->tone : 0;
}
const uint8_t *xt2_first_gain(const struct xt2_profile_operation *op,uint32_t id) {
 const struct xt2_profile_bank *b=active(op);return b && id>=77 && id<=111 ? b->gain+(id-77)*48 : 0;
}
