from . elasticfactor import ElasticFactor

from ... environment import cfg

def run(node):
    ad_id, factors = node.get('id', '63166071'), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    merged      = constructor.reduce(ad_id, *factors)

    return {
        ad_id: list(merged)
    }
