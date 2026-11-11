"""Reuse the existing single immutable ETERNA adapter without profile-tail writes.

Private source inputs stay local. Keep the old candidate and its prepared inputs
unchanged. No new processing implementation, storage service or loader.
"""
from pathlib import Path
from prepare_minimal_candidate import prepare as prepare_volatile, ROOT, sha


def prepare():
    source = ROOT/'generated/processing.c'
    assert sha(source.read_bytes()) == 'dfa86814de350879d7b260ae51afcfe3c1c387aec4e9eb059e8363184b213725'
    output = ROOT/'single-eterna-inputs/minimal-inputs'
    receipt = prepare_volatile(output)
    # Already tested one-film adapter: slot9 alone identifies immutable ETERNA.
    # There is no shared latch and no need to assign profile padding to the mod.
    target = output/'processing.c'
    target.write_bytes(source.read_bytes())
    receipt['inputs'][str(source)] = sha(source.read_bytes())
    receipt['source_outputs'][str(target)] = sha(target.read_bytes())
    receipt.update(single_immutable_recipe=True, profile_tail_writes=False,
                   processing_source=str(source),
                   single_generator_sha256=sha(Path(__file__).read_bytes()))
    return receipt
