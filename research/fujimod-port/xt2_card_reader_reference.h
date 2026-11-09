/* AI-assisted original reader/publisher exclusion for the existing card table.
 * Paired coherent API entry/return is required. No task IDs, native lock IDs,
 * allocation, registry or service. A reader arriving during publication joins
 * a stock-only cohort; its gate remains closed until that cohort drains.
 * Bounded interleaving checks do not establish all native/indirect coverage,
 * scheduler fairness, teardown or physical cache/lifetime correctness. */
#ifndef XT2_CARD_READER_REFERENCE_H
#define XT2_CARD_READER_REFERENCE_H
extern volatile unsigned int xt2_card_access_state;
#define XT2_CARD_WRITER (1u << 31)
#define XT2_CARD_STOCK_COHORT (1u << 30)
#define XT2_CARD_READERS ((1u << 30) - 1)

static inline void xt2_card_read_begin(void)
{
    unsigned int old, next;
    do {
        old=xt2_card_access_state;
        next=old+1;
        if(old & (XT2_CARD_WRITER|XT2_CARD_STOCK_COHORT)) next|=XT2_CARD_STOCK_COHORT;
    } while(!__sync_bool_compare_and_swap(&xt2_card_access_state,old,next));
}

static inline void xt2_card_read_end(void)
{
    unsigned int old, next;
    do {
        old=xt2_card_access_state;
        next=old-1;
        if(!(next & (XT2_CARD_WRITER|XT2_CARD_READERS))) next=0;
    } while(!__sync_bool_compare_and_swap(&xt2_card_access_state,old,next));
}

static inline int xt2_card_recipe_readable(void)
{
    unsigned int state=xt2_card_access_state;
    return (state & XT2_CARD_READERS) && !(state & (XT2_CARD_WRITER|XT2_CARD_STOCK_COHORT));
}

static inline int xt2_card_write_begin(void)
{
    return __sync_bool_compare_and_swap(&xt2_card_access_state,0,XT2_CARD_WRITER);
}

static inline void xt2_card_write_end(void)
{
    unsigned int old, next;
    do {
        old=xt2_card_access_state;
        next=old & ~XT2_CARD_WRITER;
        if(!(next & XT2_CARD_READERS)) next=0;
    } while(!__sync_bool_compare_and_swap(&xt2_card_access_state,old,next));
}
#endif
