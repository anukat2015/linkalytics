import json
import logging

from   concurrent.futures import ThreadPoolExecutor, wait

from . tasks import create_mux

from . import search

from . enhance import youtube, twitter, geocoder, instagrammer, phonenumber
from . environment import cfg
from . factor import ngrams, lsh, imgmeta, tika
from . factor.constructor import merge, initialize, available, status, recursor, assertion
from . factor_validator import coincidence

# Endpoint: Function Runner
RUNNERS = {
    'ngrams'             : ngrams.run,
    'lsh'                : lsh.run,
    'imgmeta'            : imgmeta.run,
    'search'             : search.run,
    'enhance/instagram'  : instagrammer.run,
    'enhance/geocoder'   : geocoder.run,
    'enhance/phone'      : phonenumber.run,
    'enhance/twitter'    : twitter.run,
    'enhance/youtube'    : youtube.run,
    'factor/initialize'  : initialize.run,
    'factor/merge'       : merge.run,
    'factor/assertion'   : assertion.run,
    'factor/status'      : status.run,
    'factor/recursor'    : recursor.run,
    'factor/available'   : available.run,
    'coincidence'        : coincidence.run,
    'metadata'           : tika.run,
    'metadata/keys'      : tika.metadata_keys,
    'metadata/values'    : tika.metadata_values,
}

logger = logging.getLogger('')
logger.setLevel(logging.INFO)

def apply(func, job):
    return func(job)

def process_record(q):
    """
    Run by worker instances

    NOTE: mux.get()
        Will block until a job has been placed
        on the work queue of the name q

    :param q: str
        Queue Name
    """
    mux = create_mux(cfg)

    qname, jobid, job = mux.get(q)
    try:
        result = apply(RUNNERS[q], job)
    except Exception as e:
        result = mux.report_exception(jobid)
        raise e
    finally:
        mux.conn.addjob(jobid, json.dumps(result))

    mux.conn.fastack(jobid)

def handle(q):
    print("Listening on '{queue}'".format(queue=q))
    while True:
        process_record(q)

def main():
    """
    Run a thread pool to handle where one thread handles one work queue.
    """
    # Have 4 Listeners one each queue
    max_workers = len(RUNNERS) * 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        wait(executor.map(handle, RUNNERS))
