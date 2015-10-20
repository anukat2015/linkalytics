import sys

from elasticsearch import Elasticsearch

from ..environment import cfg
from .entropy import main

if __name__ == '__main__':
    url = cfg["cdr_elastic_search"]["hosts"] + cfg["cdr_elastic_search"]["index"]
    es  = Elasticsearch(url, port=443, use_ssl=False, verify_certs=False)

    main(int(sys.argv[1]), sys.argv[2], es)
