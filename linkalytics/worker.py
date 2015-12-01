import json
import logging
from concurrent.futures import ThreadPoolExecutor, wait

from . factor.constructor import merge, constructor
from . factor_validator   import coincidence

from . enhance     import youtube, twitter, geocoder, instagrammer, phonenumber
from . environment import cfg
from . factor      import ngrams, lsh, imgmeta
from . tasks       import TaskMux

from . import search

mux = TaskMux(host=cfg['disque']['host'])

RUNNERS = {
    'ngrams'             : ngrams.run,
    'lsh'                : lsh.run,
    'coincidence'        : coincidence.run,
    'imgmeta'            : imgmeta.run,
    'search'             : search.run,
    'enhance/instagram'  : instagrammer.run,
    'enhance/phone'      : phonenumber.run,
    'enhance/twitter'    : twitter.run,
    'enhance/geocode'    : geocoder.run,
    'enhance/youtube'    : youtube.run,
    'factor/constructor' : constructor.run,
    'factor/merge'       : merge.run,
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
