from flask import request, redirect, render_template, flash, url_for, request, send_file
from . import create_app, database
from .models import Users, Hosts, Databases, Tables, Sessions, SessionsHosts, ExternalConnectionByHostId, db_name_ignore_per_type, host_types, user_types, user_status, session_status_type, table_type
from flask_wtf import FlaskForm #, DataRequired, Length
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
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
    
@app.route('/<filename>.html')
def render_html_template(filename):
    if filename=='logout':
        return redirect(url_for('auth.login'))
    elif filename=='login' or not current_user.is_authenticated:
        return render_template(f'{filename}.html')
    else:
        return render_template(f'{filename}.html', user_id=current_user.id)

@app.route('/<filename>.ico')
def return_ico_file(filename):
    return send_file(f'templates/{filename}.ico')

@app.route('/favicon/<filename>')
def return_favicon_file(filename):
    return send_file(f'templates/favicon/{filename}')

@app.route('/getUsers', methods=['GET'])
@login_required
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


@app.route('/addHost', methods=['POST'])
@login_required
def addHost():
    data = request.get_json()
    host_object = {}
    for item in data:
        host_object[item['name']] = item['value']
    database.add_instance(Hosts, name=host_object['name'], type=host_object['type'], ipaddress=host_object['ipaddress'], port=host_object['port'], username=host_object['username'], password=host_object['password'])
    return json.dumps(host_object), 200


@app.route('/getHosts', methods=['GET'])
@login_required
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
@login_required
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

@app.route('/getTables/<dbid>', methods=['GET'])
@login_required
def getTables(dbid, _json=False):
    tables = database.get_by(Tables, 'id_database', dbid, 'name')
    all_tables = []
    for table in tables:
        _database = database.get_id(Databases, table.id_database)
        database_name = _database.name if _database else "Unknown database"
        new_table = {
            "id": table.id,
            "name": table.name,
            "id_database": table.id_database,
            "database_name": database_name,
            "type": table_type[table.type],
            "type_id": table.type
        }
        all_tables.append(new_table)
    if _json==True:
        return all_tables
    else:
        return json.dumps(all_tables), 200


@app.route('/addUser', methods=['POST'])
@login_required
def addUser():
    data = request.get_json()
    user_obj = {}
    for item in data:
        user_obj[item['name']] = item['value']
    database.add_instance(Users, name=user_obj['name'], type=user_obj['type'], email=user_obj['email'], parent=(None if user_obj['parent']=='' else user_obj['parent']), password=generate_password_hash(user_obj['password'], method='pbkdf2:sha256'))
    return json.dumps(user_obj), 200


@app.route('/statusChangeUser/<user_id>/<status>', methods=['GET'])
@login_required
def statusChangeUser(user_id,status):    
    database.edit_instance(Users, user_id, status=status)
    return json.dumps({}), 200

@app.route('/typeChangeTable/<table_id>/<type>', methods=['GET'])
@login_required
def typeChangeTable(table_id,type):    
    database.edit_instance(Tables, table_id, type=type)
    return json.dumps({}), 200


@app.route('/getUsers/<type>', methods=['GET'])
@login_required
def getUsers(type,_json=False):
    users = database.get_all_order_by(Users, 'id')
    all_users = []
    for user in users:
        new_user = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "parent": "" if user.parent is None else database.get_id(Users, user.parent).name,
            "status": user.status,
            "status_name": user_status[user.status],
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
@login_required
def addSession():
    # session_status_type
    data = request.get_json()
    session_obj = {}
    for item in data:
        session_obj[item['name']] = item['value']        
    _sess = database.add_instance(Sessions, user=session_obj['user'], status=-1, access_start=session_obj['access_start'], access_end=session_obj['access_end'], description=session_obj['description'])
    session_obj['id_session'] = _sess
    return json.dumps(session_obj), 200


@app.route('/getSessions', methods=['GET'])
@login_required
def getSessions(_json=False):
    sessions = database.get_all_order_by(Sessions, 'id', True)
    all_sessions = []
    for session in sessions:
        _approver_name=''
        if session.approver!='' and session.approver!='null' and session.approver!='None':
            _approver_ = database.get_id(Users, session.approver)
            if _approver_!=False:
                _approver_name = _approver_.name
        _user = database.get_id(Users, session.user)
        user_name = _user.name if _user else "Unknown user"
        new_session = {
            "id": session.id,
            "user": session.user,
            "user_name": user_name,
            "approver":  _approver_name, #session.approver,
            "access_start": str(session.access_start) or '',
            "access_end": str(session.access_end) or '',
            "status": session_status_type[session.status],
            "status_id": session.status,
            "request_date": str(session.request_date) or '',
            "approve_date": str(session.approve_date) or '',
            "description": session.description
        }
        all_sessions.append(new_session)
    if _json==True:
        return all_sessions
    else:
        return json.dumps(all_sessions), 200


