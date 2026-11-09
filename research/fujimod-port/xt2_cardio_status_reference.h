/* Original AI-assisted X-T2 listing status adaptation. Native filesystem
 * end/no-match statuses map to6; media/path/cursor errors stay failures.
 * Does not qualify native FAT mounting or concurrent cancellation.
 */
#ifndef XT2_CARDIO_STATUS_REFERENCE_H
#define XT2_CARDIO_STATUS_REFERENCE_H
#define XT2_DIRECTORY_END 6
static inline int xt2_listing_result(int status)
{
    return status == XT2_DIRECTORY_END ? 0 : status;
}
#endif
