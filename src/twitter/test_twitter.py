import nose
from .. utils import with_test
from . twitter import run

@with_test(run, 'twitter')
def data():
    yield ({"text": "twitter.com/realDonalTrump"}, [
            {"id": "realdonaltrump", "name": "RealDonalTrump"}
        ])
