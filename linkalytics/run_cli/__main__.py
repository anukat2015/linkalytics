# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import sys
import functools

from argparse  import ArgumentParser
from logging   import CRITICAL

from .. factor_validator import coincidence
from .. factor.lsh       import lsh
from .. factor.ngrams    import TermDocumentMatrix, ngrams, filter_ngrams
from .. __version__      import __version__, __build__
from .. search           import query_ads, get_results
from .. utils            import SetLogging, timer

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

def tdm(args):

    with SetLogging(CRITICAL):

        tokenizer = functools.partial(ngrams, numbers=True, normalize=True)
        tdm       = TermDocumentMatrix(cutoff=1, tokenizer=tokenizer)

        # Load from File
        if args.file:
            with timer('Adding Docs to TDM takes'):
                tdm.load_json(args.file[0], n=int(args.ngrams[0]), remove_duplicates=True)

        # Load from Elasticsearch
        else:
            results = get_results(args.query[0], int(args.size[0]), True)

            with timer('Adding Docs to TDM takes'):
                tdm.load_dict(results, n=int(args.ngrams[0]), remove_duplicates=True)

    print(json.dumps(tdm.term2doc(), ensure_ascii=False, indent=4), file=sys.stdout)

def term(args):

    output = coincidence.specific_term(args)

    print()
    print("Phrase:        {phrase}".format(phrase=output['phrase']))
    print("Total Numbers: {total}".format(total=output['total']))
    print("Initial Date:  {date:%Y/%m/%d}".format(date=output['initial_date']))
    print("Final   Date:  {date:%Y/%m/%d}".format(date=output['final_date']))
    print()

    print("ID         Phone Both  Start       End")

    for _id, results in output['results'].items():
        print("{id} {phone:<5} {both:<5} {initial:%Y/%m/%d}  {final:%Y/%m/%d}".format(
                id=_id,
                phone=results['results']['phone'],
                both=results['results']['both'],
                initial=results['date']['initial'],
                final=results['date']['final'],
            )
        )

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

    parser_run.add_argument('--ngrams', '-n', help='Amount of n-grams to separate query',
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
    parser_term.set_defaults(func=term)

    # Ensure a subparser is selected
    if not len(sys.argv) - 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

def main():
    args = command_line()
    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
