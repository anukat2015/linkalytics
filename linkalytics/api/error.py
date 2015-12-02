from flask import jsonify

def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response

def page_not_found(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response
