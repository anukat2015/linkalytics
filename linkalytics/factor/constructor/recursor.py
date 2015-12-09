from ... environment import cfg
from ... run_cli import Arguments

from .. lsh import lsh

from . elasticfactor import ElasticFactor


def run(node):
    _id, factor_fields, factor_values, factors = node.get('_id', '1449687484'), node.get('factor_fields', ['phone', 'email', 'text', 'title']), node.get('factor_values', ['5023030050', '5023691601']), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    status    = constructor.recurse(_id, factor_fields, factor_values, factors)
    return status
