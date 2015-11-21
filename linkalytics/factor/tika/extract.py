# -*- coding: utf-8 -*-
import requests
import json

from urllib.parse import urlparse

__all__ = 'common_crawl', 'filter_docs', 'get_domain'

def get_domain(url):
    """
    :params url: str
        Input url string, which can be a fully qualified domain

    :returns: parsed domain url
    :rtype  : list
    """
    parsed = urlparse(url).netloc.split('.')

    if 'www' in parsed:
        parsed.remove('www')

    return parsed

def common_crawl(url):
    """
    Takes an input url and returns a list of site urls crawled from common crawl.

    :param url: str
        Input url which can be a domain name or a fully qualified url.

    :return: docs
    :rtype:  list
    """
    domain = '.'.join(reversed(get_domain(url)))
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
