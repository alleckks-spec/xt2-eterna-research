# Actual policy-hook startup of the common X-T2 artifact

AI-assisted original bounded integration,9 November2026. Unchanged ordinary four-mod ELF `208845640d4745ff9384911b2f0f38459f830fa87d29adce7c42674d532e9b69`. This milestone changes verification and documentation, not runtime code or packaging.

## Gap closed

Previous checks invoked four mod-init functions and film_loader_boot manually. A new adapter stops the existing frozen native UI fixture before that manual loop. It calls the actual patched X-T2 display-policy entry0x14d9f90, lets the existing XPP hook dispatch the registries and executes the whole stock policy body through return. There is no manual mod-init loop or manual loader boot in the adapted file-chain check.

Nine real native policy returns verify:

- Modes0,1,2,7 refuse startup without invoking any mod init/late function.
- First REC mode3 invokes the four ordinary init entries and two late entries (film_loader_boot and the existing stock-choice settings start) exactly once, in registry order. Start errors0; loader timer has a real native handle.
- Re-entry in modes3,4,5,6 leaves those six invocations and the loader timer state unchanged. These are repeat-mode checks; first startup in each non-REC mode is not qualified.
- The original instruction at policy+4 executes on every call, and the native body returns0. No stock-policy/kernel success reply is substituted.

The generic settings-file registry is empty in this particular build; the existing choice-settings owner starts from its late function. No additional runtime service is introduced by the checker.

## Actual shared-channel ordering

The full late start enables an existing service that manual-init checks had skipped: FUJIMOD/SETTINGS.JSN loads before film files and occupies the shared cardio channel. The first connected run correctly stayed in loader WAIT instead of treating a settings request as a film listing. This was a verification-assumption failure, not evidence that the guard should be bypassed.

The checker now declares SETTINGS.JSN absent at the same existing lower filesystem lookup boundary (raw0x10a). Native open/worker/status mapping produces callback6; existing settings code applies defaults. Its linked owner state is checked: registered2, loads1, found0, last_error0; one owner, native settings timer running, last_start_status0. No successful native open/read/close or semaphore reply is supplied.

The two native storage-worker frames are retained after that missing-file request and resumed for the film file. Startup waits are not repeated or forcibly posted. Lower lookup is restored to the normal supplied-file boundary; native timers then allow the film loader to use the freed channel. The settings observation log is retained separately from the later file trace.

## Linked cases on the same artifact

| Film input after settings startup | Result |
| --- | --- |
| Valid original coefficient JSON | Native open/read/close -> parser/publisher -> real UI row/property -> actual still body; matrix,curve,chroma,luma equal JSON |
| Malformed JSON | Native read succeeds; parser rejects it, no card profile/row |
| Lower read error0x100 | Native read callback5 preserved, no card profile/row |

All three pass. File resources, banks and callbacks retire. Three reusable timer holds remain (settings timer, loader tick and loader poll), rather than the two of the earlier loader-only check. This is not a quiesce/cleanup proof. Existing exact-ELF NR43/3, JPEG33/3 and66-word delivery evidence remain unchanged; no unrelated repeat tests or rebuild were performed.

## Boundaries still explicit

Native filesystem/timer constructors, borrowed UI1 stack/context, calibration/REC/settings-pointer inputs, native profile enables and logical ticks remain supplied. Native policy is invoked from that context by the harness; the actual scheduler reaching its first policy call, reset-to-UI boot and service ownership are not proved. File reads retain the original three lower FS hooks, initialized context,3008-byte padded JSON and post-FAT directory/EOF frame. Settings absence is a lower lookup input; this does not establish native mount, FAT or physical SD.

A present settings document, write/persistence, sensor/capture/encoder/JPEG, all profile copies/exposure snapshots, concurrent cancellation/cleanup and physical caches/camera remain open. Do not interpret defaults loading or a native parameter block as saved settings or an image.

Next concrete gaps: qualify actual settings restore/persistence and remaining native startup ownership on the existing artifact, retaining these boundaries and the ordinary builder. Do not add a second settings service/loader or expand a peripheral model just to reach PASS.

## Original tools and prerequisites

`common_late_start_setup.py` supplies the frozen UI prefix before manual module init. `verify_common_late_start.py` reuses the original common-file checker, omits its redundant constructors/manual boot, runs the native policy, and retains worker frames across settings/file operations. Its `--invalid-json` and `--read-error 256` options select the negative cases. It preserves the original checker hash as fixture provenance and records the adapted source/helper hashes.

Run these files alongside the earlier helpers in the prepared local ports/fujimod-xt2 checkout. Required inputs include the unchanged171-file common-file freeze, prior authorized firmware/calibration/upstream and Python/toolchain dependencies. Linked shared C header layouts are locally pinned for the direct owner-state assertions. This is not a standalone public build.

Local evidence: common-late-start-check-unverified/{valid,invalid-json,read-error}.json and its separate freeze. Previous frozen artifacts remain untouched. Public files contain reviewed original code/docs only; no firmware, private C, vendor coefficients, raw reports/patch manifests or disassembly. Prepared with OpenAI Codex assistance.
