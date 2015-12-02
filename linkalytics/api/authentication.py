from flask.ext.httpauth import HTTPBasicAuth

from . error import  unauthorized

from .  import api
from .. environment import cfg

auth = HTTPBasicAuth()

@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')

@api.before_request
@auth.login_required
def before_request():
    pass

@auth.get_password
def get_pw(username):
    if username in cfg['api']['username']:
        return cfg['api'].get('password')
    return None