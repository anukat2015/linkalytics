from __future__ import print_function

import sys

from elasticsearch  import Elasticsearch
from logging        import CRITICAL

from .. utils       import SetLogging
from .. utils       import timer
from .. environment import cfg
from .  entropy     import search
from .  entropy     import TermDocumentMatrix

if __name__ == '__main__':

    with SetLogging(CRITICAL):

        url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
        es  = Elasticsearch(url, port=443, verify_certs=False, use_ssl=False)

        results = search(sys.argv[2], 1000, es, True)
        tdm     = TermDocumentMatrix()

        with timer('Adding Docs to TDM takes'):
            tdm.load_dict(results, int(sys.argv[1]))

        with timer('Writing TDM takes'):
            tdm.write_csv('output.csv')

    print(tdm.sum_columns(), file=sys.stderr)
