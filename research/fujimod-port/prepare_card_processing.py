"""Adapt the existing card publisher/processing for coherent native API reads.

AI-assisted original transformation; generated private upstream derivatives,
firmware-derived preimages and target metadata remain local. Reuse the existing
table, timer observer, entry-hook ABI and per-context identity bytes. No new
runtime service, allocator or recipe-version store.
"""
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'card-films-expanded-build-unverified'
INPUTS=ROOT/'card-processing-inputs'


def sha(data):return hashlib.sha256(data).hexdigest()


def prepare():
    freeze=json.loads((BASE/'freeze.json').read_text())['files']
    sources=[ROOT/'card-films-inputs'/name for name in ['processing.c','cards.c']]
    for source in sources:assert sha(source.read_bytes())==freeze[str(source.resolve())]
    INPUTS.mkdir(exist_ok=True)
    header=Path(__file__).with_name('xt2_card_reader_reference.h')
    (INPUTS/header.name).write_bytes(header.read_bytes())
    text=sources[0].read_text();anchor='#include "film_xt20.h"';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n#include "xt2_card_reader_reference.h"\n'
        'extern struct xt20_film_recipe film_card_recipes[XT20_FILM_CARDS];\n'
        'extern volatile unsigned int film_card_count;')
    start=text.index('static const struct xt20_film_recipe *active_recipe(')
    end=text.index('static const struct xt20_film_recipe *replacing(',start)
    text=text[:start]+'''static const struct xt20_film_recipe *active_recipe(const unsigned char *profile)
{
    unsigned int index;
    if(profile[PROFILE_SPECIAL]==1 || profile[PROFILE_MAGIC1]!=RECIPE_MAGIC1 ||
       profile[PROFILE_MAGIC2]!=RECIPE_MAGIC2) return 0;
    index=profile[PROFILE_RECIPE];
    if(index>=1 && index<=XT20_FILM_COUNT)
        return profile[PROFILE_SLOT]==FILM_SLOT ? &xt20_film_recipes[index-1] : 0;
    if(!xt2_card_recipe_readable() || profile[PROFILE_SLOT]!=0) return 0;
    index-=XT20_FILM_COUNT+1;
    return index<XT20_FILM_CARDS && index<film_card_count ? &film_card_recipes[index] : 0;
}

'''+text[end:]
    start=text.index('int film_slot_hook(unsigned int *args)\n{')
    end=text.index('XPP_ENTRY_HOOK(film_slot_for_stored',start);body=text[start:end]
    anchor='    return 0;\n}'
    at=body.rfind(anchor);assert at>=0
    body=body[:at]+'''    for(i=0; i<XT20_FILM_CARDS && i<film_card_count; ++i) {
        if(recipe!=&film_card_recipes[i]) continue;
        profile[PROFILE_RECIPE]=XT20_FILM_COUNT+i+1;
        profile[PROFILE_MAGIC1]=RECIPE_MAGIC1;
        profile[PROFILE_MAGIC2]=RECIPE_MAGIC2;
        film_sims_active=0xff;
        break; /* Converted card recipes keep PROVIA's native slot. */
    }
'''+body[at:];text=text[:start]+body+text[end:]
    anchor='    if (!recipe) return 0;\n    out[0] = recipe->chroma[0];';assert text.count(anchor)==1
    text=text.replace(anchor,'''    if(!recipe && xt2_card_recipe_readable())
        for(i=0; i<XT20_FILM_CARDS && i<film_card_count; ++i)
            if(temporary[0]==(unsigned int)&film_card_recipes[i]) recipe=&film_card_recipes[i];
'''+anchor)
    stock_path=ROOT.parents[1]/'firmware/research/xt2-stock-sd-unverified/ffboot.bin'
    stock=stock_path.read_bytes();assert sha(stock)=='fff0913c8c9a51870e2e6e0da4aa5408a77c3ed508ea1c6157de0baa890006a2'
    symbols={'xt2_params_assemble':0x1565c20,'xt2_still_params_build':0x170cda0}
    for name,n in [('xt2_params_assemble',2),('xt2_still_params_build',7)]:
        address=symbols[name];word=struct.unpack_from('<I',stock,address)[0]
        assert word&0xffff0000==0xe92d0000 and word&0x4000
        handler=name+'_guard';typ=name+'_type'
        text+=f'''\ntypedef unsigned int {typ}({', '.join(['unsigned int']*n)});
void {handler}_stock(void);
int {handler}(unsigned int *args)
{{
    xt2_card_read_begin();
    args[0]=XPP_STOCK({handler}, {typ})({', '.join(f'args[{i}]' for i in range(n))});
    xt2_card_read_end();
    return 1;
}}
XPP_ENTRY_HOOK({name}, {handler}, {word:#x});
'''
    (INPUTS/'processing.c').write_text(text)
    cards=sources[1].read_text();anchor='#include "film_xt20.h"';assert cards.count(anchor)==1
    cards=cards.replace(anchor,anchor+'''\n#include "xt2_card_reader_reference.h"
X70_SHARED volatile unsigned int xt2_card_access_state;
X70_SHARED static volatile unsigned int xt2_card_publish_pending;
''')
    old='void film_user_publish(void)\n{';assert cards.count(old)==1
    cards=cards.replace(old,old+'''
    if(!xt2_card_write_begin()) { xt2_card_publish_pending=1; return; }
    xt2_card_publish_pending=0;''')
    old='    ++film_card_publishes;\n    request_show();';assert cards.count(old)==1
    cards=cards.replace(old,'    ++film_card_publishes;\n    xt2_card_write_end();\n    request_show();')
    old='void film_cards_tick(void)\n{\n    request_show();';assert cards.count(old)==1
    cards=cards.replace(old,'void film_cards_tick(void)\n{\n    if(xt2_card_publish_pending) film_user_publish();\n    request_show();')
    (INPUTS/'cards.c').write_text(cards)
    report=dict(scope=__doc__,sources={str(p):sha(p.read_bytes()) for p in sources},
        outputs={str(INPUTS/n):sha((INPUTS/n).read_bytes()) for n in ['processing.c','cards.c',header.name]},
        target_symbols=symbols,header_sha256=sha(header.read_bytes()),generator_sha256=sha(Path(__file__).read_bytes()),
        native_coverage_unqualified=True,hardware_verified=False)
    (INPUTS/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':print(json.dumps(prepare()))
