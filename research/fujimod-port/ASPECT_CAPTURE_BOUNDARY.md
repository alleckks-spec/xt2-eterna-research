# X-T2 aspect capture: installed native hook boundary

Isolated component ELF:
`b46a6477594da4816573931482a796d57ea11da1d2c503e51b7ec34878c610dd`.
Directories `aspect-capture-component-v2-unverified` and
`aspect-capture-component-v2-rebuild-unverified` have byte-identical ELF.
Uses the pinned existing upstream capture/geometry sources, existing XPP hook
mechanism and the exact f113fa3f chooser's selected-ratio storage. This is a
component placement, not the final SD configuration.

## New evidence

- `aspect-capture-function-check-unverified/verification.json`: actual ARM
  hooks pass 18 L/M/S × square/16:9/17:6 × SHORT/LONG Exif cases. Explicit
  descriptor/header/RAF-record fixtures verify crop windows, source/pitch/
  destination preservation, both RAF pairs with surrounding canaries and
  consumption of the saved pointers. Native 3:2, miniature, nonzero offsets,
  unknown dimensions, null descriptor and invalid-ratio controls pass.
- `sdk-native-aspect-main-v3-unverified/probe.json`: real native request
  producer and worker enter the installed JPEG function hook. With selected
  ratio 1:1, the native 6000×4000 descriptor becomes x=1000/y=0/4000×4000,
  pitch6000, source0, destination unchanged. The original prologue executes;
  execution stops before hardware programming.
- `sdk-native-aspect-thumbnail-unverified/probe.json`: the same installed
  native path leaves the native 160×120 miniature unchanged.

SDK checks reuse the existing CPU/VFP/kernel/clock/domain/SD prerequisites,
JPEG and power nodes. No new emulator or successful encoder reply is added.
The selected ratio, camera geometry and worker header remain explicit inputs.
Blank RAM backs the native-observed destination addresses so the existing
Exif scanner can read them; no header or encoded bytes are supplied there.
The FS mount workspace remains its original 1 MiB.

Earlier `sdk-native-aspect-main-v2-unverified` records a read-unmapped failure
inside that scanner: the old descriptor probe did not map destination buffers.
It is retained. This was a missing fixture input, not a successful image test.

## Still open

Main source0 means developed-image input is absent: no valid image, JPEG output
or pixel crop is proven. The Exif tests use declared headers, not native-built
headers. The preview geometry function test uses donor letterbox dimensions;
X-T2 preview pixels remain unqualified. Saved RAF pointers and selected ratio
still need actual shot ordering/overlap/lifetime proof. Native applied-aspect
setter/camera-info propagation, M/S native request production and full RAF/file
output remain open. No camera, ROM-to-SD boot or physical SD result is claimed.

## Reproduce locally

Use the existing GNU ARM13.2/LLD tools and pinned private inputs. Run
`build_aspect_capture_component.py --output NEW_DIRECTORY`; then run
`verify_aspect_capture_component.py` with the existing Unicorn TCI environment.
Run `probe_sdk_native_aspect_capture.py --kind 1 --output NEW_DIRECTORY` and
`--kind 0` with the emulator-enabled pinned SDK Python package.
The builder/verifiers depend on existing local firmware, private upstream
inputs, chooser component and earlier harnesses. Public originals do not
redistribute those inputs or constitute a standalone camera package.

Next: qualify applied-aspect and shot ownership/lifetime, then integrate the
complete existing capture variant with the compatible common configuration.
