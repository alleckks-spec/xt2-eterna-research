"""Run existing six-film checks plus explicit context-identity regression cases.

This does not qualify all native writers/copies or hardware lifetime. AI-assisted.
"""
from verify_six_films_candidate import main
from verify_ordinary_platform_nr import ROOT

if __name__=='__main__':
    main(ROOT/'context-films-build-unverified',ROOT/'context-films-check-unverified',True)
