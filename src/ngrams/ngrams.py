import functools

from .. tdm import TermDocumentMatrix
from .. tdm import n_grams
from .. tdm import get_results

def run(node):
    tokenizer = functools.partial(n_grams, numbers=True, normalize=True)
    tdm       = TermDocumentMatrix(cutoff=1, tokenizer=tokenizer)
    results   = get_results(node.get('text', None), node.get('size', 1000), True)

    tdm.load_dict(results, n=node.get('ngrams', 2), remove_duplicates=True)

    return {"results": tdm.term2doc()}
