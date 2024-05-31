from flask import request, redirect, render_template, flash, url_for, request, send_file
from . import create_app, database
from .models import Users, Hosts, Databases, Tables, Config, Sessions, SessionsHosts, ExternalConnectionByHostId, AuditLog, db_name_ignore_per_type, host_types, user_types, user_status, session_status_type, table_type, db_username_deny, db_config_exceptions
from flask_wtf import FlaskForm #, DataRequired, Length
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from datetime import datetime
import sqlalchemy as sa
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
            "days_default_access": user.days_default_access,
            "password": user.password
        }

        all_users.append(new_user)
    if _json==True:
        return all_users
    else:
        return json.dumps(all_users), 200

@app.route('/updateUserPass', methods=['POST'])
@login_required
def updateUserPass():
    data = request.get_json()
    current_logged_user = getUserLogged(True)
    user_id = current_user.id if 'id' not in data or current_logged_user['is_adm']!=True else data['id']
    password= data['password']
    database.edit_instance(Users, user_id, password=generate_password_hash(password, method='pbkdf2:sha256'))
    return json.dumps(data), 200

@app.route('/addHost', methods=['POST'])
@login_required
def addHost():
    data = request.get_json()
    host_object = {}
    for item in data:
        host_object[item['name']] = item['value']
    database.add_instance(Hosts, name=host_object['name'], type=host_object['type'], ipaddress=host_object['ipaddress'], ipaddress_read=host_object['ipaddress_read'], port=host_object['port'], username=host_object['username'], password=host_object['password'])
    return json.dumps(host_object), 200


@app.route('/getHosts', methods=['GET'])
@login_required
def getHosts(_json=False):
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    
    hosts_pag = database.get_by_paginated(Hosts, 'name', page=pag, per_page=qtd)
    
    all_hosts = []
    for host in hosts_pag['items']:
        new_host = {
            "id": host.id,
            "name": host.name,
            "type": host_types[host.type],
            "ipaddress": host.ipaddress,
            "ipaddress_read": host.ipaddress_read,
            "port": host.port,
            "username": host.username,
            "password": "*", #host.password,
            "id_user": host.id_user or '',
            "created_at": str(host.created_at),
            "updated_at": str(host.updated_at) or ''
        }

        all_hosts.append(new_host)
    
    return_obj = {
        'total': hosts_pag['total'],
        'items': all_hosts,
        'pages': hosts_pag['pages'],
        'page': hosts_pag['page'],
        'has_prev': hosts_pag['has_prev'],
        'has_next': hosts_pag['has_next'],
        'prev_num': hosts_pag['prev_num'],
        'next_num': hosts_pag['next_num']
    }
    
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200

@app.route('/addConfig', methods=['POST'])
@login_required
def addConfig():
    data = request.get_json()
    config_obj = {}
    for item in data:
        config_obj[item['name']] = item['value']
    database.add_instance_no_return(Config, key=config_obj['key'], value=config_obj['value'])
    return json.dumps(config_obj), 200

@app.route('/updateConfig', methods=['POST'])
@login_required
def updateConfig():
    data = request.get_json()
    obj_key=''
    obj_val=''
    for _key in data:
        obj_key = _key
        obj_val = data[_key]
    if obj_key=='db_user_prefix':
        if obj_val.strip()=='':
            obj_val='cb_'
    if obj_key=='hours_user_session':
        if obj_val.strip()=='':
            obj_val='24'
    database.edit_instance_by(Config, 'key', obj_key, value=obj_val)
    return json.dumps(data), 200

@app.route('/deleteConfig', methods=['POST'])
@login_required
def deleteConfig():
    data = request.get_json()['data']
    obj_key = data['key']
    for exception in db_config_exceptions[0]:
        if obj_key==exception:
            return json.dumps({}), 200
    database.delete_instance_by(Config, 'key', obj_key)
    return json.dumps(data), 200

