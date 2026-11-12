# Abandoned directory cursor: PR308 reuse

This closes one software lifetime gap in the current common X-T2 build.
PR308 head `6d189457bf14e9894b917fbd62e4479eea8eb2ff`, cardio blob
`fa270bb8a13f0ef987e250c9ba1977c3936911eb`, supplies the existing drain of
an abandoned directory through its native end callback. The local preparation
tool extracts that narrow body; it retains the already qualified X-T2 status
classifier, recorded callback banks and post-capacity retry. No platform or SDK
update was needed. Upstream source and generated binaries remain local.

The original c19 ordinary build
`c19a87a6dcc779c6052ff6468c0dcc08d72d3a8f8f77badf0393b0f0ce749244`
admits a second list after the first successful callback of the abandoned list,
while the actual native FAT cursor is still live. This reproduces a lifetime
gap, not data corruption: the second list still returns four entries in this
bounded control run. Original entry canaries remain unchanged.

The updated 77-source ordinary build
`7b9a745635bbd4152bf4def02134bbc087dc104c7cf175473234873848b9ba9d`
rejects competing lists while that cursor remains live. Actual filesystem
task39 produces the abandoned list's statuses `0,0,0,0,6`. The next list is
admitted only after native end-of-directory and cursor closure, returns the
four declared filenames, and ends with no callback banks, active request or
queue hold remaining. No firmware API successes, callback values, registration,
VFP enable or polling calls were supplied by the host. Real native timers and
the existing SDK SD model execute the operation. Request submission/cancellation
and four preformatted files are declared fixture inputs.

Evidence:

- `sdk-native-list-drain-original-v2-unverified/probe.json`: genuine original
  cursor-state control.
- `sdk-native-list-drain-fixed-unverified/probe.json`: genuine fixed worker run.
- `native-directory-drain-check-unverified/verification.json`: matching checker,
  ELF pins, native results, unchanged entries and zero substitution checks.
- `cardio-list-drain-qualified-check-unverified/freeze.json`: earlier isolated
  component controls, including failure/EOF classification and native guard.
- `cardio-list-drain-native-final-check-unverified/freeze.json`: immutable local
  evidence for the new native-worker comparison.

The two whole builds also differ by the newly integrated controls backend;
the separately compiled original/fixed cardio component provides the isolated
comparison. These results qualify directory drain, not every function of the
77-source build. Controls configuration UI and dimensions-tail integration are
still being composed into the final common build. Physical SD, interruption,
power loss and camera operation remain untested. No hardware was connected.

Next: retain this source in the final composition and verify the final ELF's
affected storage/settings chain after the controls UI and dimensions are linked.
