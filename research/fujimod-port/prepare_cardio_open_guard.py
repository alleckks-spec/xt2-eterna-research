"""Apply the published cardio open-handle check to the pinned X-T2 source.

This is a bounded backport of x70view PR #471, not its full guarded backend.
Generated upstream derivatives remain private. The local listing/status fixes
are preserved. No request/token identity, watchdog, DMA or task gate is claimed.
"""
import hashlib
import json
from pathlib import Path
from prepare_cardio_status import prepare as prepare_status

UPSTREAM = '2e2aa8af51526f81ec22036502b02881507dcd00'
BAD_HANDLE = -23  # Published X70_CARDIO_BAD_HANDLE, PR #471.


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(source, output, original=False):
    path = prepare_status(source, output)
    parent = json.loads(path.with_name('preparation.json').read_text())
    text = path.read_text()
    if not original:
        anchor = '/* ---- read ---- */'
        assert text.count(anchor) == 1
        text = text.replace(anchor, '''/* Open-handle validation adapted from x70view PR #471,
 * Taylor Chapman (heytchap) and Claude (Anthropic), 2026-11.
 * X-T2 uses drive A's first token range; the native wrappers spin on zero.
 * This backport does not implement the PR's builder-token identity check. */
#define X70_CARDIO_BAD_HANDLE (-23)
static int xt2_open_handle_ok(int handle)
{
    return handle != 0 && (unsigned int)handle < 0x10000000u;
}

''' + anchor)
        anchor = '    job->handle = handle;\n    bank_handle[k] = handle;'
        assert text.count(anchor) == 2
        text = text.replace(anchor, '''    if (!xt2_open_handle_ok(handle)) {
        x70_cardio_finish(job, X70_CARDIO_BAD_HANDLE);
        return;
    }
''' + anchor)
        # Late invalid opens cannot own a usable A: handle. Drop their bank
        # without calling the native close wrapper, preserving callback counts.
        anchor = 'READ(bank_state[k]) != BANK_ORPHAN || !handle ||'
        assert text.count(anchor) == 1
        text = text.replace(anchor,
            'READ(bank_state[k]) != BANK_ORPHAN || !handle || (unsigned int)handle >= 0x10000000u ||')
        path.write_text(text)
    report = dict(scope=__doc__, original=original, upstream_commit=UPSTREAM,
        upstream_url='https://github.com/justjake/x70view/pull/471',
        credit='Taylor Chapman (heytchap) and Claude (Anthropic)',
        parent=parent, output_sha256=sha(path.read_bytes()),
        generator_sha256=sha(Path(__file__).read_bytes()),
        hardware_verified=False, full_pr_backported=False)
    path.with_name('preparation.json').write_text(json.dumps(report, indent=2)+'\n')
    return path
