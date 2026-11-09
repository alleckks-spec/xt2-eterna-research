"""Adapt a pinned local XPP listing to X-T2 codes and existing callback banks.

Original AI-assisted adapter. Generated cardio.c is a private upstream derivative.
No new bank registry, job API or filesystem format: reuse the existing four
read/write callback banks and queue hold for listing, including orphan release.
"""
import argparse
import hashlib
import json
from pathlib import Path

PIN='7b77be6ea3513e5822baa2493a89e1ef1466c3c9'


def sha(b):return hashlib.sha256(b).hexdigest()


def prepare(source,output,original=False):
    raw=Path(source).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob==PIN
    text=raw.decode();out=Path(output);out.mkdir(parents=True,exist_ok=True)
    header=Path(__file__).with_name('xt2_cardio_listing_reference.h')
    (out/header.name).write_bytes(header.read_bytes())
    if not original:
        def replace(old,new):
            nonlocal text
            assert text.count(old)==1,old
            text=text.replace(old,new)
        replace('BANKED2(cb_open_write)','BANKED2(cb_open_write)\n#ifdef XPP_TARGET\nBANKED1(cb_list)\n#endif')
        replace('FIND_FIRST = 0x1370, FIND_NEXT = 0x1371','FIND_FIRST = XT2_FIND_FIRST, FIND_NEXT = XT2_FIND_NEXT')
        marker='        x70_cardio_hold = k + 1;\n#endif'
        replace(marker,'''        x70_cardio_hold = k + 1;
#else
        /* One native directory cursor: retain the existing queue hold until
         * the abandoned listing callback retires its bank. */
        if (job->op == X70_CARDIO_LIST) x70_cardio_hold = k + 1;
#endif''')
        start=text.index('static void cb_list_body(int status)')
        end=text.index('\n#endif',start)
        body=text[start:end]
        assert body.count('struct x70_cardio_job *job = x70_cardio_active;')==1
        body=body.replace('static void cb_list_body(int status)','static void cb_list_body(int bank, int status)')
        body=body.replace('struct x70_cardio_job *job = x70_cardio_active;',
                          'struct x70_cardio_job *job = x70_cardio_claim(bank);')
        body=body.replace('if (!job)\n        return;',
                          'if (!job) { x70_cardio_stale_drop(bank); return; }')
        wrapper='static void cb_list(int status) { cb_list_body(status); x70_callback_returned(); }\n'
        assert body.count(wrapper)==1;body=body.replace(wrapper,'')
        body=body.replace('= cb_list;','= cb_list[bank];')
        marker='x70_cardio_finish(job, 0);      /* keep what was listed */'
        assert body.count(marker)==1
        body=body.replace(marker,marker+'\n    else x70_cardio_unclaim(bank);')
        body=body.replace('    unsigned int n;','    unsigned int n;\n    int bank;')
        marker='    job->entries = entries;';assert body.count(marker)==1
        body=body.replace(marker,'    bank = x70_cardio_bank(job);\n'+marker)
        text=text[:start]+body+text[end:]
        text='#include "xt2_cardio_listing_reference.h"\n'+text
    (out/'cardio.c').write_text(text)
    report=dict(scope=__doc__,original=original,source_git_blob=blob,source_sha256=sha(raw),
        output_sha256=sha(text.encode()),generator_sha256=sha(Path(__file__).read_bytes()),
        header_sha256=sha(header.read_bytes()),new_bank_registry=False,hardware_verified=False)
    (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    return out/'cardio.c'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',action='store_true');a=p.parse_args()
    print(prepare(a.source,a.output,a.original))


if __name__=='__main__':main()