@app.route('/getConfig', methods=['GET'])
@login_required
def getConfig(_json=False):
    configs = database.get_all_order_by(Config, 'key')
    all_configs = []
    for _config in configs:
        config_key = _config.key
        config_value = _config.value
        all_configs.append({config_key:config_value})
    if _json==True:
        return all_configs
    else:
        return json.dumps(all_configs), 200
    
    
def getConfigValue(config_name):
    try:
        data = database.get_by(Config, 'key', config_name)
        if len(data)>0:
            for reg in data:
                return reg.value or False
        else:
            return False
    except:
        return False
    
@app.route('/getConfigParam/<config_name>', methods=['GET'])
@login_required
def getConfigParam(config_name):
    _value=''
    try:
        data = database.get_by(Config, 'key', config_name)
        if len(data)>0:
            for reg in data:
                _value = reg.value
        else:
            _value=''
    except:
        _value=''
    return json.dumps(_value), 200

@app.route('/getDatabases', methods=['GET'])
@login_required
def getDatabases(_json=False):
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    host_id = request.args.get('host_id', 0, type=int)
    if host_id!=0:
        databases_pag = database.get_by_paginated_filtered(Databases, 'id_host', host_id, 'name', page=pag, per_page=qtd)
    else:
        databases_pag = database.get_by_paginated(Databases, 'id', page=pag, per_page=qtd, orderby=True)
    
    all_databases = []
    for _database in databases_pag['items']:
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
    
    return_obj = {
        'total': databases_pag['total'],
        'items': all_databases,
        'pages': databases_pag['pages'],
        'page': databases_pag['page'],
        'has_prev': databases_pag['has_prev'],
        'has_next': databases_pag['has_next'],
        'prev_num': databases_pag['prev_num'],
        'next_num': databases_pag['next_num']
    }    
        
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200

@app.route('/getTables/<_dbid>', methods=['GET'])
@login_required
def getTables(_dbid, _json=False):
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    
    tables_pag = database.get_by_paginated_filtered(Tables, 'id_database', _dbid, 'name', page=pag, per_page=qtd)
    
    _database = database.get_id(Databases, _dbid)
    database_name = _database.name if _database else "Unknown database"
    items = []
    for e in tables_pag['items']:
        item_e = {
            "id": e.id,
            "name": e.name,
            "id_database": e.id_database,
            "database_name": database_name,
            "type": table_type[e.type],
            "type_id": e.type
        }
        items.append(item_e)
    
    return_obj = {
        'total': tables_pag['total'],
        'items': items,
        'pages': tables_pag['pages'],
        'page': tables_pag['page'],
        'has_prev': tables_pag['has_prev'],
        'has_next': tables_pag['has_next'],
        'prev_num': tables_pag['prev_num'],
        'next_num': tables_pag['next_num']
    }
    
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200


@app.route('/addUser', methods=['POST'])
@login_required
def addUser():
    data = request.get_json()
    user_obj = {}
    for item in data:
        if item['name']=='name':
            for username_denied in db_username_deny[0]:
                if item['value'].strip() == username_denied:
                    item['value']='DENIED_'+item['value'] 
        user_obj[item['name']] = item['value']
    database.add_instance(Users, name=user_obj['name'], type=user_obj['type'], status=1, email=user_obj['email'], parent=(None if user_obj['parent']=='' else user_obj['parent']), password=generate_password_hash(user_obj['password'], method='pbkdf2:sha256'))
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
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    
    if type=='-1':
        users_pag = database.get_by(Users, 'type', 0, 'name')
    else:
        users_pag = database.get_by_paginated(Users, 'name', page=pag, per_page=qtd)
    
    all_users = []
    for user in users_pag['items']:
        new_user = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "days_default_access": user.days_default_access,
            "parent": "" if user.parent is None else database.get_id(Users, user.parent).name,
            "parent_id": user.parent,
            "status": user.status,
            "status_name": user_status[user.status],
            "type": user_types[user.type],
        }
        all_users.append(new_user)
    
    return_obj = {
        'total': users_pag['total'],
        'items': all_users,
        'pages': users_pag['pages'],
        'page': users_pag['page'],
        'has_prev': users_pag['has_prev'],
        'has_next': users_pag['has_next'],
        'prev_num': users_pag['prev_num'],
        'next_num': users_pag['next_num']
    }
    
        
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200


