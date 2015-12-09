from ... environment import cfg
from ... run_cli import Arguments

from .. lsh import lsh

from . elasticfactor import ElasticFactor


def run(node):
    _id = node.get('_id', '1449687484')
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    status    = constructor.current_status(_id)
    return status
