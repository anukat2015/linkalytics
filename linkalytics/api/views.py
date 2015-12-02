from flask import jsonify, request

from . import api

from . error        import page_not_found
from .. tasks       import TaskMux
from .. environment import cfg
from .. worker      import RUNNERS

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
    if endpoint not in RUNNERS:
        return page_not_found('Endpoint `{}` does not exist'.format(endpoint))

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

@api.after_request
def set_content_type(response):
    response.headers['Content-Type'] = 'application/json'
    return response
