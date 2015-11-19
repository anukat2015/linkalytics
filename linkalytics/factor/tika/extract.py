# -*- coding: utf-8 -*-
import requests
import json

from urllib.parse import urlparse

__all__ = 'common_crawl', 'filter_docs'

def common_crawl(url):
    """
    Takes an input url and returns a list of site urls crawled from common crawl.

    :param url: str
        Input url which can be a domain name or a fully qualified url.

    :return: docs
    :rtype:  list
    """
    parse = list(reversed(urlparse(url).netloc.split('.')))
    if 'www' in parse:
        parse.remove('www')

    domain = '.'.join(parse)
    resp   = requests.get('http://urlsearch.commoncrawl.org/download?q={domain}'.format(domain=domain))

    return [json.loads(i.decode('utf-8')).get('url') for i in resp.iter_lines()]

def filter_docs(docs):
    """
    Filters out downloadable content from a group of urls.

    :param docs: list

    :return: documents
    :rtype:  list
    """
    filetypes = 'pdf', 'doc', 'xls', 'ppt', 'odp', 'ods', 'docx', 'xlsx', 'pptx'
    documents = [
        doc for doc in docs
            if any(doc.lower().endswith(types) for types in filetypes)
    ]
    return documents
