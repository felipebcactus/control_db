from flask import request, redirect, render_template, flash, url_for, request
from . import create_app, database
from .models import Users, Hosts, Databases, Tables, Sessions, SessionsHosts, ExternalConnectionByHostId, db_name_ignore_per_type, host_types, user_types, user_status, session_status_type
from flask_wtf import FlaskForm #, DataRequired, Length
from wtforms import StringField, SubmitField, PasswordField, EmailField
from werkzeug.security import generate_password_hash
from sqlalchemy.sql import text
from datetime import datetime
import os
import string
import random
import json


app = create_app()
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

from .synchosts import synchosts_bp
app.register_blueprint(synchosts_bp)

if __name__ == '__main__':
    app.run(debug=True)
    
@app.route('/')
def home():
    return redirect(url_for('index')) 

@app.route('/getUsers', methods=['GET'])
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

@app.route('/<filename>.html')
def render_html_template(filename):
    return render_template(f'{filename}.html')

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


@app.route('/addHost', methods=['POST'])
def addHost():
    data = request.get_json()
    host_object = {}
    for item in data:
        host_object[item['name']] = item['value']
    database.add_instance(Hosts, name=host_object['name'], type=host_object['type'], ipaddress=host_object['ipaddress'], port=host_object['port'], username=host_object['username'], password=host_object['password'])
    return json.dumps(host_object), 200


@app.route('/getHosts', methods=['GET'])
def getHosts(_json=False):
    hosts = database.get_all(Hosts)
    all_hosts = []
    for host in hosts:
        new_host = {
            "id": host.id,
            "name": host.name,
            "type": host_types[host.type],
            "ipaddress": host.ipaddress,
            "port": host.port,
            "username": host.username,
            "password": "*", #host.password,
            "id_user": host.id_user or '',
            "created_at": str(host.created_at),
            "updated_at": str(host.updated_at) or ''
        }

        all_hosts.append(new_host)
    if _json==True:
        return all_hosts
    else:
        return json.dumps(all_hosts), 200


@app.route('/getDatabases', methods=['GET'])
def getDatabases(_json=False):
    databases = database.get_all(Databases)
    all_databases = []
    for _database in databases:
        host = database.get_id(Hosts, _database.id_host)
        host_name = host.name if host else "Unknown host"
        new_database = {
            "id": _database.id,
            "name": _database.name,
            "id_host": _database.id_host,
            "host_name": host_name,
            "type": _database.type,
        }
        all_databases.append(new_database)
    if _json==True:
        return all_databases
    else:
        return json.dumps(all_databases), 200

@app.route('/getTables', methods=['GET'])
def getTables(_json=False):
    tables = database.get_all(Tables)
    all_tables = []
    for table in tables:
        _database = database.get_id(Databases, table.id_database)
        database_name = _database.name if _database else "Unknown database"
        new_table = {
            "id": table.id,
            "name": table.name,
            "id_database": table.id_database,
            "database_name": database_name,
            "type": table.type,
        }
        all_tables.append(new_table)
    if _json==True:
        return all_tables
    else:
        return json.dumps(all_tables), 200


@app.route('/addUser', methods=['POST'])
def addUser():
    data = request.get_json()
    user_obj = {}
    for item in data:
        user_obj[item['name']] = item['value']
    database.add_instance(Users, name=user_obj['name'], type=user_obj['type'], email=user_obj['email'], password=user_obj['password'])
    return json.dumps(user_obj), 200


@app.route('/getUsers/<type>', methods=['GET'])
def getUsers(type,_json=False):
    users = database.get_by(Users, 'type', type)
    all_users = []
    for user in users:
        new_user = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "parent": "",
            "status": user_status[user.status],
            "type": user_types[user.type],
        }
        all_users.append(new_user)
    
    # carrega 0 e 1 juntos se nao for 2 (pq so tem 2 abas system/database)
    if False and type!=2 :
        users = database.get_by(Users, 'type', (1 if type==0 else 0))
        for user in users:
            new_user = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "parent": "",
                "status": user_status[user.status],
                "type": user_types[user.type],
            }
            all_users.append(new_user)
        print(">>>")
        print(all_users)
    if _json==True:
        return all_users
    else:
        return json.dumps(all_users), 200



@app.route('/addSession', methods=['POST'])
def addSession():
    # session_status_type
    data = request.get_json()
    session_obj = {}
    for item in data:
        session_obj[item['name']] = item['value']
        
    database.add_instance(Sessions, user=session_obj['user'], access_start=session_obj['access_start'], access_end=session_obj['access_end'], description=session_obj['description'])
    return json.dumps(session_obj), 200


