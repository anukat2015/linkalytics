import rq
import redis
import time
from . import twitter
from . import youtube
from . import phonenumber


def main():
    q1 = rq.Queue('twitter', connection=redis.Redis())
    q2 = rq.Queue('youtube', connection=redis.Redis())
    q3 = rq.Queue('phone', connection=redis.Redis())

    job1 = q1.enqueue(twitter.run, {"text": "twitter.com/realDonaldTrump"})
    job2 = q1.enqueue(twitter.run, {"text": "Here's Nassim Taleb's twitter.....@nntaleb"})
    job3 = q2.enqueue(youtube.run, {"text": "Have you seen this https://www.youtube.com/watch?t=3&v=ToyoBTiwZ6c youtube video with Super Marioll"})
    job4 = q3.enqueue(phonenumber.run, {"text": "1800295 408-291-2521"})

    while True:
        time.sleep(1)
        print("Test Twitter Link", job1.result)
        print("Test Twitter Blob", job2.result)
        print("Test Youtube Blob", job3.result)
        print("phone", job4.result)
