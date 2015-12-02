from flask import jsonify, request

from . import api

from .. tasks       import TaskMux
from .. environment import cfg

version = cfg['api']['version']

# Instantiate Task Multiplexer
mux = TaskMux(host=cfg["disque"]["host"])

@api.route('/{version}/<path:endpoint>'.format(version=version), methods=['POST'])
def run_api(endpoint):
    """
    Main Entrypoint to the API

    :param endpoint: API Endpoint URL

    :return: JSON Response
    :rtype : str
    """
    record  = request.get_json()
    jobid   = mux.put(endpoint, record)
    results = mux.retrieve(jobid)

    return jsonify(**results)

@api.after_request
def access_control(response):
    """
    Enables Access-Control headers in a request
    To allow cross origin POST requests to the server
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST')

    return response
