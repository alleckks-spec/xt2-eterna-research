# Bounded upstream reuse check, November 11, 2026

The checked x70view main is `b2fd79df85290b19d20af4eba74df8f37df3b404`.
The local source remains pinned at `9d22f1b41c70c20407158e699f2583ac4907ff16`
with FujiMod `944d5c865d4def32663c1dad24d54ac3001f3f6e`. No automatic update
was performed. Commit search includes author branches; it is not a main-ref
test. Main was resolved separately through its branch endpoint and selected
source files were fetched at that exact commit.

| Change | Exact published source | Existing X-T2 evidence | Applicability / remaining step |
|---|---|---|---|
| Timer callback stack | [PR470](https://github.com/justjake/x70view/pull/470), `e007961f2a9ad32b96f1136433f91b4ab2597270`; X-T20 [PR480](https://github.com/justjake/x70view/pull/480), `b92e74a17a122bb9d37f25b3533709cfb8b46a79` | Minimal exact dispatcher original/fixed control already existed | Same ABI defect independently established for X-T2. New full-timer candidate uses the X-T2 literal and actual production callback chain; see FULL_TIMER_CHECKPOINT. Do not copy donor stack addresses |
| Handles, lost requests, reuse, callback task issue, DMA and stock/shot gates | [PR471](https://github.com/justjake/x70view/pull/471), `2e2aa8af51526f81ec22036502b02881507dcd00` | Four banks/retirement and native worker error chains; native16-token allocator exhaustion; XPP watchdog/admission gaps already documented | Backport only checked pieces while preserving listing/status fixes. Open-handle check now has original trap/fixed error controls; rest requires native builder-token identity, task issue, timeout and cache qualification |
| Capture/REC state distinction | [PR472](https://github.com/justjake/x70view/pull/472), `b2ca467fe08ba72b2c102c0b78da6d2fedbf0f95` | X-T2 settings currently checks supplied REC/capture/menu bytes, not a qualified capture gate | Published technical contract, not executable X-T2 proof. Locate real X-T2 producers, physical S1 and capture/storage signals before enabling the gate; no donor timing/GPIO/ready values copied |
| X100F target switches | [PR474](https://github.com/justjake/x70view/pull/474), `93f394d19937e66c4df6ff121440fa70b08f2198` | Existing independent X-T2 target/bindings/reservation | Draft has no qualified card regions and explicitly excludes feature switches; cannot supply a completed X-T2 target or serializer implementation |
| Settings/custom-slot stock film substitution | No concrete new X100F commit established | Stock-choice adaptation keeps extra choice separate and supplies underlying stock film to ordinary readers; native JSON restore tested on common ELF | General author claim is not source evidence. Actual native serializers and independent C1-C7 semantics remain software work |
| FocalUI backend/menu | [PR372](https://github.com/justjake/x70view/pull/372), `96b90e3c0a4850b9989dfff3cececf137ead6e69` | Native stock-choice menus already tested; no general X-T2 Focal renderer claimed | Draft backend/runtime probe, explicitly not a completed full menu. Keep outside the pinned confirmed feature set until selected and adapted |

All six inspected PRs were open drafts, unmerged at read time. The selected
main timer/cardio files lacked the draft stack-top/open-handle helper changes.
The local source-check record retains exact refs and main file blobs. This is a bounded
check, not a claim that every author branch was audited.

Credit for PR470/471/472/474 contributions: Taylor Chapman (heytchap) and
Claude (Anthropic). Their contribution credit is retained in the local backport.
X-T2 addresses, measurements and qualification are independently established.

Hardware has not been used. Emulator/supplied-boundary results do not establish
capture scheduling, MMU/cache/DMA, physical SD persistence or camera safety.
