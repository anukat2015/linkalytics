import rq
import redis
import time
import concurrent.futures
import itertools
import json
import elasticsearch as es
import elasticsearch.helpers as eshelp
import warnings

from . environment import cfg

from . import twitter
from . import youtube
from . import phonenumber
from . import instagrammer

queues = {
    'twitter'   : rq.Queue('twitter', connection=redis.Redis()),
    'youtube'   : rq.Queue('youtube', connection=redis.Redis()),
    'phone'     : rq.Queue('phone', connection=redis.Redis()),
    'instagram' : rq.Queue('instagram', connection=redis.Redis())
}

def process_record(record):
    print('got job {}'.format(record['_source']['id']))
    record = record['_source']
    runners = [
        (queues['twitter'], twitter.run),
        (queues['youtube'], youtube.run),
        (queues['phone'], phonenumber.run),
        (queues['instagram'], instagrammer.run)
    ]
    jobs = (q.enqueue(f, record).id for q,f in runners)
    results = list(map(get_result, jobs))
    return json.dumps(results, indent=2, separators=(',', ':'))

def get_result(job_id):
    job = q1.fetch_job(job_id)  # apparently this works...
    while job.is_started or job.is_queued:
        time.sleep(1)

    if job.result:
        return (job.id, job.status, job.result)
    else:
        return (job.id, job.status, None)

def main():
    es_instance = cfg['cdr_elastic_search']['hosts']
    client = es.Elasticsearch([es_instance], timeout=60, retry_on_timeout=True)

    # j1 = q1.enqueue(twitter.run, {"text": "twitter.com/realDonaldTrump"})
    # j2 = q1.enqueue(twitter.run, {"text": "here's nassim taleb's twitter.....@nntaleb"})
    # j3 = q2.enqueue(youtube.run, {"text": "Have you seen this https://www.youtube.com/watch?t=3&v=ToyoBTiwZ6c youtube video with Super Marioll"})
    # j4 = q3.enqueue(phonenumber.run, {"text": "1800295 408-291-2521"})
    #
    # jobs = [j1.id, j2.id, j3.id, j4.id]
    query = {
        "query": {
            "match": {
                "_all": "instagram"
            }
        }
    }
    all_ads = eshelp.scan(client, index=cfg['cdr_elastic_search']['index'], doc_type="ad", scroll='30m', query=query)
    limited_ads = itertools.islice(all_ads, 1000)

    executor = concurrent.futures.ProcessPoolExecutor(max_workers=8)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for i, result in enumerate(executor.map(process_record, limited_ads)):
            print(i, result)
