from ... utils import with_test
from . geocoder import run

@with_test(run, 'city')
def data():
    yield (
        {'city': ['Portland, MA', 'Portland, OR']}, [
        {'latitude': 42.077535,
           'longitude': -72.654684,
           'name': 'Portland, MA'},
          {'latitude': 45.5230622, 'longitude': -122.6764816, 'name': 'Portland, OR'}
    ])
