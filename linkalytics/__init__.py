"""
Investigative Case Management without Pre-Processing
====================================================

For testing, in a second terminal window, type

    curl -H "Content-type: application/json" \
         -d '{"search":[search_term]}' \
         -X POST http://127.0.0.1:5000/search

where you choose the search_term.
"""

from .__version__ import __version__
from .__version__ import __build__

__title__     = 'linkalytics'
__license__   = 'Apache Software License Version 2.0'

from flask import Flask

from flask.ext.cors      import CORS
from flask.ext.restful   import Api

def create_app(cfg):
    """
    Application factory function

    :param cfg: dict
        Configuration parameters

    :return: app
    """
    app = Flask(__name__)

    from . api import api

    app.register_blueprint(api)

    # By default this sets CORS access to resource endpoints to `*`
    app.config['BASIC_AUTH_USERNAME'] = cfg['api']['username']
    app.config['BASIC_AUTH_PASSWORD'] = cfg['api']['password']

    # Enable CORS Configuration and Basic Authentication
    cors       = CORS(app)
    api        = Api(app)

    return app