@app.route('/addSession', methods=['POST'])
@login_required
def addSession():
    # session_status_type
    data = request.get_json()
    session_obj = {}
    for item in data:
        session_obj[item['name']] = item['value']       
    if 'writer' not in session_obj:
        session_obj['writer']=0
    _sess = database.add_instance(Sessions, user=session_obj['user'], writer=session_obj['writer'], status=-1, access_start=session_obj['access_start'], access_end=session_obj['access_end'], description=session_obj['description'])
    session_obj['id_session'] = _sess
    return json.dumps(session_obj), 200

def getFieldValuesFromObjectsArray(objects, name, getFieldNameById=False, ModelName=False):
    values = []
    for obj in objects:
        if name!=None and name!=False and obj!=False and hasattr(obj, name):
            item = getattr(obj, name)
            if item!=None:
                if getFieldNameById:
                    if ModelName:
                        values.append({item:getattr(database.get_id(ModelName, item),getFieldNameById)})
                    else:
                        values.append({item:getFieldNameById[item]})
                else:
                    values.append(item)
    return values

@app.route('/getSessions', methods=['GET'])
@login_required
def getSessions(_json=False):
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    print('getSessions')
    unique_users = getFieldValuesFromObjectsArray(database.get_distinct(Sessions,'user'), 'user', 'name', Users)
    unique_approvers = getFieldValuesFromObjectsArray(database.get_distinct(Sessions,'approver'), 'approver', 'name', Users)
    unique_status = getFieldValuesFromObjectsArray(database.get_distinct(Sessions,'status'), 'status', session_status_type)
    print('pegou uniques')
    sessions_pag = database.get_by_paginated(Sessions, 'request_date', page=pag, per_page=qtd, orderby=True)
    print('sessoes paginadas')
    all_sessions = []
    for session in sessions_pag['items']:
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
            "writer": session.writer,
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
    
    return_obj = {
        'total': sessions_pag['total'],
        'items': all_sessions,
        'pages': sessions_pag['pages'],
        'page': sessions_pag['page'],
        'has_prev': sessions_pag['has_prev'],
        'has_next': sessions_pag['has_next'],
        'prev_num': sessions_pag['prev_num'],
        'next_num': sessions_pag['next_num'],
        'unique_users': unique_users,
        'unique_approvers': unique_approvers,
        'unique_status': unique_status
    }
    
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200


