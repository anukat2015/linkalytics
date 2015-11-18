from datetime import datetime

from ... search import get_results, phone_hits, both_hits

from ... run_cli import Arguments

from multiprocessing.dummy import Pool as ThreadPool

pool = ThreadPool(4)

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

def parsetime(timestring):
    return datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S')

def specific_term(args):

    accumulator = lambda x: get_term(x, args)

    query     = args.query[0]
    results   = get_results(query, int(args.size[0]), True)
    phone     = unique_features("phone", results)
    posttime  = unique_features("posttime", results)

    output = {
        'phrase'      : query,
        'total'       : len(phone),
        'initial_date': parsetime(min(posttime)),
        'final_date'  : parsetime(max(posttime)),
    }

    output['results'] = dict(pool.map(accumulator, phone))

    return output

def get_term(pid, args):

    phone_res  = phone_hits(pid, int(args.size[0]))
    both_res   = both_hits(args.query[0], pid)
    date_phone = set()

    for v in phone_res.values():
        try:
            date_phone.add(v["posttime"])
        except:
            pass

    term = {
        'results':{
            'phone'  : phone_res['total'],
            'both'   : both_res['total'],
        },
        'date': {
            'initial': parsetime(min(date_phone)),
            'final'  : parsetime(max(date_phone)),
        }
    }

    return pid, term

def run(node):
    args = Arguments(node.get('text', 'bouncy'), node.get('size', 10))
    return specific_term(args)
