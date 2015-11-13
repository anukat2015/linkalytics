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

@app.route('/{version}/<path:endpoint>'.format(version=version), methods=['POST'])
@basic_auth.required
def run_api(endpoint):
    record  = request.get_json()
    jobid   = mux.put(endpoint, record)
    results = mux.retrieve(jobid)
    return jsonify(endpoint=endpoint, **results)


@app.route('/{version}/enhance/<path:endpoint>'.format(version=version), methods=['POST'])
@basic_auth.required
def enhance(endpoint):
    record = request.get_json()
    jobid   = mux.put(endpoint, record)
    results = mux.retrieve(jobid)
    return jsonify(results=results, endpoint=endpoint, **record)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response