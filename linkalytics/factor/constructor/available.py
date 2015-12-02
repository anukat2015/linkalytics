from . elasticfactor import ElasticFactor
from ... environment import cfg

def run(node):
    ad_id  = node.get('id', '63166071')
    factor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])

    return {
        ad_id: factor.available(ad_id)
    }
