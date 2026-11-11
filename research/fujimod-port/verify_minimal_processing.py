"""Reuse the bounded ETERNA function assay on the exact single-film SD artifact.

These are isolated native processing/selection calls with existing calibration
and uncontended transport fixtures. No scheduled startup, capture or camera
result. The changed ELF is why the processing checks are run again.
"""
import json
from pathlib import Path
from verify_ordinary_platform_nr import ROOT,START,END,load,sha
from verify_processing import verify
from verify_ordinary_platform_processing import actual_factory,initialize,select,TRANSPORT,transport_calls
from verify_ordinary_platform_card import main as card_check

BUILD=ROOT/'minimal-build-unverified'
OUT=ROOT/'minimal-check-unverified/processing'

def main():
    words=len(json.loads((BUILD/'manifest.json').read_text())['words'])
    card_check(BUILD,words)
    def build():
        sections,symbols,report=load(BUILD,words)
        from build_fixture import BINDINGS
        for edit in report['edits']:
            if edit['address'] not in {a for a,_ in BINDINGS.values()}:continue
            assert edit['value'] & 0xff000000 == 0xea000000
            displacement=(edit['value'] & 0xffffff)<<2
            if displacement & 0x2000000:displacement-=0x4000000
            edit['thunk']=edit['address']+8+displacement
        return sections,symbols,report
    verify(build_function=build,output_directory=OUT,resident_region=(START,END),
           actual_factory=actual_factory,
           initialize=lambda u,s,i:initialize(u,s,i,1),select_profile=select,
           selection_write_ranges=((0xffd000,0x1000000),(0x1180000,0x1235000),(0x1ab0000,0x1ad0000)))
    path=OUT/'processing-verification-tci.json';report=json.loads(path.read_text())
    report.update(scope=__doc__,elf_sha256=sha((BUILD/'mods.elf').read_bytes()),
        transport_fixtures=dict(results=TRANSPORT,calls=transport_calls),
        manual_init=True,full_boot=False,hardware_verified=False)
    path.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
