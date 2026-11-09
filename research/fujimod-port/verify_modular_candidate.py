"""Reuse exact-artifact card/processing/NR checks on the modular candidate.

Bounded evidence only; original fixtures and hardware limitations still apply.
AI-assisted; no new emulation or success responses.
"""
from verify_ordinary_platform_processing import main as processing
from verify_ordinary_platform_nr import load, ROOT, START, END
from verify_nr_candidate import verify as noise_reduction

BUILD=ROOT/'modular-build-unverified'


def main():
    processing(BUILD,ROOT/'modular-processing-check-unverified')
    output=ROOT/'modular-nr-check-unverified';output.mkdir(exist_ok=True)
    noise_reduction(build_function=lambda:load(BUILD),output=output,resident_region=(START,END),
        binding_audit=ROOT/'nr-candidate-unverified/binding-audit.json',
        artifact_files=[BUILD/'manifest.json',BUILD/'mods.elf',BUILD/'region.bin',
                        BUILD/'source-roots.json',ROOT/'modular-build-unverified-card/manifest.json'])


if __name__=='__main__':main()
