# First data-only profile publication

Original C implementation and verification work developed with OpenAI Codex assistance. This is an intermediate integration prototype, not camera firmware. The complete goal still includes a real file-loading owner, safe native activation, additional simulations, profile replacement and physical validation.

## Implementation

The new bank copies only the validated tone record, gain records and 149 sorted parameter entries from a prepared profile. It checks the exact pipeline request and generation, validates the source container again, and compares its data with the prepared candidate. It does not copy executable instructions into the bank. Source ownership and immutability remain caller preconditions; an eligibility query is not callback exclusion.

Atomic states distinguish EMPTY, PREPARING, SEALED, PUBLISHING, READY and FAILED. Publication rechecks eligibility and release-publishes one bank pointer. The bank remains unchanged for the rest of the boot; replacement is rejected. This first-publication restriction is an explicit interim limit, not completion of reload support. Actual cache coherence and persistent memory ownership are not established by C acquire/release operations alone.

Each caller-owned operation captures a pointer once, including a null pointer. Custom admission and all data lookups use that captured value. An operation begun before publication stays on stock data until it ends; a later operation can use the new profile. Parameters use binary search over the validated sorted keyset. Stock, unknown-key, unscoped and ended-operation reads fall back to the original reader.

## What the composed check exercises

The native file-queue fixture reads a laboratory container, validates it and prepares a candidate. Compiled C then extracts and publishes the bank. Dispatch callbacks are installed in the isolated emulator before the reader begins; they marshal an explicit operation pointer to the compiled adapters. They are **not installed native firmware wrappers or a solved task/interrupt transport**.

The check executes the original aggregate builder and the original incremental gain, matrix and tone wrappers. In the incremental path, it invokes compiled publication between the low-byte and high-byte reads of a native coefficient, after gain and before tone. The operation's earlier null snapshot must continue to produce the original stock result. Subsequent custom outputs are compared with a separate direct-data reference; stock outputs are compared with an untouched stock machine. The numerical references share native arithmetic, so these are differential checks rather than independent mathematical oracles.

The previous supplied boundary copied a prepared executable payload and wrote 29 hook words after file preparation. This prototype instead publishes copied data through compiled C. The planned 29 native hook words are checked unchanged and monitored for CPU writes. This narrower result does not demonstrate the early installation of the new dispatchers on a camera.

The final sequential run passed both fresh-machine cases: successful publication and eligibility revoked after sealing. The latter leaves the bank FAILED with a null published pointer, denies custom selection and preserves stock reads. The successful case also rejects malformed candidate data, wrong generation, replacement and invalid scopes. Three aggregate comparisons (custom 18, stock 3 and stock 0) and one custom incremental comparison match their references; custom tone and gain differ from stock under the selected enabled context.

The binary-search version preserves the prior native outputs and bank contents while reducing measured bank CPU reads from 196,436 to 12,068. This is an access-count improvement for this fixture, not a camera performance measurement. The combined harness links 18,388 text bytes and 6,572 BSS bytes with no undefined symbols. Source/input hashes and runtime dependency identities were captured before and after the run and matched; exact snapshots and failures remain local.

Local final report SHA-256: `447cba26fb454d00a75aa5c83cddb0878bb4e095a3ca6a82f3f463c79bf4b3a1`. Earlier failures exposed a missing include, the original tone getter's valid null-output ABI, and an inherited instruction-budget limit; these were preserved and corrected before the successful result.

## Remaining integration obligations

- Native operation propagation must handle nested calls, task identity and exceptions. Static analysis shows that current-task ID, IRQ depth and SVC mode alone cannot distinguish every exception callback from its interrupted task.
- Both the aggregate and incremental paths need coverage; the full outer incremental function is not executed by this fixture. Synchronous operation consistency does not prove whole-frame or asynchronous hardware lifetime consistency.
- Development-ID and public-selection admission still need integration. The test's processing selector is not the entire UI/development path.
- The bank needs 2,944 persistent data bytes plus control and operation storage. Its separate harness placement does not fit the frozen resident variant's 84-byte BSS slack. No frozen image or carrier layout is changed.
- Actual owner/worker completion, mounted-card access, cache visibility, full boot, profile replacement, preview/JPEG/movie output and hardware behavior remain unverified. Representation validation does not establish numerical safety of arbitrary coefficients.

## Source and reproduction boundary

Adjacent C/header/Python files are reviewed original source for inspection. They are not a standalone runnable distribution. Put them under `scripts/` in the full local research workspace. The verifier also needs the published reader-pipeline verifier and loaded-profile helper, local original pipeline/container/materializer/reader/routing sources and headers, native filesystem and numeric-reference helpers, generated schema and relocation template, locally supplied X-T2 4.41/X-H1 2.15 extracted inputs and stock image, prior parameter reports, and Clang/LLD, Python, pyelftools, Capstone and Unicorn with the tested TCI backend.

The local test additionally uses assembly continuations that reproduce displaced stock prologues. Those copied instructions are deliberately not published. No firmware, coefficient tables, generated manifests, raw output buffers or full private reports are uploaded.

The optimization comparison additionally requires the named local frozen pre-optimization report; runtime checks expect the locally installed compiler, linker and emulator libraries. The older reader verifier gains only an optional pre-reader observer; previous source versions remain in their exact evidence snapshots.

Local command in that complete workspace:

```sh
LIBUNICORN_PATH="$PWD/.toolchains/unicorn-tci" UC_IGNORE_REG_BREAK=1 .venv/bin/python scripts/verify_xt2_first_data_activation.py
```
