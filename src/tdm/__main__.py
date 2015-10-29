# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
import os
import functools

from elasticsearch  import Elasticsearch
from logging        import CRITICAL
from argparse       import ArgumentParser

from .. __version__ import __version__, __build__
from .. utils       import SetLogging
from .. utils       import timer
from .. utils       import search
from .. environment import cfg
from .  entropy     import n_grams
from .  entropy     import TermDocumentMatrix
from .  entropy     import filter_ngrams
from .  entropy     import get_connected_components_jaccard_similarity
from .  entropy     import similarity_to_csv

url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
es  = Elasticsearch(url, port=443, verify_certs=False, use_ssl=False, request_timeout=120)

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

def query_ad_ids(tdm, value="text"):
    """
    Query ads containing the n-gram
    We use a boolean Elastic query rather than phrase match because we may be working with a subset of the Elastic instance
    """
    phrases = tdm.term2doc()
    filtered_phrases = filter_ngrams(phrases, True, True)
    output = {}
    for k, v in filtered_phrases.items():
        results = query_ads(k, v, value)
        output[k] = results
    return output

@search(es)
def query_ads(k, v, value='text'):
    ad_ids = []
    for ad_id in v:
        ad_ids.append({ "term" : {"_id" : int(ad_id) }})
    if value == "text":
        size = len(ad_ids)
    else:
        size = 500
    query = {
        "filtered" : {
            "filter" : {
                "bool" : {
                    "should" : ad_ids
                }
            }
        }
    }

    payload = {
        "size": size,
        "query" : query
    }
    return payload


def command_line():
    description = 'Backend analytics to link together disparate data'
    parser      = ArgumentParser(prog='linkalytics', description=description)

    parser.add_argument('--version', '-v',
                        action='version',
                        version='%(prog)s ' + __version__ + '.0.0 ' + __build__
    )
    parser.add_argument('--ngrams', '-n', help='Amount of ngrams to seperate query',
                        metavar='n',
                        nargs=1,
                        default=[2],
    )
    parser.add_argument('--query', '-q', help='Elasticsearch query string',
                        metavar='query',
                        nargs=1,
                        default=['bouncy'],
    )
    parser.add_argument('--size', '-s', help='Maximum size of elasticsearch query',
                        metavar='size',
                        nargs=1,
                        default=[1000],
    )

    return parser.parse_args()

def main():
    args = command_line()

    print(args, file=sys.stderr)

    with SetLogging(CRITICAL):

        tokenizer = functools.partial(n_grams, numbers=True, normalize=True)
        tdm       = TermDocumentMatrix(cutoff=1, tokenizer=tokenizer)
        """Create the tdm from a json in the top level directory of linkalytics"""
        tdm.load_json('elastic.json', n=int(args.ngrams[0]), remove_duplicates=True)

        """Create the tdm from an Elastic query"""
        # results = search(args.query[0], int(args.size[0]), es, True)
        # with timer('Adding Docs to TDM takes'):
        #     tdm.load_dict(results, int(args.ngrams[0]))

        # with timer('Writing TDM takes'):
        #     tdm.write_csv('output.csv')

        output = query_ad_ids(tdm, "text")
        # print(output)
        cc_text = {}
        cc_phone = {}
        similarity_to_csv(output)


        # print(tdm.term2doc())

if __name__ == '__main__':
    sys.exit(main())
