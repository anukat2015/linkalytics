from . elasticfactor import ElasticFactor

from ... environment import cfg
from elasticsearch import Elasticsearch


def run(node):
    id_a, id_b 	= node.get('id_a', '63166071_1'), node.get('id_b', '63166071_2')
    es 			= Elasticsearch()
    data_a 		= es.get(index="factor_state2016", doc_type='factor_network', id=id_a)
    data_b 		= es.get(index="factor_state2016", doc_type='factor_network', id=id_b)
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    merged 		= constructor.merge(data_a["_source"], data_b["_source"])
    return merged
