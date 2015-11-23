# -*- coding: utf-8 -*-

import requests
import tempfile
import shutil
import redis
import json
import os

from urllib.request        import urlretrieve, url2pathname
from multiprocessing.dummy import Pool as ThreadPool

from ... environment import cfg
from .   extract     import common_crawl, filter_docs, get_domain

tika_host,  tika_port  = cfg['tika']['host'],  cfg['tika']['port']

__all__ = 'extract_metadata', 'get_metadata', 'run', 'redis_key', 'json_deserializer'

r = redis.Redis(host=cfg['redis']['host'])

def json_deserializer(b):
    """
    :param b: bytes
        Bytes of unencoded strings

    :return: output
        Encoded as UTF-8
    :rtype:  str
    """
    return json.loads(b.decode('utf-8'))

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
    """
    Manually goes to URL endpoint, and downloads file to temporary directory.
    Then tries to extract the metadata from a Tika Server.

    :param url: str
        Fully qualified url endpoint leading to a file

    :return: filename, None or filename, metadata
    :rtype: tuple
    """
    tempdir, metadata = tempfile.mkdtemp(), None

    filename = url.split('/')[-1]
    filepath = os.sep.join([tempdir, filename])
    try:
        urlretrieve(url, filename=filepath)
        metadata = extract_metadata(filepath, host=tika_host, port=tika_port)
    except:
        return filename, None
    finally:
        shutil.rmtree(tempdir)

    return filename, metadata

def redis_load(url, redis_instance):
    """
    :param url:
        A fully qualified url to a document
    :param redis_instance: Redis<Instance>
        A redis client instance

    :return: redis_value
        Serialized values retried from redis
    :rtype:  dict
    """
    redis_value = redis_instance.get(url)

    if not redis_value:
        key, meta = get_metadata(url)
        if meta:
            redis_instance.set(url, json.dumps(meta))
        else:
            redis_instance.set(url, json.dumps(None))

        redis_value = redis_instance.get(url)

    return (url, json_deserializer(redis_value)) if redis_value else (url, {})

def redis_docs(url, redis_instance):
    """
    A proxy which queries a redis instance for a cached copy of document urls.
    If docs do not exist, dispatches to common-crawl to retrieve the list of documents.

    :param url: str
        URL to a particular domain.
    :param redis_instance: <Redis>
        A redis client instance

    :return: docs
        List of document URL's
    :rtype:  list
    """
    key = 'crawl:{domain}'.format(domain='.'.join(get_domain(url)))
    if redis_instance.llen(key):
        docs = [i.decode('utf-8') for i in redis_instance.lrange(key, 0, redis_instance.llen(key))]
    else:
        docs = filter_docs(common_crawl(url))
        redis_instance.lpush(key, *docs)
    return docs


def run(node):
    """
    Primary entry-point for running this module.

    :param node: dict
    {
        "url": "https://some-site.com"
    }

    :return:
    {
        document_url: metadata,
        ...
    }
    :rtype:  dict
    """
    mapper    = lambda x: redis_load(x, r)
    url       = node.get('url', 'https://google.com')
    pool      = ThreadPool(32)
    docs      = redis_docs(url, r)
    metadata  = pool.map(mapper, docs)
    return {
        url2pathname(k): v
            for k,v in metadata if v
    }