@app.route('/getSessions', methods=['GET'])
def getSessions(_json=False):
    sessions = database.get_all(Sessions)
    all_sessions = []
    for session in sessions:
        _user = database.get_id(Users, session.user)
        user_name = _user.name if _user else "Unknown user"
        new_session = {
            "id": session.id,
            "user": session.user,
            "user_name": user_name,
            "approver": '', #session.approver,
            "access_start": str(session.access_start) or '',
            "access_end": str(session.access_end) or '',
            "status": session.status,
            "request_date": str(session.request_date) or '',
            "approve_date": str(session.approve_date) or '',
            "description": session.description
        }
        all_sessions.append(new_session)
    if _json==True:
        return all_sessions
    else:
        return json.dumps(all_sessions), 200


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

@app.route('/getHostsDatabasesTablesTree', methods=['GET'])
def getHostsDatabasesTablesTree(_json=False):
    hosts = database.get_all_order_by(Hosts, 'name')
    tree = []
    for host in hosts:
        databases = database.get_all_order_by(Databases, 'name')
        host_dict = {
            "id": str(host.id),
            "text": host.name,
            "children": []
        }
        for _database in databases:
            if _database.id_host == host.id:
                database_dict = {
                    "id": '-'.join((str(host.id),str(_database.id))),
                    "text": _database.name,
                    "children": []
                }
                tables = database.get_all_order_by(Tables, 'name')
                for table in tables:
                    if table.id_database == _database.id:
                        table_dict = {
                            "id": '-'.join((str(host.id),str(_database.id),str(table.id))),
                            "text": table.name
                        }
                        database_dict["children"].append(table_dict)
                host_dict["children"].append(database_dict)
        tree.append(host_dict)
    if _json==True:
        return tree
    else:
        return json.dumps(tree), 200
    
    

def returnPermissionTree(_data):
    permissions_obj_name = {}
    permissions_obj_id = {}
    
    def _getHostName(_id):
        return database.get_id(Hosts, _id).name
    def _getDatabaseName(_id):
        return database.get_id(Databases, _id).name
    def _getTableName(_id):
        return database.get_id(Tables, _id).name
    
    def _addHost(_id):
        _hostname = _getHostName(_id)
        if _hostname not in permissions_obj_name:
            permissions_obj_name[_hostname] = {}
            permissions_obj_id[_id] = {}
    def _addDatabase(_id_host,_id_database):
        _hostname = _getHostName(_id_host)
        _databasename = _getDatabaseName(_id_database)
        if _databasename not in permissions_obj_name[_hostname]:
            permissions_obj_name[_hostname][_databasename] = []
            permissions_obj_id[_id_host][_id_database] = []
    def _addTable(_id_host,_id_database,_id_table):
        _hostname = _getHostName(_id_host)
        _databasename = _getDatabaseName(_id_database)
        _tablename = _getTableName(_id_table)
        if _tablename not in permissions_obj_name[_hostname][_databasename]:
            permissions_obj_name[_hostname][_databasename].append(_tablename)
            permissions_obj_id[_id_host][_id_database].append(_id_table)
    
    for item in _data:
        _parts = item.split('-')
        if len(_parts) == 1:
            # apenas host
            _addHost(_parts[0])
        elif len(_parts) == 2:
            # host + database
            _addDatabase(_parts[0],_parts[1])
        elif len(_parts) == 3:
            # host + database + tables
            _addTable(_parts[0],_parts[1],_parts[2])
        else :            
            print('else ')
            print(_parts)
        
    return { 'permissions_name' : permissions_obj_name , 'permissions_id' : permissions_obj_id }


