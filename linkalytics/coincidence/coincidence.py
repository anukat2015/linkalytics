from datetime import datetime

from .. search import get_results, phone_hits, both_hits
from .. run import Arguments

def unique_features(feature, data):
    features = set()
    for v in data.values():
        try:
            if isinstance(v[feature], str):
                features.add(v[feature])
            elif isinstance(v[feature], list):
                for i in v:
                    features.add(v[feature])
        except:
            pass

    return features


def specific_term(args):

    query     = args.query[0]
    results   = get_results(query, int(args.size[0]), True)
    phone     = unique_features("phone", results)
    posttime  = unique_features("posttime", results)

    parsetime = lambda t: datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')

    output = {
        'phrase'      : query,
        'total'       : len(phone),
        'initial_date': parsetime(min(posttime)),
        'final_date'  : parsetime(max(posttime)),
        'results'     : {},
    }
    for pid in phone:
        phone_res  = phone_hits(pid, int(args.size[0]))
        both_res   = both_hits(query, pid)
        date_phone = set()
        for v in phone_res.values():
            try:
                date_phone.add(v["posttime"])
            except:
                pass

        output['results'][pid] = {
            'results':{
                'phone'  : phone_res['total'],
                'both'   : both_res['total'],
            },
            'date': {
                'initial': parsetime(min(date_phone)),
                'final'  : parsetime(max(date_phone)),
            }
        }

    return output

def run(node):
    args = Arguments(node.get('text', 'bouncy'), node.get('size', 10))
    return specific_term(args)
