/* Original X-T2 4.41 UI post ABI reference, AI-assisted.
 * Layout only: no queue readiness, task ownership or hardware qualification.
 */
#ifndef XT2_UI_POST_MESSAGE_REFERENCE_H
#define XT2_UI_POST_MESSAGE_REFERENCE_H
#include <stdint.h>
#include <stddef.h>
enum { XT2_UI_POST_PAYLOAD_BYTES = 68, XT2_UI_POST_PACKET_BYTES = 76 };
struct xt2_ui_post_packet {
    uint32_t event;
    uint32_t argument;
    unsigned char data[XT2_UI_POST_PAYLOAD_BYTES];
};
_Static_assert(offsetof(struct xt2_ui_post_packet, data) == 8, "UI payload offset");
_Static_assert(sizeof(struct xt2_ui_post_packet) == XT2_UI_POST_PACKET_BYTES, "UI packet extent");
#endif