@app.route('/getSessions/<user_id>', methods=['GET'])
@login_required
def getSessionsUser(user_id, _json=False):
    sessions = database.get_by(Sessions, 'user', user_id)
    all_sessions = []
    for session in sessions:
        _user = database.get_id(Users, session.user)
        user_name = _user.name if _user else "Unknown user"
        new_session = {
            "id": session.id,
            "user": session.user,
            "user_name": user_name,
            "approver": '' if session.approver==None else database.get_id(Users, session.approver).name,
            "access_start": str(session.access_start) or '',
            "access_end": str(session.access_end) or '',
            "status": session_status_type[session.status],
            "status_id": session.status,
            "request_date": str(session.request_date) or '',
            "approve_date": str(session.approve_date) or '',
            "description": session.description
        }
        all_sessions.append(new_session)
    if _json==True:
        return all_sessions
    else:
        return json.dumps(all_sessions), 200

@app.route('/getTreeSession/<session_id>', methods=['GET'])
@login_required
def getTreeSession(session_id, _json=False):
    session = database.get_id(Sessions, session_id)
    if session.datatree != None and 'datatree' in json.loads(session.datatree):
        return json.dumps(returnPermissionTree(json.loads(session.datatree)['datatree'])), 200
    else:
        return json.dumps({}), 200
    
@app.route('/getHostsDatabasesTablesTree', methods=['GET'])
@login_required
def getHostsDatabasesTablesTree(_json=False):
    hosts = database.get_all_order_by(Hosts, 'name')
    tree = []
    for host in hosts:
        databases = database.get_all_order_by(Databases, 'name')
        host_dict = {
            "id": str(host.id),
            "text": host.name,
            "children": []
        }  # 🔒🔓
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
                            "text": ('🔒 ' if table.type==0 else "✅ ") + table.name
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
    user_auto_approve=True
    
    def _getHostName(_id):
        return database.get_id(Hosts, _id).name
    def _getDatabaseName(_id):
        return database.get_id(Databases, _id).name
    def _getTableDetails(_id):
        return database.get_id(Tables, _id)
    
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
    def _addTable(_id_host,_id_database,_id_table,user_auto_approve):
        _hostname = _getHostName(_id_host)
        _databasename = _getDatabaseName(_id_database)
        _tabledetails = _getTableDetails(_id_table)
        if _tabledetails.name not in permissions_obj_name[_hostname][_databasename]:
            if _tabledetails.type != 1 :
                user_auto_approve = False
            permissions_obj_name[_hostname][_databasename].append(_tabledetails.name)
            permissions_obj_id[_id_host][_id_database].append(_id_table)
        return user_auto_approve
    
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
            _user_auto_approve = _addTable(_parts[0],_parts[1],_parts[2],user_auto_approve)
            if user_auto_approve:
                user_auto_approve = _user_auto_approve # so altera o valor pra false, nao mais pra true se ocorrer
        else :            
            print('else ')
            print(_parts)
    return { 'permissions_name' : permissions_obj_name , 'permissions_id' : permissions_obj_id, 'user_auto_approve': user_auto_approve }


@app.route('/postHostsDatabasesTablesTreeApprove', methods=['POST'])
@login_required
def postHostsDatabasesTablesTreeApprove():
    _data = request.get_json()['data']
    _return = postHostsDatabasesTablesTree(_data['session_id'],_data['approver'])
    print(_return)
    return {}, 200
    
