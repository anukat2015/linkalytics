import sys

from elasticsearch import Elasticsearch

from .. environment import cfg
from .. utils import timer
from .  entropy import main

if __name__ == '__main__':
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    es  = Elasticsearch(url, port=443, use_ssl=False, verify_certs=False)

    with timer('Adding Docs to TDM takes'):
        tdm = main(int(sys.argv[1]), sys.argv[2], es)

    print(tdm.to_df())

    with timer('Writing TDM takes'):
        tdm.write_csv('output.csv')
