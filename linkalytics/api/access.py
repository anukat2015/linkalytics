from . import api

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
