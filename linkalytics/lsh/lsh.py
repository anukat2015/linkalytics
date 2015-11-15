from . import nearduplicates

from .. run    import Arguments
from .. search import get_results

def lsh(args, threshold=0.7):
    results    = get_results(args.query[0], int(args.size[0]), True)

    hashcorpus = [
        nearduplicates.run_getminhash({'id': key, 'text': value['text']})
            for key, value in results.items() if 'text' in value
        ]

    doc_to_lsh, lsh_dict = nearduplicates.run_lsh_batch(
        {
            'threshold': threshold,
            'data'     : hashcorpus
        }
    )

    hashdict = {
        obj['id']: obj['hashv'] for obj in hashcorpus
    }

    output = {}

    for i in results:
        docs = {
            'seed'      : i,
            'hashcorp'  : hashdict,
            'doc_to_lsh': doc_to_lsh,
            'lsh_dict'  : lsh_dict,
            'threshold' : threshold
        }
        cluster = nearduplicates.run_near_duplicates(docs)
        for j in cluster:
            if j != i:
                print('', results[j]['text'], sep='\t')
                if not output.get(i, None):
                    output[i] = [{j: results[j]['text']}]
                else:
                    output[i].append({j: results[j]['text']})

    for k, v in results.items():
        docs = {
            'seed'      : k,
            'hashcorp'  : hashdict,
            'doc_to_lsh': doc_to_lsh,
            'lsh_dict'  : lsh_dict,
            'threshold' : threshold
        }

        return output


def run(node):
    query, size = node.get('text', 'cali'), node.get('size', 1000)

    args = Arguments(query, size)

    return lsh(args)
