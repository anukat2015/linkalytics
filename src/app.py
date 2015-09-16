import rq
import redis
import time
from . import twitter
from . import youtube

def main():
    q1 = rq.Queue('twitter', connection=redis.Redis())
    q2 = rq.Queue('youtube', connection=redis.Redis())

    job1 = q1.enqueue(twitter.run, {"text": "twitter.com/realDonalTrump"})
    job2 = q2.enqueue(youtube.run, {"text": "https://www.youtube.com/watch?t=3&v=ToyoBTiwZ6c"})

    while True:
        time.sleep(1)
        print("twitter", job1.result)
        print("youtube", job2.result)
