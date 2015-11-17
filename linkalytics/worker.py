import json
import logging

from concurrent.futures import ThreadPoolExecutor, wait

from . enhance import youtube, twitter, geocoder, instagrammer, phonenumber
from . factor  import ngrams, lsh, imgmeta

from . environment import cfg
from . tasks       import TaskMux

from . import search

from . factor_validator import coincidence

mux = TaskMux(host=cfg['disque']['host'])

RUNNERS = {
    'instagram'  : instagrammer.run,
    'phone'      : phonenumber.run,
    'twitter'    : twitter.run,
    'geocode'    : geocoder.run,
    'youtube'    : youtube.run,
    'ngrams'     : ngrams.run,
    'lsh'        : lsh.run,
    'coincidence': coincidence.run,
    'imgmeta'    : imgmeta.run,
    'search'     : search.run
}

logging.getLogger('').setLevel(logging.INFO)

def process_record(q):
    qname, jobid, job = mux.get(q)
    try:
        result = RUNNERS[q](job)
    except Exception as e:
        result = mux.report_exception(jobid)
        raise e
    finally:
        mux.conn.addjob(jobid, json.dumps(result))

    mux.conn.fastack(jobid)

def handle(q):
    print("Listening on '{}'".format(q))
    while True:
        process_record(q)

def main():
    """
    Run a thread pool to handle where one thread handles one work queue.
    """
    with ThreadPoolExecutor(max_workers=len(RUNNERS)) as executor:
        futures = executor.map(handle, RUNNERS)
        wait(futures)
