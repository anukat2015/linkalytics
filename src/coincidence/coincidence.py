from datetime import datetime

from .. tdm import get_results
from .. tdm import unique_features
from .. tdm import phone_hits
from .. tdm import both_hits
from .. tdm import Arguments

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
