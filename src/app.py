import rq
import redis
import time
from . import twitter

def main():
    q = rq.Queue('twitter', connection=redis.Redis())

    job = q.enqueue(twitter.run, {"text": "twitter.com/realDonalTrump"})

    while True:
        time.sleep(1)
        print(job.result)
