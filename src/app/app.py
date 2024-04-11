import json

from flask import request, redirect, render_template, flash, url_for, request

from . import create_app, database
from .models import Users


# from flask import Flask
# from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm #, DataRequired, Length
from wtforms import StringField, SubmitField, PasswordField, EmailField
from werkzeug.security import generate_password_hash
import os

app = create_app()
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")


@app.route('/', methods=['GET'])
def fetch(_json=False):
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
    if _json==True:
        return all_users
    else:
        return json.dumps(all_users), 200

@app.route('/index', methods=['GET'])
def index():
    usuarios = fetch(_json=True)
    return render_template('index.html',  usuarios=usuarios)

@app.route('/editar', methods=['GET'])
def editar():
    return render_template('index.html')

@app.route('/excluir', methods=['GET'])
def excluir():
    return render_template('index.html')

# Registration form
class RegistrationForm(FlaskForm):
    name = StringField('Nome de Usuário:') #, validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email:') #, validators=[DataRequired(), EmailField()])
    password = PasswordField('Senha:') #, validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Cadastrar')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)        
        add({'name':form.name.data, 'email':form.email.data, 'password':hashed_password})
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('index'))  # Change to desired route after successful registration
    return render_template('cadastrar.html', form=form)


@app.route('/add', methods=['POST'])
def add(_data=None):
    data = request.get_json() if _data==None else _data
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
