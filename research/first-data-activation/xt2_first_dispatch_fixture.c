/* Test-only explicit operation transport; NOT native task/IRQ scope storage. */
#include "xt2_profile_first_bank.h"
static struct xt2_profile_operation *operation;
extern uint32_t xf_stock_parameter(uint32_t);
extern int xf_stock_tone(uint32_t,uint8_t *,uint8_t *);
extern void xf_stock_gain(uint32_t,uint8_t *);
extern void xf_stock_selector(uint8_t *,uint32_t);
void xf_transport(struct xt2_profile_operation *op){operation=op;}
uint32_t xf_parameter(uint32_t key){uint8_t value;if(xt2_first_parameter(operation,key,&value))return value;return xf_stock_parameter(key);}
int xf_tone(uint32_t id,uint8_t *metadata,uint8_t *out){
 const uint8_t *r=xt2_first_tone(operation,id);unsigned i;
 if(!r)return xf_stock_tone(id,metadata,out);
 if(metadata)for(i=0;i<9;++i)metadata[i]=r[4+i];if(out)for(i=0;i<56;++i)out[i]=r[14+i];return 1;
}
void xf_gain(uint32_t id,uint8_t *out){const uint8_t *r=xt2_first_gain(operation,id);unsigned i;
 if(!r){xf_stock_gain(id,out);return;}if(!out)return;for(i=0;i<44;++i)out[i]=r[4+i];}
void xf_selector(uint8_t *out,uint32_t id){if(xt2_first_admit(operation,id)){*out=9;return;}xf_stock_selector(out,id);}

uint32_t xf_publish_parameter(uint32_t key){(void)xt2_first_publish();return xf_parameter(key);}
