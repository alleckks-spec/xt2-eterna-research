# Native custom-record film byte serialization

Exact five-mod ELF:
`58eab0e9177c61d00b689b4bd08ae3c52cb7215975266f7bc93d6462d0c3affa`.
This is a new serialization-boundary check, not a journal write, reboot or
per-slot extra-film recall claim. No firmware/ELF/SD bytes were changed.

`verify_custom_slot_film_serialization.py` reuses the initialized native UI
machine. For each current film key0 and32..37, it selects through the actual
property hook and verifies the ordinary film getter returns0. It then executes
the native SAVE doorway, actual stock copy/property setters and first journal
descriptor construction for each native custom-record index0..6. Selection
mode/current settings, destination index and valid neighboring records remain
declared fixtures. The SAVE run stops before journal transport.

All49 combinations pass. The destination film byte becomes stock PROVIA0;
the six added choice keys remain only in the linked volatile choice state.
Other seven primary records remain byte-identical. The journal descriptor
selects the actual destination record,256bytes and the expected stock record
offset. Existing scalar-offset evidence independently identifies the film field;
the check does not infer its location from the observed zero value.

Report: `custom-slot-film-check-unverified/verification.json`. The report retains
exact ELF/stock/checker and native setup hashes, per-case record hashes and
descriptors. It contains no successful NAND result. Native UI-label mapping
to the visible C1-C7 names is not independently qualified by this assay.

## Test development and limits

Early exploratory input used an invalid film-byte marker; it was replaced with
valid stock film3. An earlier attempt observed the existing diagnostic GPIO
boundary. Those attempts did not produce a PASS report. The final checker uses
the valid fixture and passive instruction trace. An initial mistaken index set
1..7 revealed that index7 takes a different native current-settings journal
route (3700bytes), rather than the256-byte custom-record route. The final seven
custom-record indices are0..6; this change follows actual native behavior, not
a skipped failing custom slot. The old discovery report is retained separately.

The frozen prior SAVE fixture tested one record without the mod selection.
This check is justified by the previously untested extra-film property hooks
and all seven destinations on the new exact ELF. The native helper still
borrows a UI task and initialized profile/calibration state; this does not prove
native menu entry, physical controls, full startup or healthy camera state.

The result establishes that these49 SAVE paths serialize the underlying stock
film. It does not establish all internal serializers, live/still producer
lifetime, custom-slot recall/reset, independent extra choices in C1-C7,
successful journal completion, power-cycle preservation or physical NAND/SD.
The existing codec's C1-C7 schema is not promoted to working per-slot support.
Next follow the real native custom-record recall and visible slot selection,
preserving ordinary fields; retain the current choice on SD through the existing
settings service only after positive native writes are qualified.
