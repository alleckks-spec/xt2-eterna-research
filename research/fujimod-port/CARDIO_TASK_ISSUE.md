# PR471 recorded callback issue: native refusal no longer strands a bank

This is a bounded backport of the existing per-bank task-issue mechanism in
x70view PR471, commit2e2aa8af51526f81ec22036502b02881507dcd00, cardio Git
blob231d78c80ca3e503ce4f28032bcc62a7602932e8. Credit: Taylor Chapman
(heytchap) and Claude (Anthropic). It preserves the qualified X-T2 listing,
status and invalid-open-handle adaptations. It does not import donor timing,
GPIO/capture gates, DMA policy or automatic lost-request retry/watchdog rules.

Exact new ELF: `095daaa2fb441f4ab2f4027dbe27f063e1a05549030393663a98eabbf10ad398`.
Base is the qualified eight-mod WB+USB+dual-date artifact18d06d6a. Only cardio
source selection changes, in a new private input directory; the other41sources
and all14libraries/target memory operands stay pinned. There are42sources and
81SDwords; payload249288bytes leaves12856bytes in the existing262144-byte
reservation at0x1380000. A fresh build reproduces ELF, region and both SD files
byte for byte, and delivery verifies ELF → region → actual SD bytes.

## Actual X-T2 contract and original counterexample

The original final SDK chain is reused with its native mount, two A7 cores,
timer8/IRQ56, native tasks and genuine positive filesystem calls. Observational
instruction stops record actual callbacks, request messages, return values and
native task IDs; they do not select device completion or replace API results.

On18d06d6a, a normal open callback runs on native task39. Its body immediately
issues read on task39 while the cardio bank is RUNNING. The native read builder
can call its callback synchronously before that issue returns. The explicit
negative input sets native media-status bit4 at context+0x16b6c only for this
transfer; its real callback returns status5. A transient control restores that
input at the real error callback, so subsequent close would be admissible.
No successful kernel/API answer, callback, ready bit or registration is supplied.

The original callback tries to claim the already-RUNNING bank, is counted as
stale and disappears. After eight genuine timer waits: jobBUSY, bankLIVE,
active=job, outstanding callbacks0, stale1, native open-count1. An unchanged
positive control completes normally. This is a recorded native failure, not a
hypothetical need for a general queue.

## Existing mechanism and fixed result

The bank callback now records its arguments and body. Its lifetime hold remains
raised until the body executes from an existing cardio readiness/busy poll.
The existing PR's bounded bank slots, step lock and overlap diagnostics are
reused; no universal dispatcher or scheduler is added. The bank is unclaimed
before a later poll executes the next recorded response, including synchronous
native refusals. The original four-bank ownership and stale retirement remain.

On095daaa2, native task39 records the open callback; the next read/close requests
issue from polling task34. The identical transient native refusal becomes one
jobFAILED/status5. Native close succeeds; all banks, active pointer, outstanding
callbacks and native open-count return to zero, with stale0. Three further
native timer waits do not redeliver anything. One explicit caller retry advances
generation4→5, reads166bytes successfully and again retires all resources. This
is a caller retry after a known error, not automatic recovery of a lost queue
request. Eight additional bounded callback-error cases cover live and abandoned
requests across every bank, showing record-before-poll and exactly-once delivery
or stale retirement without any successful storage input.

## Changed-artifact regression and limits

The new exact ELF retains genuine SDK merged SETTINGS commit/write/readback and
fresh-board restore: ETERNA plus DATE FOLDERS on / FORMAT CARD NAME off. Owners
complete without failures; restore has no explicit selection setter or host
settings decoder. All21existing native storage/timer/settings/menu reports,
24invalid-open controls, WB84chains/import42/reset cases, USB, SAVE49, date A/B/
transitions/dual-menu, formatter/codec, numeric films/NR/JPEG and delivered
BSS/allocator/map-argument checks were rerun on this artifact.

Older manual-boot file fixtures stop at retained worker/function boundaries;
they now explicitly poll cardio after restoring the caller frame and alongside
their explicit timer ticks. Their old inline-completion assumption is not kept.
This adaptation is separately hashed. The genuine SDK positive/fault/retry cases
use original native timer/task polling, with no added host cardio poll. A bare
consumer of recorded callbacks must poll cardio; isolated loader-only boot is
not promoted to a scheduled full-platform result.

Native queue-pool exhaustion/post failure, completion-token identity, automatic
lost-request quiet-time/retry, permanently refused close recovery and overlap
saturation remain separate software boundaries. No X100F timeout constant or
capture GPIO is treated as an X-T2 fact. Physical SD/NAND retention, camera boot,
real MMU/cache/DMA timing and physical buttons/USB exchange remain unverified.
The next specific storage step is to qualify native queue admission failure and
its discarded issue status before choosing any lost-request retry policy.

Local evidence is pinned by cardio-task-issue-check-unverified/{integration,
delivery,freeze}.json; original and fixed fault reports retain exact source
history. Original SDK/checker sources and all prior frozen artifacts remain
unchanged. Generated derivatives, firmware and raw reports stay private. Only
the original transformer, builder, probe/adapters/checker and this note are
publication candidates; this child did not publish.
