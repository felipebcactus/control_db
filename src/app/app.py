import json

from flask import request

from . import create_app, database
from .models import Users

app = create_app()


@app.route('/', methods=['GET'])
def fetch():
    users = database.get_all(Users)
    all_users = []
    for user in users:
        new_user = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": user.password
        }

        all_users.append(new_user)
    return json.dumps(all_users), 200


@app.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']

    database.add_instance(Users, name=name, email=email, password=password)
    return json.dumps("Added"), 200


@app.route('/remove/<user_id>', methods=['DELETE'])
def remove(user_id):
    database.delete_instance(Users, id=user_id)
    return json.dumps("Deleted"), 200


@app.route('/edit/<user_id>', methods=['PATCH'])
def edit(user_id):
    data = request.get_json()
    new_email = data['email']
    database.edit_instance(Users, id=user_id, email=new_email)
    return json.dumps("Edited"), 200
