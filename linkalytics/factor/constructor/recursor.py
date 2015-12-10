from ... environment import cfg
from ... run_cli import Arguments

from . elasticfactor import ElasticFactor


def run(node):
    _id, factor_fields, factor_values, factors = node.get('_id', '1449687484'), node.get('factor_fields', ['phone', 'phone']), node.get('factor_values', ['5023030050', '5023691601']), node.get('factors', ['phone', 'email', 'text', 'title'])
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
    for i in range(0, len(factor_fields)):
        additions = constructor.reverse_lookup(factor_fields[i], factor_values[i])
        state[factor_fields[i] + "_" + factor_values[i]] = {}
        for ad_id in additions:
            new = constructor.initialize(ad_id, *factors)
            for k1, v1 in new.items():  # k1 is ad_id, v1 is factor_type
                state[factor_fields[i] + "_" + factor_values[i]][k1] = {}
                for k2, v2 in v1.items():  # v2 is factor_value
                    for k3, v3 in v2.items():
                        if v2:
                            if k3 not in state_identifiers:
                                state[factor_fields[i] + "_" + factor_values[i]][k1][k2] = v2
                if state[factor_fields[i] + "_" + factor_values[i]][k1] == {}:
                    state[factor_fields[i] + "_" + factor_values[i]].pop(k1)
        if state[factor_fields[i] + "_" + factor_values[i]] == {}:
            state.pop(factor_fields[i] + "_" + factor_values[i])
    return state
