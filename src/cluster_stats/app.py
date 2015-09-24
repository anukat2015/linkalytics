from flask import Flask, request
from elasticsearch import Elasticsearch
import reverse_geocoder as rg
import json
from collections import Counter
import numpy as np
from itertools import tee, izip
from geopy.distance import vincenty
import datetime
from environment import cfg

app = Flask(__name__)


def price_quantile(cdfs, city, price):
    temp = filter(lambda x: x['city'] == city, cdfs)
    df = temp[0]['data']
    df['key'] = df['key'].astype(float)

    df = df.sort('key')
    df = df.reset_index(drop=True)
    return df[df['key'] >= price]['quantile'].iloc[0]


def window(iterable, size):
    iters = tee(iterable, size)
    for i in xrange(1, size):
        for each in iters[i:]:
            next(each, None)
    return izip(*iters)


@app.route('/cluster_analyze', methods=['POST'])
def analyze_clusters():
    clusters = json.loads(request.data)['ids']
    q = {
        "size": 2000,
        "query": {
            "terms": {
                "_id": clusters
            }
        },
        "aggregations": {
            "forces": {
                "terms": {"field": "city"},
                "aggregations": {
                    "prices": {
                        "terms": {"field": "rate60"}
                    }
                }
            }
        }
    }

    es = Elasticsearch(cfg.CDR_ELASTIC.URL)
    res = es.search(body=q, index=cfg.CDR_ELASTIC.INDEX, doc_type='ad')
    geo = filter(lambda x: 'latitude' in x['_source'].keys(), res['hits']['hits'])
    geopts = map(lambda x: (float(x['_source']['latitude']), float(x['_source']['longitude'])), geo)
    ethnicity = filter(lambda x: 'ethnicity' in x['_source'].keys(), res['hits']['hits'])
    ethnicity = map(lambda x: str(x['_source']['ethnicity']), ethnicity)
    city = filter(lambda x: 'city' in x['_source'].keys(), res['hits']['hits'])
    city = map(lambda x: str(x['_source']['city'].encode('ascii', 'ignore')), city)
    ethnicity_all = dict(Counter(ethnicity))
    prices = filter(lambda x: 'rate60' in x['_source'].keys() and 'city' in x['_source'].keys(), res['hits']['hits'])
    prices = filter(lambda x: x['_source']['rate60'] != '', prices)
    time = filter(lambda x: 'posttime' in x['_source'].keys(), geo)
    time_dist = map(lambda x: (x['_source']['latitude'], x['_source']['longitude'], datetime.datetime.strptime(x['_source']['posttime'], "%Y-%m-%dT%H:%M:%S").date()), time)

    imps = []  # implied travel speed
    imps2 = []  # average distance between multiple posts at exact timestamp
    total_ts = sorted(time_dist, key=lambda item: item[2])

    for item in window(total_ts, 2):
        dist = vincenty((item[0][0], item[0][1]), (item[1][0], item[1][1])).miles
        time = abs(item[1][2]-item[0][2]).total_seconds()/(24*3600.00)
        if dist != 0 and time == 0:
                imps2.append(dist)
        elif dist != 0 and time != 0:
                imps.append(time)
        else:
                pass

    total_time = abs(total_ts[-1][2]-total_ts[0][2]).total_seconds()/(24*3600.00)
    avg_post_week = len(total_ts)/(total_time/7.0)
    if len(ethnicity_all) > 1:
        eth = "More than one"
    else:
        eth = "One"

    if geopts:
        results = rg.search(geopts)  # default mode = 2
        countries = set(map(lambda x: x['cc'], results))
        states = set(map(lambda x: x['admin1'], results))
        cities = set(map(lambda x: x['name'], results))
        if len(countries) > 1:
            location = "International"
        elif len(countries) == 1 and len(states) > 1:
            location = "National"
        else:
            location = "Local"
    else:
        location = "No information"

    q2 = {
        "size": 2000,
        "query": {
            "terms": {
                "city": list(set(city))
            }
        },
        "aggregations": {
            "forces": {
                "terms": {"field": "city"},
                "aggregations": {
                    "prices": {
                        "terms": {"field": "rate60"}
                    }
                }
            }
        }
    }

    pq = []
    raw = []
    for item in map(lambda x: (x['_source']['city'], x['_source']['rate60']), prices):
        try:
            raw.append(float(item[1]))
        except:
            pass

    return json.dumps({'avg_price_quantile': np.mean(pq), 'loc': location, 'ethnicity': eth, 'price_var': np.std(raw), 'mean_price': np.mean(raw), 'implied_travel_time': np.mean(imps), 'total_time': total_time, 'max_dist_sim_posts': np.max(imps2), 'no_cites': len(cities), 'avg_post_week': avg_post_week})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
