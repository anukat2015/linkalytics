import functools

from geopy.geocoders import GoogleV3

from utils import memoize

@memoize
def get_lat_long(geocoder, query):
    """
    Get's the latitude and longitude using geopy geocoder

    Input
    =====
    geocoder: <geopy.geocoders>
        geopy geocoder instance

    query: str
        Query string
    """
    location = geocoder.geocode(query)

    return location.latitude, location.longitude


google = GoogleV3()

lat_long = functools.partial(get_lat_long, google)

def run(node):
    coordinates = [(i, lat_long(i)) for i in node['city']]
    return {
        'city': [
            {"name": k, "latitude": v[0], "longitude": v[1] } for k, v in coordinates
        ]
    }
