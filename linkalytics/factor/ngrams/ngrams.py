import functools

from ... search import get_results
from .  entropy import TermDocumentMatrix, ngrams

def run(node):
    tokenizer = functools.partial(ngrams, numbers=True, normalize=True)
    tdm       = TermDocumentMatrix(cutoff=1, tokenizer=tokenizer)
    results   = get_results(node.get('text', 'cali'), node.get('size', 100), True)

    tdm.load_dict(results, n=node.get('ngrams', 2), remove_duplicates=True)

    return {"results": tdm.term2doc()}
