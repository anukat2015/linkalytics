from flask import jsonify, request

from . import api

from .  error       import page_not_found
from .. tasks       import create_mux
from .. environment import cfg
from .. worker      import RUNNERS

version = cfg['api']['version']

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
    mux     = create_mux(cfg)
    jobid   = mux.put(endpoint, record)
    results = mux.retrieve(jobid)

    return jsonify(**results)

