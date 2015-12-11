from ... environment import cfg
from ... run_cli import Arguments

from . elasticfactor import ElasticFactor
from elasticsearch import Elasticsearch


def run(node):
    """
    :param _id: str
        Str of elastic index _id
    :param factor_tuples: str
        Str to specify factor tuple: factor field, factor value e.g. phone, 415...

    return: update entity extended based on the user's post request
    type: dict
    """
    _id, factor_tuples, factors = node.get('_id', '63166071_1'), node.get('factor_tuples', [['phone', '5023030050'], ['phone', '5023691601']]), node.get('factors', ['phone', 'email', 'text', 'title'])
    constructor = ElasticFactor(cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"])
    state = constructor.current_status(_id)
    state.pop("_index")
    state.pop("_score")
    state.pop("_type")
    state_identifiers = []
    level = int(state["_id"].split("_")[1])
    if level == 1:
        for k1, v1 in state.items():       # k1 is _source or factor_type/value, v1 is ad_id
            if isinstance(v1, dict):
                for k2, v2 in v1.items():      # v2 is ad_id
                    if isinstance(v2, dict):
                        for k3, v3 in v2.items():  # v3 is factor_type
                            if v3:
                                for k4 in v3.keys():  # k4 is factor_value
                                    state_identifiers.append(k4)
    else:
        for k1, v1 in state["_source"].items():       # k1 is sourcecontents_x, v1 is factor_tuple
            if isinstance(v1, dict):
                for k2, v2 in v1.items():      # v2 is ad_id
                    if isinstance(v2, dict):
                        for k3, v3 in v2.items():  # v3 is factor_type
                            if isinstance(v3, dict):
                                for k4, v4 in v3.items():  # v4 is factor_value
                                    if k1 == "sourcecontents_1":
                                        state_identifiers.append(k4)
                                    elif isinstance(v4, dict):
                                        for k5 in v4.items():
                                            state_identifiers.append(k5)

    for i in range(0, len(factor_tuples)):
        """We are hitting a bottle neck here because we query a factor to ad_ids (additions), then we query each ad_id to get the next level of factors. BUT, we could've gotten this next level of factors from the initial query of a factor. So there's a little of code refactoring to do... """
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
    index_id = state["_id"].split("_")[0] + "_" + str(level + 1)
    state.pop("_id")
    if level > 1:
        for i in range(0, (level - 1)):
            state['sourcecontents_' + str(i + 1)] = state["_source"].pop('sourcecontents_' + str(i + 1))
    state['sourcecontents_' + str(level)] = state.pop('_source')
    es = Elasticsearch()
    res = es.index(index="factor_state2016", id=index_id, doc_type="factor_network", body=state)
    return state
