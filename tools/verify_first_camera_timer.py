"""Run the unchanged native timer assay with the existing full-image fixture.

The original four-mod setup has obsolete placement bounds. The newer existing
fixture selects the exact manifest's region; timer assertions are unchanged.
"""
import json
import sys
from pathlib import Path
import verify_full_timer_dispatch as timer
from verify_first_camera_menu import make_machine
from build_modular_candidate import sha


if __name__ == '__main__':
    timer.make_machine = make_machine
    timer.main()
    output = Path(sys.argv[sys.argv.index('--output')+1])
    report = json.loads(output.read_text())
    report.update(setup_adapter_sha256=sha(Path(__file__).read_bytes()),
                  setup_adapter_helper_sha256=sha(Path(__file__).with_name('verify_first_camera_menu.py').read_bytes()),
                  timer_assertions_unchanged=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
