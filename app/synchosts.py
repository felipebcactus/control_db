from flask import Blueprint
from sqlalchemy.sql import text
from .models import Hosts, Databases, Tables, ExternalConnectionByHostId, db_name_ignore_per_type, host_types
from . import database
import json

synchosts_bp = Blueprint('synchosts', __name__)

@synchosts_bp.route('/synchosts/<host_id>', methods=['GET'])
def synchosts(host_id):
    try:
        external_session = ExternalConnectionByHostId.getConn(host_id)

        connections = database.get_id(Hosts, host_id)
        
        # Get all database names from the external database
        qry=''
        if connections.type == 0 : #MySQL
            qry = text('SHOW DATABASES;')    
        elif connections.type == 1:  # PostgreSQL
            qry = text('SELECT datname FROM pg_database WHERE datistemplate = false;')  
        elif connections.type == 2:  # SQLServer
            databases = False # TODO
        
        databases = external_session.execute( qry ).fetchall()
        
        print("Verificando os Databases [qtde "+ str(len(databases)) +"] do HOST: "+connections.name) 
        # Insert the database names into the databases table in the local database
        
        for _database in databases:
            db_name = _database[0]
            
            # ignore database of systems
            if db_name in (db_name_ignore_per_type[connections.type] if connections.type in db_name_ignore_per_type else []):
                continue
            
            print("Atualizando DATABASE: "+db_name) 
            
            result = database.get_by_like_and_id(Databases, 'name', db_name, 'id_host', host_id)
            if len(result)>0:
                db_id = result[0].id
                print("DATABASE JA EXISTENTE: "+db_name) 
            else:
                db_id = database.add_instance(Databases, name=db_name, id_host=host_id, type=0)
                print("DATABASE NOVO: "+db_name) 
                        
            # Get all tables names from each external database
            if connections.type == 0 or connections.type == 1 : #MySQL and #postgres
                tables = external_session.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = :db_name'), {'db_name': db_name}).fetchall()  
            elif connections.type == 2:  # SQLServer
                tables = False # TODO
            
            print("Verificando as tabelas [qtde "+ str(len(tables)) +"] do DATABASE: "+db_name) 
            # Insert the table names into the tables table in the local table
            for table in tables:
                table_name = table[0]
                print("Atualizando TABELA: "+table_name) 
                
                result = database.get_by_like_and_id(Tables, 'name', table_name, 'id_database', db_id)
                if len(result)>0:
                    print("TABELA JA EXISTENTE: "+table_name) 
                    table_id = result[0].id
                else:
                    table_id = database.add_instance(Tables, name=table_name, id_database=db_id, type=0)
                    print("TABELA NOVA: "+table_name) 
        
        return json.dumps('Synchosts successful!'), 200
    except Exception as ex:
        print(ex)
        return json.dumps('Fail'), 200