@app.route('/postHostsDatabasesTablesTree', methods=['POST'])
def postHostsDatabasesTablesTree():
    
    # TODO: pensar em colocar ou controlar por HOST esses usuarios, precisa?
    
    _data = request.get_json()['data']
    
    permissions = returnPermissionTree(_data['datatree'])
    permissions_obj_name = permissions['permissions_name']
    permissions_obj_id = permissions['permissions_id']
    
    username = _data['username']
    session_id = _data['session_id']
    sessionData = database.get_id(Sessions, session_id)
    details={}
    details['host']=[]
    details['permissions']=permissions_obj_name
    
    def _getHostData(_id):
        return database.get_id(Hosts, _id)
    def _getDatabaseData(_id):
        return database.get_id(Databases, _id)
    
    
    results = []
    if len(permissions_obj_id)>0 :
        for _host_id in permissions_obj_id :
            hostData = _getHostData(_host_id)
            
            # create relationship for future remove
            results.append({'removingOldSessionHost': session_id+'-'+_host_id})
            removeUserFromHostBySession({'session_id': session_id, 'user_name': username})    
            results.append({'addSessionHost': session_id+'-'+_host_id})
            database.add_instance_no_return(SessionsHosts, id_session=session_id, id_host=_host_id)
            details['host'].append({'hostname': hostData.name, 'ipaddress': hostData.ipaddress, 'port': hostData.port, 'type': host_types[hostData.type]})
            
            if hostData.type == 0 : #MySQL
                    
                external_session = ExternalConnectionByHostId.getConn(_host_id)    
                
                def _execSQL(sql, _fetch=False):
                    if _fetch:
                        return external_session.execute(text(sql)).fetchall()
                    else:
                        external_session.execute(text(sql))
                
                characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
            
                # check if user exists mysql
                # SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'username')
                
                # REMOVE USER BEFORE CREATE A NEWER
                _command = 'DROP USER IF EXISTS '+username+';'
                results.append({'dropuserifexists': _command})
                _execSQL(_command)
                
                pass_len = 10
                password = "".join([random.choice(characters) for _ in range(pass_len)])
                results.append({'newpassword': password})
                details['password']=password
                database.edit_instance(Sessions, id=session_id, description=sessionData.description+"\n["+datetime.today().strftime('%Y-%m-%d')+"] Password:  "+password)
                
                # CREATE USER 'user'@'hostname';
                _command = "CREATE USER '"+username+"'@'%';"
                results.append({'createnewuser': _command})
                _execSQL(_command)
                
                
                for _database in permissions_obj_id[_host_id]:
                    
                    databaseData = _getDatabaseData(_database)     
                    database_tables_count = len(permissions_obj_id[_host_id][_database])
    
                                        
                    if database_tables_count == 0 : # todo o database (todas as tabelas)
                        
                        # GRANT ALL PRIVILEGES ON dbTest.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas database dbTest
                        _command = "GRANT ALL PRIVILEGES ON "+databaseData.name+".* To '"+username+"'@'%' IDENTIFIED BY '"+password+"';"
                        results.append({'grantpermission': _command})
                        _execSQL(_command)
                                                
                    else: # apenas algumas tabelas dentro de um database
                                                                                   
                        # Get all tables names from each external database
                        tables = _execSQL('SELECT table_name FROM information_schema.tables WHERE table_schema = "'+databaseData.name+'"', True)
                        qtd_tables_total = len(tables)
                        
                        if qtd_tables_total != database_tables_count :
                            
                            # GRANT PRIVILEGES PER TABLE
                            for _table in permissions_obj_name[hostData.name][databaseData.name]:
                                _command = "GRANT ALL PRIVILEGES ON "+databaseData.name+"."+_table+" To '"+username+"'@'%' IDENTIFIED BY '"+password+"';"
                                results.append({'grantpermission_table_'+_table: _command})
                                _execSQL(_command)
                        
                        else:
                            
                            # GRANT ALL PRIVILEGES ON dbTest.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas database dbTest
                            _command = "GRANT ALL PRIVILEGES ON "+databaseData.name+".* To '"+username+"'@'%' IDENTIFIED BY '"+password+"';"
                            results.append({'grantpermission': _command})
                            _execSQL(_command)
                                            
                                
                        
                # FLUSH PRIVILEGES;
                _command = "FLUSH PRIVILEGES;"
                results.append({'flushprivileges': _command})
                _execSQL(_command)
                                
                
                # GUIDE EXAMPLES
                # GRANT ALL PRIVILEGES ON *.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> todo o HOST
                # GRANT ALL PRIVILEGES ON dbTest.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas database dbTest
                # GRANT ALL PRIVILEGES ON dbTest.table_one To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas tabela table_one
                # FLUSH PRIVILEGES;
    
                
            elif host_types[hostData.type] == 1 : #Postgres
                print("ACCESS FOR POSTGRES - TODO")
            elif host_types[hostData.type] == 2 : #SQLServer
                print("ACCESS FOR SQL SERVER - TODO")
    
    
    return json.dumps({'details': details,'results': results}), 200



@app.route('/removeUserFromHostBySession', methods=['POST'])
def removeUserFromHostBySession(_data_received=None):
        
    _data = request.get_json()['data'] if _data_received==None else _data_received
    id_session = _data['session_id']
    user_name = _data['user_name']
    sessionData = database.get_id(Sessions, id_session)
    sessions_host = database.get_by(SessionsHosts, 'id_session', id_session)
    results = []
    if len(sessions_host)>0 :
        for _reg in sessions_host :
            external_session = ExternalConnectionByHostId.getConn(_reg.id_host)
            _command = 'DROP USER IF EXISTS '+user_name+';'
            results.append({'dropuserfromhost': _command, 'host_id': _reg.id_host})
            external_session.execute(text(_command))
            
            
    database.delete_instance_by(SessionsHosts, 'id_session', id_session)
    database.edit_instance(Sessions, id=id_session, description=sessionData.description+"\n["+datetime.today().strftime('%Y-%m-%d')+"] REMOVED")
                
    
    return json.dumps(results), 200