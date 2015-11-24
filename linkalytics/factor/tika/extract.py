# -*- coding: utf-8 -*-
import requests
import json

from urllib.parse import urlparse
from operator     import methodcaller

__all__ = 'common_crawl', 'filter_docs', 'get_domain'

def get_domain(url):
    """
    :params url: str
        Input url string, which can be a fully qualified domain

    :returns: parsed domain url
    :rtype  : str
    """
    parsed = urlparse(url)

    if not parsed.scheme:
        return get_domain('http://' + url)

    domain = parsed.netloc.split('.')

    if 'www' in domain:
        domain.remove('www')

    return '.'.join(domain)

def common_crawl(url):
    """
    Takes an input url and returns a list of site urls crawled from common crawl.

    :param url: str
        Input url which can be a domain name or a fully qualified url.

    :return: docs
    :rtype:  list
    """
    decoder, getter = methodcaller('decode', 'utf-8'), methodcaller('get', 'url')

    domain = '.'.join(reversed(get_domain(url).split('.')))
    resp   = requests.get('http://urlsearch.commoncrawl.org/download?q={domain}'.format(domain=domain))

    return list(map(getter, map(json.loads, map(decoder, resp.iter_lines()))))

def filter_docs(docs, url=None):
    """
    Filters out downloadable content from a group of urls.

    :param docs: list
    :param url:  str

    :return: documents
    :rtype:  list
    """
    documents = []
    filetypes = 'pdf', 'doc', 'xls', 'ppt', 'odp', 'ods', 'docx', 'xlsx', 'pptx'
    for doc in docs:
        if any(doc.lower().endswith(types) for types in filetypes):
            domain = get_domain(doc)
            if not url or url in domain:
                documents.append(doc)
    return documents