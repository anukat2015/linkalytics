from utils import with_test

from . twitter import run

@with_test(run, 'twitter')
def data():
    yield (
        {
            "text": "twitter.com/realDonaldTrump",
        }, [
            {
                "id": "realdonaldtrump",
                "name": "Donald J. Trump",
            }
        ]
    )
