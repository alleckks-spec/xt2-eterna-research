/* AI-assisted original AAPCS memory glue for Clang-built loader components.
 * Use the already supplied libc, with no firmware API substitution. */
#include <string.h>
void __aeabi_memcpy(void *out, const void *in, size_t n) { memcpy(out, in, n); }
void __aeabi_memcpy4(void *out, const void *in, size_t n) { memcpy(out, in, n); }
void __aeabi_memcpy8(void *out, const void *in, size_t n) { memcpy(out, in, n); }
void __aeabi_memclr8(void *out, size_t n) { memset(out, 0, n); }