@app.route('/postHostsDatabasesTablesTree', methods=['POST'])
@login_required
def postHostsDatabasesTablesTree(_approve=False,_approver=False):
    
    # TODO: pensar em colocar ou controlar por HOST esses usuarios, precisa?
    
    if _approve!=False:
        _approve_data = database.get_id(Sessions, _approve)
        _data = json.loads(_approve_data.datatree)
    else:
        _data = request.get_json()['data']
    
    permissions = returnPermissionTree(_data['datatree'])
    permissions_obj_name = permissions['permissions_name']
    permissions_obj_id = permissions['permissions_id']
    user_auto_approve = permissions['user_auto_approve']
    filter_user = _data['filter_user']
    
    username = _data['username']
    session_id = _data['session_id']
    details={}
    details['host']=[]
    details['permissions']=permissions_obj_name
    
    def _getHostData(_id):
        return database.get_id(Hosts, _id)
    def _getDatabaseData(_id):
        return database.get_id(Databases, _id)
        
    results = []
    
    if _approve==False:
        characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")            
        pass_len = 10
        password = "".join([random.choice(characters) for _ in range(pass_len)])
        results.append({'newpassword': password})
        details['password']=password
        database.edit_instance(Sessions, id=session_id, status=0, password=password, datatree=json.dumps(_data))
    else:
        password = _approve_data.password
        results.append({'newpassword': password})
        details['password']=password
        user_auto_approve = True
        filter_user = False
        database.edit_instance(Sessions, id=session_id, status=1, approver=_approver)
    
    details['user_auto_approve'] = user_auto_approve
    details['filter_user'] = filter_user
    
    if (len(permissions_obj_id)>0) :
        details['waiting_approve'] = False
        for _host_id in permissions_obj_id :
            hostData = _getHostData(_host_id)
            
            # create relationship for future remove
            results.append({'removingOldSessionHost': session_id+'-'+_host_id})
            results.append({'addSessionHost': session_id+'-'+_host_id})
            details['host'].append({'hostname': hostData.name, 'ipaddress': hostData.ipaddress, 'port': hostData.port, 'type': host_types[hostData.type]})
            
            # pula o laco caso nao tenha permissao
            if filter_user!=False or (filter_user==False and user_auto_approve!=True) :
                continue
                        
            if _approve==False:
                removeUserFromHostBySession({'session_id': session_id, 'user_name': username})
                database.add_instance_no_return(SessionsHosts, id_session=session_id, id_host=_host_id)
                
            def _execSQL(sql, _fetch=False):
                if _fetch:
                    return external_session.execute(text(sql)).fetchall()
                else:
                    external_session.execute(text(sql))
                    
                    
            if hostData.type == 0 : #MySQL
                    
                external_session = ExternalConnectionByHostId.getConn(_host_id)   
                
                # check if user exists mysql
                # SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'username')
                
                # REMOVE USER BEFORE CREATE A NEWER
                _command = 'DROP USER IF EXISTS '+username+';'
                results.append({'dropuserifexists': _command})
                _execSQL(_command)
                
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
                                
                                
                database.edit_instance(Sessions, id=session_id, status=1, approve_date=datetime.now())
                
                # GUIDE EXAMPLES
                # GRANT ALL PRIVILEGES ON *.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> todo o HOST
                # GRANT ALL PRIVILEGES ON dbTest.* To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas database dbTest
                # GRANT ALL PRIVILEGES ON dbTest.table_one To 'user'@'hostname' IDENTIFIED BY 'password'; -> apenas tabela table_one
                # FLUSH PRIVILEGES;
    
                
            elif host_types[hostData.type] == 1 : #Postgres
                print("ACCESS FOR POSTGRES - TODO")
            elif host_types[hostData.type] == 2 : #SQLServer
                print("ACCESS FOR SQL SERVER - TODO")
                
    else:
        details['waiting_approve'] = True
    
    
    return json.dumps({'details': details,'results': results}), 200


@app.route('/expireAccessEnd', methods=['GET'])
@login_required
def expireAccessEnd():
    _sessions_expired=[]
    _expired = database.get_by_date_and_filter(Sessions, 'access_end', datetime.now(), 'status', 1, False)
    for expired_session in _expired:
        removeUserFromHostBySession({'session_id':expired_session.id,'expired':datetime.now()})
        _sessions_expired.append(expired_session.id)
    return {'session_expired': _sessions_expired}, 200


# pode receber apenas _data['session_id']
@app.route('/removeUserFromHostBySession', methods=['POST'])
@login_required
def removeUserFromHostBySession(_data_received=None):
        
    _data = request.get_json()['data'] if _data_received==None else _data_received
    id_session = _data['session_id']
    sessionData = database.get_id(Sessions, id_session)
    if 'user_name' not in _data:
        _data['user_name'] = database.get_id(Users, sessionData.user).name
    user_name = _data['user_name']
    sessions_host = database.get_by(SessionsHosts, 'id_session', id_session)
    results = []
    if len(sessions_host)>0 :
        for _reg in sessions_host :
            external_session = ExternalConnectionByHostId.getConn(_reg.id_host)
            _command = 'DROP USER IF EXISTS '+user_name+';'
            results.append({'dropuserfromhost': _command, 'host_id': _reg.id_host})
            external_session.execute(text(_command))
            
            
    database.delete_instance_by(SessionsHosts, 'id_session', id_session)
    database.edit_instance(Sessions, id=id_session, password=None, status=(3 if 'expired' in _data else 2), approve_date=None)
    # database.edit_instance(Sessions, id=id_session, description=sessionData.description+"\n["+datetime.today().strftime('%Y-%m-%d')+"] REMOVED")
    
    return json.dumps(results), 200


@app.route('/removeSession/<user_id_logged>', methods=['POST'])
@login_required
def removeSession(user_id_logged, _data_received=None):
        
    _data = request.get_json()['data'] if _data_received==None else _data_received
    id_session = _data['session_id']
    user_name = _data['user_name']
    user_id_selected = _data['user_id']
    
    if user_id_logged!='0' and user_id_logged != user_id_selected:
        return {}, 200
    
    sessions_host = database.get_by(SessionsHosts, 'id_session', id_session)
    results = []
    if len(sessions_host)>0 :
        for _reg in sessions_host :
            external_session = ExternalConnectionByHostId.getConn(_reg.id_host)
            _command = 'DROP USER IF EXISTS '+user_name+';'
            results.append({'dropuserfromhost': _command, 'host_id': _reg.id_host})
            external_session.execute(text(_command))
            
            
    database.delete_instance_by(SessionsHosts, 'id_session', id_session)
    database.delete_instance_by(Sessions, 'id', id_session)
    
    return json.dumps(results), 200