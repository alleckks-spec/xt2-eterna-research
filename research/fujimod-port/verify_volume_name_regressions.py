"""Existing film/NR/JPEG checks on the relocated five-mod volume-name artifact.

This parameter adapter reruns affected exact-ELF checks because added code/data
and the measured reservation resize change placement. It preserves the original
supplied calibration/manual-init/transport and bounded-function limitations.
"""
import argparse
import inspect
import json
from pathlib import Path
import verify_ordinary_platform_nr as ordinary
import verify_jpeg_max_candidate as jpeg
import verify_six_films_candidate as films
from verify_ordinary_platform_card import main as verify_card
from verify_ordinary_platform_processing import initialize
from verify_nr_candidate import verify as verify_nr

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'volume-name-resized-build-unverified')
    p.add_argument('--output', type=Path, default=ROOT/'volume-name-regressions-unverified')
    p.add_argument('--case', choices=['nr', 'jpeg', 'films'], required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    ordinary.START, ordinary.END = 0x1380000, 0x13c0000
    artifacts = [a.build/'manifest.json', a.build/'mods.elf', a.build/'region.bin',
                 Path(str(a.build)+'-card')/'manifest.json']
    if a.case == 'nr':
        verify_nr(build_function=lambda: ordinary.load(a.build, 68),
            output=a.output/'nr', resident_region=(ordinary.START, ordinary.END),
            binding_audit=ROOT/'nr-candidate-unverified/binding-audit.json',
            expected_init_count=4, artifact_files=artifacts)
    elif a.case == 'jpeg':
        jpeg.BUILD, jpeg.OUT = a.build, a.output/'jpeg'
        jpeg.START, jpeg.END = ordinary.START, ordinary.END
        jpeg.load = lambda directory, count: ordinary.load(directory, 68)
        jpeg.verify_card = lambda directory, count: verify_card(directory, 68)
        jpeg.initialize = lambda u, symbols, call, count: initialize(u, symbols, call, 4)
        jpeg.main()
    else:
        films.START, films.END = ordinary.START, ordinary.END
        def load_at(directory, words):
            # The comparison baseline is a separate unchanged artifact at its
            # own original reservation. Keep its original placement check.
            previous = ordinary.START
            if Path(directory).resolve() == (ROOT/'modular-build-unverified').resolve():
                ordinary.START = 0x1390000
            try:
                return ordinary.load(directory, words)
            finally:
                ordinary.START = previous
        films.load = load_at
        # The common card-films selection uses the published generated label
        # table, unlike the older six-film-only fixture's private text symbols.
        # Keep every numeric/ABI/menu/context check; bind only its caption
        # assertions to the selected source's actual table and declared labels.
        source = inspect.getsource(films.main)
        old = "        assert word==symbols[name+'_text']"
        assert source.count(old) == 1
        source = source.replace(old, "        assert word==int.from_bytes(actual.mem_read(symbols['film_xt20_labels']+20*i,4),'little')")
        old = "    expected_captions=['ETERNA','CLASSIC Neg.','ETERNA BLEACH BYPASS','NOSTALGIC Neg.','REALA ACE','NEUTRAL']"
        assert source.count(old) == 1
        source = source.replace(old, "    expected_captions=['ETERNA','Classic Neg. (approx.)','Bleach Bypass (approx.)','Nostalgic Neg. (approx.)','REALA ACE (approx.)','Neutral']")
        namespace = dict(vars(films))
        namespace['main'] = None
        exec(compile(source, str(Path(films.__file__)) + ':selected-card-labels', 'exec'), namespace)
        namespace['main'](a.build, a.output/'films', context_identity=True,
                          expected_words=68, expected_init_count=4)
    report = dict(scope=__doc__, case=a.case,
        elf_sha256=ordinary.sha((a.build/'mods.elf').read_bytes()),
        checker_sha256=ordinary.sha(Path(__file__).read_bytes()),
        changed_placement=True, words=68, init_count=4, hardware_verified=False)
    (a.output/(a.case+'-adapter.json')).write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
