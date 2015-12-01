
from . elasticfactor import ElasticFactor
from . lsh           import lsh

from .. environment  import cfg
from .. run_cli      import Arguments

def run(node):
    ad_id, factors = node.get('id', '63166071'), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    combined    = constructor.combine(ad_id, *factors)

    # If Text Factor is Selected, run LSH to get near duplicates
    if 'text' in factors and combined[ad_id]['text']:
        combined[ad_id]['lsh'] = {}
        for text in combined[ad_id]['text']:
            combined[ad_id]['lsh'][text] = list(lsh(Arguments(text, 1000)))

    return combined

