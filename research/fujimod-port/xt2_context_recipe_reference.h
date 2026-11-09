/* Original AI-assisted X-T2-specific identity logic from the experimental
 * context-films candidate. This reference excerpt is NOT separately linked:
 * the private candidate inlines the exact bodies below. Do not add both.
 *
 * Requires locally provided upstream film_xt20.h, six immutable recipes, the
 * existing selector/diagnostics and unchanged XPP hook ABI (args[-1] is LR;
 * return 0 = stock continuation, 1 = handled). No upstream implementation,
 * vendor coefficients or instruction preimages are distributed here.
 *
 * Scope: X-T2 4.41's inspected 0x148-byte processing class and two qualified
 * mapper callers. Complete native writer/copy/lifetime and hardware coverage
 * remain OPEN; this is not a global free-space or camera acceptance claim.
 */
#ifndef XT2_CONTEXT_RECIPE_REFERENCE_H
#define XT2_CONTEXT_RECIPE_REFERENCE_H
#include "film_xt20.h"
#if XT20_FILM_COUNT != 6 || XT20_FILM_CARDS != 0
#error "This adapter is qualified only for the six immutable built-ins"
#endif
#ifndef FILM_SLOT
#define FILM_SLOT 9
#endif
#ifndef PROFILE_SLOT
#define PROFILE_SLOT 0x52
#endif
#ifndef PROFILE_SPECIAL
#define PROFILE_SPECIAL 0x144
#endif
#if FILM_SLOT != 9 || PROFILE_SLOT != 0x52 || PROFILE_SPECIAL != 0x144
#error "Unexpected X-T2 processing layout"
#endif
extern volatile unsigned int film_sims_slot_calls, film_sims_active;

/* X-T2 native processing object: base initializer clears exactly 0x148.
 * Known named fields end with special byte +144. These three tail bytes are
 * scoped to this processing class, not custom settings/flash records.
 * Two original mapper callers pass profile+52; foreign callers stay stock.
 */
#define PROFILE_RECIPE 0x145
#define PROFILE_MAGIC1 0x146
#define PROFILE_MAGIC2 0x147
#define RECIPE_MAGIC1 0x58
#define RECIPE_MAGIC2 0x54
#define SLOT_RETURN1 0x157ac70u
#define SLOT_RETURN2 0x157b3ccu

static const struct xt20_film_recipe *active_recipe(const unsigned char *profile)
{
    unsigned int index;
    if (profile[PROFILE_SLOT] != FILM_SLOT || profile[PROFILE_SPECIAL] == 1 ||
        profile[PROFILE_MAGIC1] != RECIPE_MAGIC1 || profile[PROFILE_MAGIC2] != RECIPE_MAGIC2)
        return 0;
    index=profile[PROFILE_RECIPE];
    return index >= 1 && index <= XT20_FILM_COUNT ? &xt20_film_recipes[index-1] : 0;
}

int film_slot_hook(unsigned int *args)
{
    const struct xt20_film_recipe *recipe;
    unsigned char *profile;
    unsigned int i;
    film_sims_slot_calls++;
    if (args[-1] != SLOT_RETURN1 && args[-1] != SLOT_RETURN2) return 0;
    profile=(unsigned char *)(args[0]-PROFILE_SLOT);
    recipe=film_xt20_select(args[1]);
    profile[PROFILE_RECIPE]=profile[PROFILE_MAGIC1]=profile[PROFILE_MAGIC2]=0;
    film_sims_active=0; /* diagnostic only, never used by a consumer */
    for (i=0; i<XT20_FILM_COUNT; ++i) {
        if (recipe != &xt20_film_recipes[i]) continue;
        profile[PROFILE_RECIPE]=i+1;
        profile[PROFILE_MAGIC1]=RECIPE_MAGIC1;
        profile[PROFILE_MAGIC2]=RECIPE_MAGIC2;
        profile[PROFILE_SLOT]=FILM_SLOT;
        film_sims_active=i+1;
        return 1;
    }
    return 0;
}
#endif
