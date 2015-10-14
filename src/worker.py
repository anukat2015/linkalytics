import json
import concurrent.futures
import argparse
import logging

from .environment import cfg
from .task_mux import TaskMux
from . import instagrammer
from . import phonenumber
from . import twitter
from . import geocoder
from . import youtube

mux = TaskMux(host=cfg['disque']['host'])
RUNNERS = {
    'instagram': instagrammer.run,
    'phone': phonenumber.run,
    'twitter': twitter.run,
    'geocode': geocoder.run,
    'youtube': youtube.run
}

logging.getLogger('').setLevel(logging.DEBUG)

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
    parser = argparse.ArgumentParser(description="Do work from queue.")
    parser.add_argument('queues', nargs='+')

    args = parser.parse_args()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = executor.map(handle, args.queues)
        concurrent.futures.wait(futures)
