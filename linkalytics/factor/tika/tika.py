# -*- coding: utf-8 -*-

import requests
import tempfile
import shutil
import os

from urllib.request        import urlretrieve
from multiprocessing.dummy import Pool as ThreadPool

from ... environment import cfg
from .   extract     import common_crawl, filter_docs

host, port = cfg['tika']['host'], cfg['tika']['port']

__all__ = 'extract_metadata', 'get_metadata', 'run'

def extract_metadata(document, host='localhost', port=9998):
    tika_url = 'http://{host}:{port}/meta'.format(host=host, port=port)
    headers  = {
        'Accept': 'application/json'
    }
    if not os.path.isfile(document):
        return None

    with open(document, 'rb') as doc:
        metadata = requests.put(tika_url, headers=headers, data=doc)

    if not metadata.ok:
        return None

    return metadata.json()

def get_metadata(url):
    metadata, tempdir = None,  tempfile.mkdtemp()

    filename = url.split('/')[-1]
    filepath = os.sep.join([tempdir, filename])
    try:
        urlretrieve(url, filename=filepath)
        metadata = extract_metadata(filepath, host=host, port=port)
    except:
        return None
    finally:
        shutil.rmtree(tempdir)

    return filename, metadata

def run(node):
    url       = node.get('url', 'https://google.com')
    pool      = ThreadPool(32)
    docs      = filter_docs(common_crawl(url))
    metadata  = pool.map(get_metadata, docs)
    print(metadata)
    return {
        meta[0]: meta[1] for meta in metadata if meta
    }