@app.route('/getUserLogged', methods=['GET'])
@login_required
def getUserLogged(_json=False):
    user_data = database.get_id(Users,current_user.id)      
    return_obj = {"id":current_user.id,"name":user_data.name,"is_adm":(True if int(user_data.type)==2 or int(user_data.type)==0 else False)}
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200  

    
@app.route('/getSessions/<user_id>', methods=['GET'])
@login_required
def getSessionsUser(user_id, _json=False):
    pag = request.args.get('pag', 1, type=int)
    qtd = request.args.get('qtd', 5, type=int)
    
    # unique_users = Users.objects.filter(session__isnull=False).distinct()
        
    sessions_pag = database.get_by_paginated_filtered(Sessions, 'user', user_id, 'request_date', page=pag, per_page=qtd, order_desc=True)
    
    sessions = database.get_by(Sessions, 'user', user_id)
    all_sessions = []
    for session in sessions:
        _user = database.get_id(Users, session.user)
        user_name = _user.name if _user else "Unknown user"
        new_session = {
            "id": session.id,
            "user": session.user,
            "writer": session.writer,
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
        
    approver_user=False
    user_data = database.get_id(Users,user_id)
    if int(user_data.type)==2:
        approver_user=True
        print('User approver')
        # verifica se o user logado possui "usuarios filhos"
        sessions_child = database.get_by_join(Sessions, 'user', user_id, join=Users, parent_column='parent', parent_value=user_id)
        for session in sessions_child:
            _user = database.get_id(Users, session.user)
            user_name = _user.name if _user else "Unknown user"
            new_session = {
                "id": session.id,
                "user": session.user,
                "writer": session.writer,
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
    
    return_obj = {
        'total': sessions_pag['total'],
        'items': all_sessions,
        'pages': sessions_pag['pages'],
        'page': sessions_pag['page'],
        'has_prev': sessions_pag['has_prev'],
        'has_next': sessions_pag['has_next'],
        'prev_num': sessions_pag['prev_num'],
        'next_num': sessions_pag['next_num'],
        'approver_user': approver_user
    }        
            
    if _json==True:
        return return_obj
    else:
        return json.dumps(return_obj), 200

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
def getHostsDatabasesTablesTree():
    return getHostsDatabasesTablesTreeFromFile()

@app.route('/forceGenerateTree', methods=['GET'])
@login_required
def forceGenerateTree():
    getHostsDatabasesTablesTreeFromFile(_force_generate=True)
    return json.dumps(getHostsDatabasesTablesTreeFromFile()), 200

def getHostsDatabasesTablesTreeFromFile(_force_generate=False):
    nome_arquivo = '/tmp/HostsDatabasesTablesTree.json'
    if _force_generate:
        print('forcando a criacao de nova arvore')
        dados = generateHostsDatabasesTablesTree(_json=True, nome_arquivo=nome_arquivo)
    else:
        if os.path.exists(nome_arquivo):
            print('arquivo de arvore existente')
            with open(nome_arquivo, 'r') as f:
                try:
                    dados = json.load(f)
                    print('retornando arquivo de arvore')
                except json.decoder.JSONDecodeError:
                    print('execao do arquivo de arvore, gerando dinamicamente')
                    dados = generateHostsDatabasesTablesTree(_json=True, nome_arquivo=nome_arquivo)
        else:
            print('arquivo de arvore nao existe, gerando dinamicamente')
            dados = generateHostsDatabasesTablesTree(_json=True, nome_arquivo=nome_arquivo)
    return dados
    
def generateHostsDatabasesTablesTree(_json=False, nome_arquivo=False):
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
    if nome_arquivo!=False:
        with open(nome_arquivo, 'w') as f:
            json.dump(tree, f, indent=4)
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
    _return = postHostsDatabasesTablesTree(_data['session_id'],_data['approver'],True)
    return json.dumps(_return), 200
    
@app.route('/postHostsDatabasesTablesTree', methods=['POST'])
@login_required
def postHostsDatabasesTablesTree(_approve=False, _approver=False, _as_json=False):
    
    if _approve!=False:
        _approve_data = database.get_id(Sessions, _approve)
        _data = json.loads(_approve_data.datatree)
    else:
        _data = request.get_json()['data']
        
    privilegesConfig = getConfigValue('privileges') or 'SELECT' ## ALL PRIVILEGES
    permissions = returnPermissionTree(_data['datatree'])
    permissions_obj_name = permissions['permissions_name']
    permissions_obj_id = permissions['permissions_id']
    user_auto_approve = permissions['user_auto_approve']
    filter_user = _data['filter_user']

    prefixo = (getConfigValue('db_user_prefix') if getConfigValue('db_user_prefix')!='' and getConfigValue('db_user_prefix')!=False else '_') or '_'
    username = prefixo + _data['username']
    session_id = _data['session_id']
    details={}
    details['host']=[]
    details['permissions']=permissions_obj_name
    _session_data = database.get_id(Sessions, session_id)
    details['session_writer']= True if _session_data.writer == 1 else False
    
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
            host_details_json = {'hostname': hostData.name, 'endpoint_reader': hostData.ipaddress_read, 'port': hostData.port, 'type': host_types[hostData.type]}
            if _session_data.writer == 1:
                host_details_json['endpoint_writer'] = hostData.ipaddress
            details['host'].append(host_details_json)
            
            privilegesConfig = 'SELECT, UPDATE, INSERT, DELETE' if _session_data.writer == 1 else privilegesConfig
            print("PRIVILEGE: "+privilegesConfig)
            results.append({'PRIVILEGE': privilegesConfig})
            
            # pula o laco caso nao tenha permissao
            if ((filter_user!=False and user_auto_approve!=True) or (_session_data.writer == 1 and _approve==False)) :
                results.append({'lacoPuladoSemPermissao':{"filter_user":filter_user,"user_auto_approve":user_auto_approve,"writer_permission": (_session_data.writer == 1)}})
                continue

            _removeUserFromHost = removeUserFromHostBySession({'session_id': session_id, 'user_name': username})
            results.append({'removeUserFromHostBySession':_removeUserFromHost})
                    
            external_session = ExternalConnectionByHostId.getConn(_host_id)   
            def _execSQL(sql, _fetch=False):
                if _fetch:
                    return external_session.execute(text(sql)).fetchall()
                else:
                    external_session.execute(text(sql))
                        
            if hostData.type == 0 : #MySQL
                                       
                try:
                    # CREATE USER 'user'@'hostname';
                    _command = "CREATE USER '"+username+"'@'%' IDENTIFIED BY '"+password+"';"
                    results.append({'createnewuser': _command})
                    _execSQL(_command)                    
                except Exception as ex:
                    print('Exception creating user')
                    print(ex)
                
                for _database in permissions_obj_id[_host_id]:
                    
                    databaseData = _getDatabaseData(_database)     
                    database_tables_count = len(permissions_obj_id[_host_id][_database])
                   
                    if database_tables_count == 0 :
        
                        _command = "GRANT "+ privilegesConfig +" ON "+databaseData.name+".* To '"+username+"'@'%';"
                        results.append({'grantpermission': _command})
                        _execSQL(_command)
                                                
                    else:
                                                                                   
                        # Get all tables names from each external database
                        tables = _execSQL('SELECT table_name FROM information_schema.tables WHERE table_schema = "'+databaseData.name+'"', True)
                        qtd_tables_total = len(tables)
                        
                        if qtd_tables_total != database_tables_count :
                            
                            # GRANT PRIVILEGES PER TABLE
                            for _table in permissions_obj_name[hostData.name][databaseData.name]:
                                _command = "GRANT "+ privilegesConfig +" ON "+databaseData.name+"."+_table+" To '"+username+"'@'%';" # IDENTIFIED BY '"+password+"';"
                                results.append({'grantpermission_table_'+_table: _command})
                                _execSQL(_command)
                        
                        else:
                            
                            _command = "GRANT "+ privilegesConfig +" ON "+databaseData.name+".* To '"+username+"'@'%';" 
                            results.append({'grantpermission': _command})
                            _execSQL(_command)
                                                
                # FLUSH PRIVILEGES;
                _command = "FLUSH PRIVILEGES;"
                results.append({'flushprivileges': _command})
                _execSQL(_command)
                                
                database.edit_instance(Sessions, id=session_id, status=1, approve_date=datetime.now())
                                
            elif hostData.type == 1:  # PostgreSQL

                # CREATE USER 'user' WITH PASSWORD 'password';
                _command = "CREATE ROLE "+username+" NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN NOREPLICATION NOBYPASSRLS PASSWORD '"+password+"'; COMMIT;"
                results.append({'createnewuser': _command})
                _execSQL(_command)

                for _database in permissions_obj_id[_host_id]:
                    databaseData = _getDatabaseData(_database)
                    database_tables_count = len(permissions_obj_id[_host_id][_database])

                    if database_tables_count == 0:  # All tables in the database
                        # GRANT ALL PRIVILEGES ON DATABASE dbTest TO 'user';
                        _command = "GRANT ALL PRIVILEGES ON DATABASE "+databaseData.name+" TO "+username+"; COMMIT;"
                        results.append({'grantpermission': _command})
                        _execSQL(_command)

                    else:  # Specific tables within a database
                        # GRANT PRIVILEGES PER TABLE
                        for _table in permissions_obj_name[hostData.name][databaseData.name]:
                            _command = "GRANT ALL PRIVILEGES ON "+_table+" TO "+username+"; COMMIT;"
                            results.append({'grantpermission_table_'+_table: _command})
                            _execSQL(_command)

                database.edit_instance(Sessions, id=session_id, status=1, approve_date=datetime.now())


            elif hostData.type == 2:  # SQL Server

                # CREATE LOGIN 'user' WITH PASSWORD = 'password';
                _command = "CREATE LOGIN "+username+" WITH PASSWORD = '"+password+"';"
                results.append({'createnewuser': _command})
                _execSQL(_command)

                for _database in permissions_obj_id[_host_id]:
                    databaseData = _getDatabaseData(_database)
                    database_tables_count = len(permissions_obj_id[_host_id][_database])

                    if database_tables_count == 0:  # All tables in the database
                        # GRANT ALL PRIVILEGES ON DATABASE::dbTest TO 'user';
                        _command = "USE "+databaseData.name+"; GRANT ALL TO "+username+";"
                        results.append({'grantpermission': _command})
                        _execSQL(_command)

                    else:  # Specific tables within a database
                        # GRANT PRIVILEGES PER TABLE
                        for _table in permissions_obj_name[hostData.name][databaseData.name]:
                            _command = "USE "+databaseData.name+"; GRANT ALL ON "+_table+" TO "+username+";"
                            results.append({'grantpermission_table_'+_table: _command})
                            _execSQL(_command)

                database.edit_instance(Sessions, id=session_id, status=1, approve_date=datetime.now())
            
            
            database.add_instance_no_return(SessionsHosts, id_session=session_id, id_host=_host_id)
            results.append({'SessionsHostsCreated':True})
                
            external_session.close()
    else:
        details['waiting_approve'] = True
    
    _return_json = {'details': details,'results': results,'username': username}
    if _as_json:
        return _return_json
    else:
        return json.dumps(_return_json), 200


@app.route('/expireAccessEnd', methods=['GET'])
def expireAccessEnd():
    _sessions_expired=[]
    _expired = database.get_by_date_and_filter(Sessions, 'access_end', datetime.now(), 'status', 1, False)
    print('Sessoes expiradas: ')
    print(_expired)
    for expired_session in _expired:
        removeUserFromHostBySession_action({'session_id':expired_session.id,'expired':datetime.now()})
        _sessions_expired.append(expired_session.id)
    return {'session_expired': _sessions_expired}, 200


@app.route('/updateCrudRealTime', methods=['POST'])
@login_required
def updateCrudRealTime(_data_received=None):
    _data = request.get_json()['data'] if _data_received==None else _data_received
    table_name = _data['table_edited']
    instance_id = _data['_id_edited']
    field_name = _data['field_edited']
    new_value = _data['val_edited']
    edited = database.edit_instance(model=globals()[table_name], id=instance_id, **{field_name: new_value})
    print('EDITED: ')
    print('val_edited: ' + new_value)
    print('_id_edited: ' + instance_id)
    print('table_edited: ' + table_name)
    print('field_edited: ' + field_name)
    print('original_edited: ' + _data['original_edited'])
    print('------------------------------')
    print(edited)
    print('------------------------------')
    return json.dumps(_data), 200
    
@app.route('/removeHostAndAllTogether', methods=['POST'])
@login_required
def removeHostAndAllTogether(_data_received=None):
    results = []
    _data = request.get_json()['data'] if _data_received==None else _data_received
    host_id = _data['host_id']
    _reg_host = database.get_id(Hosts, host_id)
    _removeSessions = removeUserFromHostByHostId(host_id)
    results.append({'removeSessions':_removeSessions})
    _databases = database.get_by(Databases, 'id_host', host_id)
    if len(_databases)>0 :
        for _reg_database in _databases :
            _tables = database.get_by(Tables, 'id_database', _reg_database.id)
            if len(_tables)>0 :
                for _reg_table in _tables :
                    _remove_table = database.delete_instance(Tables, _reg_table.id)
                    results.append({'removeTable':_remove_table,'id':_reg_table.id,'name':_reg_table.name})
            _remove_database = database.delete_instance(Databases, _reg_database.id)
            results.append({'removeDatabase':_remove_database,'id':_reg_database.id,'name':_reg_database.name})
    _host_rem = {'id':_reg_host.id,'name':_reg_host.name}
    _remove_host = database.delete_instance(Hosts, host_id)
    _host_rem['removeHost']=_remove_host
    results.append(_host_rem)
    return json.dumps(results), 200
    

def removeUserFromHostByHostId(_host_id):
    print("removeUserFromHostByHostId")
    print(_host_id)
    try:
        sessionsData = database.get_by(SessionsHosts, 'id_host', _host_id)
        if len(sessionsData)>0 :
            for _reg in sessionsData :
                removeUserFromHostBySession({'session_id':_reg.id_session})
    except Exception as ex:
        print('Exception on remove user')
        print(ex)
        
            

# pode receber apenas _data['session_id']
@app.route('/removeUserFromHostBySession', methods=['POST'])
def removeUserFromHostBySession(_data_received=None):
    return removeUserFromHostBySession_action(_data_received=_data_received)
    
def removeUserFromHostBySession_action(_data_received=None):
    print("removeUserFromHostBySession")
    print(_data_received)
    _data = request.get_json()['data'] if _data_received==None else _data_received
    id_session = _data['session_id']
    sessionData = database.get_id(Sessions, id_session)
    if 'user_name' not in _data:
        _data['user_name'] = database.get_id(Users, sessionData.user).name
    prefixo = (getConfigValue('db_user_prefix') if getConfigValue('db_user_prefix')!='' and getConfigValue('db_user_prefix')!=False else '_') or '_'
    user_name = (prefixo + _data['user_name']) if prefixo not in _data['user_name'] else _data['user_name']
    sessions_host = database.get_by(SessionsHosts, 'id_session', id_session)
    print('preparando exclusao: '+user_name)
    results = []
    try:
        print('sessoes: '+str(len(sessions_host)))
        if len(sessions_host)>0 :
            for _reg in sessions_host :     
                # TODO: criar um apagar usuario por HOST mas tem q ter o username pq ao remover um session pode nao existir mais um SESSIONHOST         
                hostData = database.get_id(Hosts, _reg.id_host)
                print("Host: "+hostData.name)
                _databases_host = database.get_by(Databases, 'id_host', _reg.id_host)
                if len(_databases_host)>0 :
                    for _reg_database in _databases_host :                    
                        external_session = ExternalConnectionByHostId.getConn(_reg.id_host)
                        
                        if hostData.type == 0 : #MySQL
                            _command = 'DROP USER IF EXISTS \''+user_name+'\'@\''+_reg_database.name+'\';'
                            print(_command)
                            results.append({'dropuserfromdatabase': _command, 'host_id': _reg.id_host, 'database': _reg_database.name})
                            external_session.execute(text(_command))     

                        if hostData.type == 1 : #Postgres
                            _command = 'DROP OWNED BY '+user_name
                            print(_command)
                            results.append({'dropuserfromdatabase1': _command, 'host_id': _reg.id_host, 'database': _reg_database.name})
                            external_session.execute(text(_command))     

                            _command = 'DROP ROLE '+user_name
                            print(_command)
                            results.append({'dropuserfromdatabase2': _command, 'host_id': _reg.id_host, 'database': _reg_database.name})
                            external_session.execute(text(_command))     

                            _command = 'COMMIT'
                            print(_command)
                            results.append({'dropuserfromdatabase3': _command, 'host_id': _reg.id_host, 'database': _reg_database.name})
                            external_session.execute(text(_command))     

                        if hostData.type == 2 : #SQLServer
                            _command = '' #TODO
                                
                if hostData.type == 0 : #MySQL   
                    _command = 'DROP USER IF EXISTS \''+user_name+"\'@'%';"                    
                    print(_command)
                    results.append({'dropuserfromhost': _command, 'host_id': _reg.id_host})
                    external_session.execute(text(_command))
        else:
            results.append({'nenhumhost': True})
            print('nenhum host de sessao')
    except Exception as ex:
        print(ex)
        _msgtry = 'banco sem conexao - pode ter sido desativado'
        print(_msgtry)
        results.append({'dropuserfromhost': _msgtry})
    try:
        database.edit_instance(Sessions, id_session, password=None, status=(3 if 'expired' in _data else 2), approve_date=None, approver=None)
        print('atualizou sessao info')
        database.delete_instance_by(SessionsHosts, 'id_session', id_session)
        print('apagou sessionhost')
        # database.edit_instance(Sessions, id=id_session, description=sessionData.description+"\n["+datetime.today().strftime('%Y-%m-%d')+"] REMOVED")
    except Exception as ex:
        print('ERRO: ')
        print(ex)
    print('returnOK')
    return json.dumps(results), 200


@app.route('/removeSession/<user_id_logged>', methods=['POST'])
@login_required
def removeSession(user_id_logged, _data_received=None):
    print("removeSession")
    print(user_id_logged)
    print(_data_received)
    _data = request.get_json()['data'] if _data_received==None else _data_received
    id_session = _data['session_id']
    user_id_selected = _data['user_id']
    results = []
    
    if user_id_logged!='0' and user_id_logged != user_id_selected:
        return json.dumps(results), 200
    
    sessions_host = database.get_by(SessionsHosts, 'id_session', id_session)
    print(sessions_host)
    if len(sessions_host)>0 :
        for _reg in sessions_host :
            print(_reg)
            removeUserFromHostBySession({'session_id':_reg.id_session})
            
            
    database.delete_instance_by(SessionsHosts, 'id_session', id_session)
    database.delete_instance_by(Sessions, 'id', id_session)
    
    return json.dumps(results), 200


    

# AUDITLOGS
def log_changes(session: Session, operation: str):
    for obj in session.new:
        if isinstance(obj, AuditLog):
            continue
        for attr in sa.inspect(obj).mapper.column_attrs:
            log_entry = AuditLog(
                table_name=obj.__tablename__,
                operation=operation,
                field_name=attr.key,
                new_value=str(getattr(obj, attr.key)),
                changed_by=current_user.id
            )
            session.add(log_entry)
    
    for obj in session.dirty:
        if isinstance(obj, AuditLog):
            continue
        state = sa.inspect(obj)
        for attr in state.attrs:
            if attr.history.has_changes():
                old_value = attr.history.deleted[0] if attr.history.deleted else None
                new_value = attr.history.added[0] if attr.history.added else None
                log_entry = AuditLog(
                    table_name=obj.__tablename__,
                    operation=operation,
                    field_name=attr.key,
                    old_value=str(old_value) if old_value else None,
                    new_value=str(new_value) if new_value else None,
                    changed_by=current_user.id
                )
                session.add(log_entry)

    for obj in session.deleted:
        if isinstance(obj, AuditLog):
            continue
        for attr in sa.inspect(obj).mapper.column_attrs:
            log_entry = AuditLog(
                table_name=obj.__tablename__,
                operation=operation,
                field_name=attr.key,
                old_value=str(getattr(obj, attr.key)),
                changed_by=current_user.id
            )
            session.add(log_entry)

@sa.event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    log_changes(session, 'INSERT')

@sa.event.listens_for(Session, 'before_commit')
def before_commit(session):
    log_changes(session, 'UPDATE')

@sa.event.listens_for(Session, 'before_delete')
def before_delete(session, flush_context, instances):
    log_changes(session, 'DELETE')