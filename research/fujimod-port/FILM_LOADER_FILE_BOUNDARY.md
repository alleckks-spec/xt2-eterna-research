# Existing loader through native file operations

AI-assisted original bounded check. Same separate loader component
`82b1a840…`; ordinary ELF/SD unchanged. This is a supplied filesystem-boundary
test, not successful access to a mounted camera card.

`verify_film_loader_file_boundary.py` connects the existing loader, the adapted
directory reader, native file APIs and actual parser. It reuses the earlier
`NativeProfileFSFixture` only for initialized downstream filesystem structures,
directory lookup, metadata and bytes. Its kernel/transport/semaphore hooks are
removed, and the overwritten native dispatch/queue/semaphore/instrumentation
locations are restored to their values after native construction. Exactly
three lower filesystem calls are supplied: lookup, entry metadata and data read.
Those assumptions do not establish card mounting or physical storage behavior.

The first directory record is written by native code from an explicitly
supplied post-FAT frame; the native EOF tail invokes the adapted C callback.
The loader's native timer poll chooses `200TEST.JSN` and calls open. Native
queues120/39 and both native workers then execute open, read and close, invoking
the compiled cardio callbacks. Their worker frames are retained across all
three operations: native initialization and its semaphore wait execute once,
and later operations resume the original loops. No callback or API return is
manually delivered at the public file/worker/transport level.

Three cases pass on the same exact component:

| Supplied file boundary | Actual consumer result |
| --- | --- |
| Valid JSON, padded with whitespace to3008 bytes | open0/nonzero handle → read0/3008 → close0; parser accepts ID200/name; loader DONE, one loaded film, catalog ready |
| Truncated JSON syntax, same length | native file chain completes; parser rejects it; loader DONE with one rejected entry and no loaded film |
| Lower read error0x100 | native mapping delivers read status5/count0; close0; loader retains error5 and rejects the entry |

All cases release the file alias, descriptor, reservation and context slot;
open count returns to zero. Cardio banks and outstanding callback count return
to zero. The two timer registry holds intentionally remain for reuse, so
`x70_lifetime_live()==2` here. An earlier draft incorrectly expected zero;
that checker assertion was corrected, without changing production code.

REC-idle, initialized filesystem structures, the directory/FAT frame and file
bytes are explicit fixtures. Software ticks and workers use scratch task0
contexts; this is not scheduled task ownership, physical IRQ delivery, full
boot or a native FAT traversal. The source publisher runs with card processing
disabled: its card count stays zero, and no new card rows or mutable recipes
are admitted. A loader catalog entry is not evidence that a card profile is
selectable or used by the image pipeline. Hardware remains untested.

## Dependencies and reproduction boundary

Use the component and dependencies in [FILM_LOADER_COMPONENT.md](FILM_LOADER_COMPONENT.md).
This checker additionally imports the locally supplied existing
`scripts/xt2_native_profile_fs_fixture.py`, together with that note's checker
and native-worker/clock helpers. Put the prepared `scripts` directory on
`PYTHONPATH`, use the existing TCI Unicorn library via `LIBUNICORN_PATH`, and
provide the stock flat image, common ELF, baseline cardio component and loader
component through the matching command-line arguments. `--invalid-json` and
`--read-error 0x100` select the two failure cases. Outputs must be distinct.
No firmware, JSON schema, source-profile coefficients, initialized-volume dump,
private upstream C, binary component or raw execution manifest is distributed.
This is not a standalone public build.
