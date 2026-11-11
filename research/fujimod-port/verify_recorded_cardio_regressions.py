"""Reuse native regression controls after recording callback bodies for polling.

The invalid-open matrix now enters the real cardio poll after recording each
callback. Existing request-boundary stops remain stops, not successful APIs.
All other original checks are invoked unchanged through the dual-menu adapter.
"""
import inspect
import json
from pathlib import Path
import verify_composed_native_storage as dual
original=dual.original


def main():
    source=inspect.getsource(original.callback_cases)
    old="    code = 'def run():\\n' + body"
    new="    body = body.replace(\"                m.api(f'{wrapper}_{bank}', status, handle)\", \"                m.api(f'{wrapper}_{bank}', status, handle)\\n                m.api('x70_cardio_busy')\")\n"+old
    assert source.count(old)==1;source=source.replace(old,new)
    exec(compile(source,str(Path(original.__file__))+'::recorded-callback-controls','exec'),vars(original))
    import verify_common_card_file as common
    import verify_common_settings_restore as restore
    import verify_film_loader_file_boundary as filecheck
    getsource=inspect.getsource;overrides={};source_hashes={}
    # Retained native workers return to an explicitly supplied polling caller.
    # Drain the existing per-bank recording after restoring that caller frame.
    for module,name in [(filecheck,'main'),(common,'main'),(restore,'settle_startup')]:
        function=getattr(module,name);text=getsource(function);old_text=text
        if module is common:
            old='    def take():';assert text.count(old)==1
            text=text.replace(old,old+"\n        m.api('x70_cardio_busy')")
        else:
            old='\n        m.u.context_restore(outer)\n';assert text.count(old)==1
            text=text.replace(old,old+"        m.api('x70_cardio_busy')\n")
        if module is filecheck:
            old='for _ in range(n):m.call(0xcdf968)';assert text.count(old)==1
            text=text.replace(old,old+";m.api('x70_cardio_busy')")
        if module is not filecheck:
            exec(compile(text,str(Path(module.__file__))+'::recorded-native-poll','exec'),vars(module))
            function=getattr(module,name)
        overrides[function]=text
        source_hashes[str(Path(module.__file__))+'::'+name]=dict(original=original.sha(old_text.encode()),adapted=original.sha(text.encode()))
    inspect.getsource=lambda function:overrides[function] if function in overrides else getsource(function)
    try:dual.main()
    finally:inspect.getsource=getsource

    path=original.OUT/'recorded-callback-adapter.json'
    path.write_text(json.dumps(dict(scope=__doc__,checker_sha256=original.sha(Path(__file__).read_bytes()),
        original_checker_sha256=original.sha(Path(original.__file__).read_bytes()),adapted_callback_cases_sha256=original.sha(source.encode()),
        elf_sha256=original.sha((original.BUILD/'mods.elf').read_bytes()),explicit_native_poll_source_adapters=source_hashes),indent=2)+'\n')


if __name__=='__main__':main()
