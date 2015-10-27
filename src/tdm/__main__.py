# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

from elasticsearch  import Elasticsearch
from logging        import CRITICAL
from argparse       import ArgumentParser

from .. __version__ import __version__, __build__
from .. utils       import SetLogging
from .. utils       import timer
from .. environment import cfg
from .  entropy     import search
from .  entropy     import TermDocumentMatrix
from .  entropy     import get_ad_ids
from .  entropy     import query_ad_ids
from .  entropy     import get_connected_components_jaccard_similarity

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
                        default=['cali'],
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

        url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
        es  = Elasticsearch(url, port=443, verify_certs=False, use_ssl=False, request_timeout=120)

        results = search(args.query[0], int(args.size[0]), es, True)
        tdm     = TermDocumentMatrix(cutoff=1)

        with timer('Adding Docs to TDM takes'):
            tdm.load_dict(results, int(args.ngrams[0]))

        with timer('Writing TDM takes'):
            tdm.write_csv('output.csv')

        # print(tdm.sum_columns(), file=sys.stderr)
        output = query_ad_ids(es, tdm, "you the cali way dont", "text")
        cc = get_connected_components_jaccard_similarity(output, .1)
        print("There are " + str(len(cc)) + " connected components for 'you the cali way dont', which are made up of the following ad_ids:", file=sys.stderr)
        print(cc, file=sys.stderr)
        print(tdm.term2doc())

if __name__ == '__main__':
    sys.exit(main())
