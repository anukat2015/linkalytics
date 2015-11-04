from datetime import datetime

from .. tdm import get_results
from .. tdm import unique_features
from .. tdm import phone_hits
from .. tdm import both_hits

class Arguments:

    def __init__(self, query, size):
        self.query = [query]
        self.size  = [size]

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
    for i in phone:
        phone_res  = phone_hits(i, int(args.size[0]))
        both_res   = both_hits(query, i)
        date_phone = set()
        for v in phone_res.values():
            try:
                date_phone.add(v["posttime"])
            except:
                pass
        results = {
            'results':{
                'phone': phone_res['total'],
                'both' : both_res['total'],
            },
            'date': {
                'initial': parsetime(min(date_phone)),
                'final'  : parsetime(max(date_phone)),
            }
        }

        output['results'][i] = results

    return output

def run(node):
    args = Arguments(node.get('text', 'bouncy'), node.get('size', 10))
    return specific_term(args)
