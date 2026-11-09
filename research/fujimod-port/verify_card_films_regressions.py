"""Reuse existing NR/JPEG cases on the resized four-mod ordinary ELF.

AI-assisted parameter adapter only. Existing supplied calibration, manual init,
uncontended transport and bounded register/table scopes remain unchanged.
No numeric-film, card processing, service startup or hardware claim is added.
"""
import json
from pathlib import Path
import verify_ordinary_platform_nr as ordinary
import verify_jpeg_max_candidate as jpeg
from verify_ordinary_platform_processing import initialize
from verify_ordinary_platform_card import main as verify_card
from verify_nr_candidate import verify as verify_nr

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'card-films-expanded-build-unverified'
OUT=ROOT/'card-films-expanded-check-unverified'


def main():
    ordinary.START=0x1388000;ordinary.END=0x13c0000
    load=lambda:ordinary.load(BUILD,64)
    verify_nr(build_function=load,output=OUT/'nr',resident_region=(ordinary.START,ordinary.END),
        binding_audit=ROOT/'nr-candidate-unverified/binding-audit.json',expected_init_count=4,
        artifact_files=[BUILD/'manifest.json',BUILD/'mods.elf',BUILD/'region.bin',
                        Path(str(BUILD)+'-card')/'manifest.json'])
    jpeg.BUILD=BUILD;jpeg.OUT=OUT/'jpeg';jpeg.START=ordinary.START;jpeg.END=ordinary.END
    jpeg.load=lambda directory,count:ordinary.load(directory,64)
    jpeg.verify_card=lambda directory,count:verify_card(directory,64)
    jpeg.initialize=lambda u,symbols,call,count:initialize(u,symbols,call,4)
    jpeg.main()
    report=dict(scope=__doc__,nr=str(OUT/'nr/verification.json'),jpeg=str(OUT/'jpeg/verification.json'),
                ordinary_words=64,init_count=4,region=[ordinary.START,ordinary.END],hardware_verified=False)
    (OUT/'regressions.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
