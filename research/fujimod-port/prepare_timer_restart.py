"""Fix restart/cancel ownership in a locally supplied pinned XPP timer wrapper.

AI-assisted original adapter. Output is a private upstream source derivative,
not a public source release. X70's branch is preserved; only XPP behavior is
qualified. The existing hold and timer APIs are reused; no new resource layer.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(b):return hashlib.sha256(b).hexdigest()


def prepare(source,output):
    raw=Path(source).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert blob=='f872a416c84fd5639547213ecf4dd3c6e1633db4'
    text=raw.decode()
    replacements={
        '    x70_timer_stop(context);\n    return 0;':
        '''#ifdef XPP_TARGET
    return x70_timer_stop(context);
#else
    x70_timer_stop(context);
    return 0;
#endif''',
        '    if (x70_lifetime_stopping()) return X70_LIFETIME_STOPPING;':
        '''    if (x70_lifetime_stopping()) return X70_LIFETIME_STOPPING;
#ifdef XPP_TARGET
    if (timer->running) {
        status = x70_timer_stop(timer);
        if (status) return status;
    }
#endif''',
        '    timer->running = 0;\n#ifdef XPP_TARGET\n    return software_timer_cancel((unsigned int)timer->handle);':
        '''#ifdef XPP_TARGET
    int status = software_timer_cancel((unsigned int)timer->handle);
    if (!status) timer->running = 0;
    return status;'''}
    # The X70 branch retains its original early running clear.
    for old,new in replacements.items():
        assert text.count(old)==1,old
        text=text.replace(old,new)
    old='#else\n    return ui_sys_stop_timer((int)timer->handle);'
    assert text.count(old)==1
    text=text.replace(old,'#else\n    timer->running = 0;\n    return ui_sys_stop_timer((int)timer->handle);')
    out=Path(output);out.mkdir(parents=True,exist_ok=True);(out/'timer.c').write_text(text)
    report=dict(scope=__doc__,source_git_blob=blob,source_sha256=sha(raw),
        output_sha256=sha(text.encode()),generator_sha256=sha(Path(__file__).read_bytes()),
        xpp_cancel_before_restart=True,keep_running_on_cancel_failure=True,
        propagate_cleanup_failure=True,hardware_verified=False)
    (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    return out/'timer.c'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(prepare(a.source,a.output))


if __name__=='__main__':main()
