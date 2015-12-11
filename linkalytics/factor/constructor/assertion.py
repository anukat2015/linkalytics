from ... environment import cfg
from ... run_cli import Arguments

from . elasticfactor import ElasticFactor
from elasticsearch import Elasticsearch


def run(node):
    _id, factor_tuples, factors = node.get('_id', '63166071_1'), node.get('factor_tuples', [('phone', '5023030050'), ('phone', '5023691601')]), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    state = constructor.current_status(_id)
    state.pop("_index")
    state.pop("_score")
    state.pop("_type")
    state_identifiers = []
    for k1, v1 in state.items():       # k1 is _source or factor_type/value, v1 is ad_id
        if isinstance(v1, dict):
            for k2, v2 in v1.items():      # v2 is factor_type
                if isinstance(v2, dict):
                    for k3, v3 in v2.items():  # v3 is factor_value
                        if v3:
                            for k4 in v3.keys():  # k4 is factor_value
                                state_identifiers.append(k4)
    for i in range(0, len(factor_tuples)):
        """Rather than a reverse_lookup, we should be getting all the other factor_values produced by the first factor values"""
        name = factor_tuples[i][0] + "_" + factor_tuples[i][1]
        additions = constructor.reverse_lookup(factor_tuples[i][0], factor_tuples[i][1])
        state[name] = {}
        for ad_id in additions:
            new = constructor.initialize(ad_id, *factors)
            for k1, v1 in new.items():  # k1 is ad_id, v1 is factor_type
                state[name][k1] = {}
                for k2, v2 in v1.items():  # v2 is factor_value
                    for k3, v3 in v2.items():
                        if v2:
                            if k3 not in state_identifiers:
                                state[name][k1][k2] = v2
                if state[name][k1] == {}:
                    state[name].pop(k1)
        if state[name] == {}:
            state.pop(state[name])
    index_id = state["_id"].split("_")[0] + "_" + str(int(state["_id"].split("_")[1]) + 1)
    # state["index_id"] = index_id
    state.pop("_id")
    state['sourcecontents'] = state.pop('_source')

    es = Elasticsearch()
    res = es.index(index="factor_state2016", id=index_id, doc_type="factor_network", body=state)
    return state
