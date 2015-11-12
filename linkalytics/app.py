"""
Investigative Case Management without Pre-Processing
====================================================

For testing, in a second terminal window, type

    curl -H "Content-type: application/json" \
         -d '{"search":[search_term]}' \
         -X POST http://127.0.0.1:5000/search

where you choose the search_term.
"""

from flask import Flask, jsonify, request

from flask.ext.cors      import CORS
from flask.ext.basicauth import BasicAuth
from flask.ext.restful   import Api

from . import ngrams
from . import lsh
from . import coincidence
from . import search
from . import imgmeta

from . environment import cfg
from . tasks       import TaskMux

app = Flask(__name__)

# By default this sets CORS access to resource endpoints to `*`
app.config['BASIC_AUTH_USERNAME'] = cfg['api']['username']
app.config['BASIC_AUTH_PASSWORD'] = cfg['api']['password']

cors       = CORS(app)
api        = Api(app)
basic_auth = BasicAuth(app)

version = cfg['api']['version']

mux = TaskMux(host=cfg["disque"]["host"])

@app.route("/{version}/search".format(version=version), methods=['POST'])
@basic_auth.required
def run_search():
    """
    Here's a server that takes a search term as an input
    and provides a list of grouped documents as an output
    """
    record = request.get_json()
    search_term, size = record.get('search', 'cali'), int(record.get('size', 100))

    results = search.get_results(search_term, size)

    return jsonify(**results)


@app.route('/{version}/ngrams'.format(version=version), methods=['POST'])
@basic_auth.required
def run_ngrams():
    record  = request.get_json()
    results = ngrams.run(record)
    return jsonify(**results)


@app.route('/{version}/lsh'.format(version=version), methods=['POST'])
@basic_auth.required
def run_lsh():
    record  = request.get_json()
    results = lsh.run(record)
    return jsonify(**results)


@app.route('/{version}/coincidence'.format(version=version), methods=['POST'])
@basic_auth.required
def run_coincidence():
    record  = request.get_json()
    results = coincidence.run(record)
    return jsonify(**results)

@app.route('/{version}/imgmeta'.format(version=version), methods=['POST'])
@basic_auth.required
def run_imgmeta():
    record  = request.get_json()
    results = imgmeta.run(record)
    return jsonify(**results)


@app.route('/{version}/enhance/<path:endpoint>'.format(version=version), methods=['POST'])
@basic_auth.required
def enhance(endpoint):
    record = request.get_json()

    if endpoint not in set(cfg["queues"]["endpoints"]):
        return jsonify(results={"message": "endpoint not found"}, endpoint=endpoint, **record), 404

    jobid   = mux.put(endpoint, record)
    results = mux.retrieve(jobid)

    return jsonify(results=results, endpoint=endpoint, **record)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response
