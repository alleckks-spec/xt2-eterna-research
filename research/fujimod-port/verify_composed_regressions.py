"""Reuse existing numeric and delivered-memory checks for an explicit composition.

Only expected SD word count, artifact and output paths vary. Existing manual
function inputs and bounded-runtime limitations remain. Original reports and
sources stay immutable; each adapted source hash is recorded locally.
"""
import argparse
import inspect
import json
import sys
from pathlib import Path
import verify_volume_name_regressions as numeric
import verify_minimal_memory as memory
import verify_full_storage_guard as fixture
ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',choices=['films','nr','jpeg','memory'],required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((args.build/'manifest.json').read_text());words=len(manifest['words'])
    if args.case!='memory':
        source=inspect.getsource(numeric.main)
        old='choices=[68, 72, 73, 76]';assert source.count(old)==1
        source=source.replace(old,'choices=['+str(words)+']').replace('def main():','def execute():',1)
        namespace=dict(vars(numeric));before=sys.argv
        sys.argv=[before[0],'--build',str(args.build),'--output',str(args.output),'--case',args.case,'--words',str(words)]
        try:
            exec(compile(source,str(Path(numeric.__file__))+'::composed-artifact','exec'),namespace)
            namespace['execute']()
        finally:sys.argv=before
        report=json.loads((args.output/(args.case+'-adapter.json')).read_text())
    else:
        fixture.BUILD=args.build
        def machine():
            (u,symbols,call,api,clock,exceptions),setup=fixture.fixture_machine(False)
            return (u,symbols,call,clock,exceptions),setup
        start=int(manifest['regions'][0]['address'],0)
        target=json.loads((args.build/'target.json').read_text())
        base=json.loads((ROOT/'save-data-menu-native-build-unverified/target.json').read_text())
        assert target['card_regions']==base['card_regions'] and target['card_words']==base['card_words']
        assert start==0x1380000 and manifest['regions'][0]['size']<=0x40000
        source=inspect.getsource(memory.main).replace('def main():','def execute():',1)
        namespace=dict(vars(memory),machine=machine,BUILD=args.build,OUT=args.output,START=start,END=0x13c0000)
        exec(compile(source,str(Path(memory.__file__))+'::composed-artifact','exec'),namespace)
        namespace['execute']()
        report=json.loads((args.output/'memory.json').read_text())
    report.update(composition_adapter_scope=__doc__,composition_adapter_sha256=fixture.sha(Path(__file__).read_bytes()),
        original_source_sha256=fixture.sha(Path(numeric.__file__ if args.case!='memory' else memory.__file__).read_bytes()),
        adapted_source_sha256=fixture.sha(source.encode()),expected_words=words)
    path=args.output/(args.case+'-composition-adapter.json');path.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
