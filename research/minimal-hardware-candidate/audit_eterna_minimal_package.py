"""Read-only integrity gate for the fixed SEPIA-alias candidate, not a boot test.

Original tooling developed with OpenAI Codex assistance. Python standard library
only. Supply the private candidate directory and stock ffboot.bin locally; no
firmware, donor tables or patch manifest are distributed with this script.
"""
import argparse
import hashlib
import json
from pathlib import Path

IMAGE = '0f14244971768d783e09d4eb21fe59e60262ea183b938d31ff1fff170caceddf'
STOCK = 'fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
HEADER = 'b1e52216d083b43b430b2abcb880ebf72ca055c0ff9623d23bc03bddcb539351'
DAT = 'dd02ec5a862cf0e6f03a519a600ed99435efa442848249945b13ca6d78fabb25'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(candidate, stock_file):
    stock = stock_file.read_bytes()
    image = (candidate / 'ffboot.bin').read_bytes()
    header = (candidate / 'ffsys.bin').read_bytes()
    dat = (candidate / 'FWUP0010.DAT').read_bytes()
    manifest = json.loads((candidate / 'manifest.json').read_text())
    require(digest(stock) == STOCK, 'Wrong stock carrier')
    require(digest(image) == IMAGE == manifest['image_sha256'], 'Wrong candidate')
    require(len(image) == len(stock) == manifest['image_size'] == 46505984,
            'Image length differs')
    require(digest(header) == HEADER == manifest['header_sha256'] and len(header) == 2048,
            'Wrong SD header')
    require(digest(dat) == DAT == manifest['original_dat_sha256'] and len(dat) == 53543964,
            'DAT is not the original update')
    require(manifest['stock_sha256'] == STOCK and manifest['alias_id'] == 5
            and manifest['replaced_simulation'] == 'SEPIA'
            and manifest['hardware_verified'] is False, 'Wrong manifest scope')
    # Replay sequentially: specialization writes intentionally overlap generic stubs.
    replay = bytearray(stock)
    for edit in manifest['edits']:
        address = edit['address']
        old, new = bytes.fromhex(edit['old']), bytes.fromhex(edit['new'])
        require(len(old) == len(new) and 0 <= address <= len(replay) - len(new),
                'Invalid edit extent')
        require(replay[address:address + len(old)] == old, 'Edit preimage differs')
        replay[address:address + len(new)] = new
    require(replay == image, 'Unlisted or missing candidate changes')
    changed = sum(a != b for a, b in zip(stock, image))
    require(changed == manifest['changed_bytes'] == 8705, 'Change count differs')
    # Preserve the stock carrier's loader, preloaded-state controls, section table
    # and public-ID conversion table. This does not execute those paths.
    preserved = [(0, 0x100000), (0x950000, 0x950400), (0xCE5050, 0xCE5098),
                 (0xCE4358, 0xCE435C), (0xCE51AC, 0xCE51B0),
                 (0xFADC58, 0xFADC59), (0xE8BBB4, 0xE8BD04)]
    require(all(image[a:b] == stock[a:b] for a, b in preserved),
            'Carrier or public conversion path changed')
    return dict(scope=__doc__, status='PASS: package integrity only',
                image_sha256=IMAGE, image_size=len(image), changed_bytes=changed,
                manifest_sha256=digest((candidate / 'manifest.json').read_bytes()),
                header_sha256=HEADER, original_dat_sha256=DAT,
                edits_replayed=len(manifest['edits']), carrier_controls_preserved=True,
                rom_transfer_tested=False, patch_lifetime_tested=False,
                continuous_capture_tested=False, hardware_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('stock_ffboot', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.candidate, args.stock_ffboot), indent=2))
