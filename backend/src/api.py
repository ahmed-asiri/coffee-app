import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
https://ahemd.us.auth0.com/authorize?audience=coffee&response_type=token&client_id=CoUmz5x4TOR1FzVEWzP5lYbBFkpULawo&redirect_uri=http://localhost:4200/tabs/user-page
'''

db_drop_and_create_all()


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Authorization,'+
    ' Content-Type, true'
    header['Access-Control-Allow-Methods'] = 'POST,GET,PUT,'
    +'DELETE,PATCH,OPTIONS'
    return response


# ROUTES


@app.route("/drinks")
def get_drinks():
    drinks = Drink.query.all()

    drinks_list = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drinks_list
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details(token):
        drinks = Drink.query.all()
        result = {
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        }
        return jsonify(result)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(jwt):
    request_data = request.get_json()
    if 'title' and 'recipe' not in request_data:
        abort(400)

    drink_title = request_data['title']
    drink_recipe = json.dumps([request_data['recipe']])
    drink = Drink(title=drink_title, recipe=drink_recipe)

    try:
        drink.insert()
    except:
        abort(500)

    return jsonify({
        "success": True,
        "drinks": drink.long()
        }), 200


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def modify_drink(jwt, id):
    request_data = request.get_json()

    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    try:
        if 'title' in request_data:
            drink.title = request_data['title']
        if 'recipe' in request_data:
            drink.recipe = json.dumps(request_data['recipe'])
        drink.update()
    except:
        abort(500)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    drink.delete()
    return jsonify({
        'success': True,
        'deleted': id
    })

# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "bad request"
                    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
                    "success": False,
                    "error": 500,
                    "message": "internal server error"
                    }), 500


@app.errorhandler(403)
def forbiden(error):
    return jsonify({
                    "success": False,
                    "error": 403,
                    "message": "forbidden"
                    }), 403


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
                    "success": False,
                    "error": 401,
                    "message": "unauthorized"
                    }), 401
