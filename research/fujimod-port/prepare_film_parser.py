"""Use the supplied XPP film header's custom-icon constants in the shared parser.

AI-assisted original adapter. The pinned shared parser refers to the X70-only
film_custom_icons object. XPP's film_gen.h instead declares the two constants;
its zero values mean no artwork. All parsing/schema behavior remains upstream.
Generated C is a private upstream derivative and must remain local.
"""
import hashlib
import json
from pathlib import Path


def prepare(source,output):
    raw=Path(source).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert blob=='77ad6f5e510b9e13e58a4aee4ee97f7ce4eac337'
    text=raw.decode()
    for old,new in [('film_custom_icons[0]','FILM_CUSTOM_ICON_PICKER'),
                    ('film_custom_icons[1]','FILM_CUSTOM_ICON_Q')]:
        assert text.count(old)==1
        text=text.replace(old,new)
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    # Preserve the source-relative generated schema include at its real path.
    header=(Path(source).parent/'../settings/generated/film.h').resolve()
    old='#include "../settings/generated/film.h"'
    assert text.count(old)==1
    text=text.replace(old,'#include "'+str(header)+'"')
    result=out/'film_parse.c';result.write_text(text)
    (out/'preparation.json').write_text(json.dumps(dict(
        source_git_blob=blob,source_sha256=hashlib.sha256(raw).hexdigest(),
        output_sha256=hashlib.sha256(text.encode()).hexdigest(),
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        hardware_verified=False),indent=2)+'\n')
    return result
