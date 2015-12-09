from ... environment import cfg
from ... run_cli import Arguments

from .. lsh import lsh

from . elasticfactor import ElasticFactor
from elasticsearch import Elasticsearch
import time

es = Elasticsearch()
try:
    es.indices.create(index="factor_state2015")
    time.sleep(1)
except:
    pass

def run(node):
    ad_id, factors = node.get('id', '63166071'), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    initialized    = constructor.initialize(ad_id, *factors)

    # If Text Factor is Selected, run LSH to get near duplicates
    if 'text' in factors and initialized[ad_id]['text']:
        initialized[ad_id]['lsh'] = {}
        for text in initialized[ad_id]['text']:
            initialized[ad_id]['lsh'][text] = list(lsh(Arguments(text, 1000)))

    res = es.index(index="factor_state2015", id=int(time.time()), doc_type="analysis", body=initialized)
    return initialized
