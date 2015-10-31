# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import functools
import warnings

warnings.simplefilter('ignore')

from elasticsearch   import Elasticsearch
from logging         import CRITICAL
from argparse        import ArgumentParser
from datetime        import datetime

from .. __version__ import __version__, __build__
from .. environment import cfg
from .. utils       import SetLogging
from .. utils       import timer
from .. utils       import search
from .  entropy     import n_grams
from .  entropy     import TermDocumentMatrix
from .  entropy     import filter_ngrams
from .  entropy     import similarity_to_csv

from .  import nearduplicates

with warnings.catch_warnings():
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    es  = Elasticsearch(url, port=443, verify_certs=False, use_ssl=False, request_timeout=160)

@search(es)
def get_results(search_term, size, phrase=True):
    match_type = 'match_phrase' if phrase else 'match'
    payload = {
        "size": size,
        "query" : {
            match_type : {
                "_all" : search_term
            }
        }
    }
    return payload

@search(es)
def query_ads(k, v, value='text'):

    ad_ids = []
    for ad_id in v:
        ad_ids.append({ "term" : {"_id" : int(ad_id) }})

    size    = len(ad_ids) if value == 'text' else 500
    query   = { "filtered" : { "filter" : { "bool" : { "should" : ad_ids } } } }
    payload = { "size": size, "query" : query }

    return payload

@search(es)
def phone_hits(phone, size):
    payload = {
        "size": size,
        "query" : {
            "match_phrase": {
                "phone" : phone
            }
        }
    }
    return payload

@search(es)
def both_hits(search_term, phone):
    query =  {
        "bool": {
            "must": [
                { "match_phrase": { "_all": search_term } },
                { "match": { "phone": phone } }
            ]
        }
    }
    return { "size": 500, "query" : query }

def query_ad_ids(tdm, value="text"):
    """
    Query ads containing the n-gram

    We use a boolean Elastic query rather than phrase match
    because we may be working with a subset of the Elastic instance
    """
    phrases  = tdm.term2doc()
    filtered = filter_ngrams(phrases, True, True)
    output   = {}

    for k, v in filtered.items():
        results   = query_ads(k, v, value)
        output[k] = results

    return output

def command_line():
    """
    Parse command line arguments using Python arparse
    """
    description = 'Backend analytics to link together disparate data'
    parser      = ArgumentParser(prog='linkalytics', description=description)

    parser.add_argument('--version', '-v',
                        action='version',
                        version='%(prog)s ' + __version__ + '.0.0 ' + __build__
                        )

    subparsers = parser.add_subparsers()

    parser_run   = subparsers.add_parser('run')
    parser_lsh   = subparsers.add_parser('lsh')
    parser_term  = subparsers.add_parser('term')

    parser_run.add_argument('--ngrams', '-n', help='Amount of ngrams to seperate query',
                            metavar='n',
                            nargs=1,
                            default=[2],
                            )
    parser_run.add_argument('--query', '-q', help='Elasticsearch query string',
                            metavar='query',
                            nargs=1,
                            default=['bouncy'],
                            )
    parser_run.add_argument('--size', '-s', help='Maximum size of elasticsearch query',
                            metavar='size',
                            nargs=1,
                            default=[1000],
                            )
    parser_run.add_argument('--file', '-f', help='Load TDM from file',
                            metavar='file',
                            nargs=1,
                            )
    parser_lsh.add_argument('--query', '-q', help='Elasticsearch query string',
                            metavar='query',
                            nargs=1,
                            default=['bouncy'],
                            )
    parser_lsh.add_argument('--size', '-s', help='Maximum size of elasticsearch query',
                            metavar='size',
                            nargs=1,
                            default=[1000],
                            )
    parser_term.add_argument('--query', '-q', help='Elasticsearch query string',
                             metavar='query',
                             nargs=1,
                             default=['bouncy']
                             )
    parser_term.add_argument('--size', '-s', help='Maximum size of elasticsearch query',
                            metavar='size',
                            nargs=1,
                            default=[1000],
                            )

    parser_run.set_defaults(func=tdm)
    parser_lsh.set_defaults(func=lsh)
    parser_term.set_defaults(func=specific_term)

    if not len(sys.argv) - 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

def tdm(args):

    with SetLogging(CRITICAL):

        tokenizer = functools.partial(n_grams, numbers=True, normalize=True)
        tdm       = TermDocumentMatrix(cutoff=1, tokenizer=tokenizer)

        # Load from File
        if args.file:
            tdm.load_json(args.file[0], n=int(args.ngrams[0]), remove_duplicates=True)

        # Load from Elasticsearch
        else:
            results = get_results(args.query[0], int(args.size[0]), True)

            with timer('Adding Docs to TDM takes'):
                tdm.load_dict(results, n=int(args.ngrams[0]), remove_duplicates=True)

        with timer('Writing TDM takes'):
            tdm.write_csv('output.csv')

        output = query_ad_ids(tdm, "text")
        cc_text = {}
        cc_phone = {}
        similarity_to_csv(output)


        # print(tdm.term2doc())

def lsh(args):
    threshold = 0.7
    results    = get_results(args.query[0], int(args.size[0]), True)

    if 'total' in results:
        del results['total']

    hashcorpus = [
        nearduplicates.run_getminhash({'id': key, 'text': value['text']})
            for key, value in results.items() if 'text' in value
    ]

    doc_to_lsh, lsh_dict = nearduplicates.run_lsh_batch({'threshold': threshold, 'data': hashcorpus})

    hashdict = {
        obj['id']: obj['hashv'] for obj in hashcorpus
    }

    for k, v in results.items():
        print('Near Duplicates For:', v.get('text', None), sep='\t')
        docs = {
            'seed'      : k,
            'hashcorp'  : hashdict,
            'doc_to_lsh': doc_to_lsh,
            'lsh_dict'  : lsh_dict,
            'threshold' : threshold
        }
        cluster = nearduplicates.run_near_duplicates(docs)
        for j in cluster:
            if j != k:
                print('', results[j]['text'], sep='\t')


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
    results   = get_results(query, args.size[0], True)
    phone     = unique_features("phone", results)
    posttime  = unique_features("posttime", results)

    parsetime = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')

    print()
    print("Phrase:        {phrase}".format(phrase=query))
    print("Total Numbers: {total}".format(total=len(phone)))
    print("Initial Date:  {date:%Y-%m-%d %H:%M}".format(date=parsetime(min(posttime))))
    print("Final   Date:  {date:%Y-%m-%d %H:%M}".format(date=parsetime(max(posttime))))
    print()

    print("ID         Phone Both  Start              End")

    for i in phone:
        phone_res  = phone_hits(i, 1000)
        both_res   = both_hits(query, i)
        date_phone = set()
        for v in phone_res.values():
            try:
                date_phone.add(v["posttime"])
            except:
                pass

        print("{id} {phone:<5} {both:<5} {initial:%Y-%m-%d %H:%M} : {final:%Y-%m-%d %H:%M}".format(
                id=i,
                phone=phone_res['total'],
                both=both_res['total'],
                query=query,
                initial=parsetime(min(date_phone)),
                final=parsetime(max(date_phone)),
            )
        )

def main():
    args = command_line()
    print(args)
    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
