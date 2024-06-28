import flask_sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
from datetime import datetime
import uuid


db = flask_sqlalchemy.SQLAlchemy()

host_types = {
    0: "MySQL",
    1: "Postgres",
    2: "SQL Server"
}

db_name_ignore_per_type = {
    0: ['information_schema','mysql','sys','performance_schema','innodb','tmp','awsdms_control']
}

db_username_deny = {
    0: ['bet7k','%']
}

db_config_exceptions = {
    0: ['db_user_prefix','hours_user_session']
}

user_types = {
    0: "Admin",
    1: "User",
    2: "Approver"
}

user_status = {
    0: "Inactive",
    1: "Active"
}

table_type = {
    0: "Restrict",
    1: "Open"
}

table_type_restricted_default = {
    0: ['auth_config', 'users', 'user_documents']
}

session_status_type = {
    -1: 'New',
    0: 'Waiting for approval',
    1: 'Approved' ,
    2: 'Revoked'  ,
    3: 'Expired'  ,
    4: 'DB Removed',
    5: 'Denied' 
}

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(255))
    type = db.Column(db.Integer)
    status = db.Column(db.Integer, default=0) # 0-Inactive; 1-Active; -1 -soft deleted
    parent = db.Column(db.Integer, default=None)
    days_default_access = db.Column(db.Integer, default=1)
    created_at  = db.Column(db.DateTime(), default=db.func.now())
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(255), nullable=False)
    operation = db.Column(db.String(255), nullable=False)
    field_name = db.Column(db.String(255), nullable=True)
    old_value = db.Column(db.Text(), nullable=True)
    new_value = db.Column(db.Text(), nullable=True)
    changed_by = db.Column(db.Integer, nullable=False)
    changed_at = db.Column(db.DateTime(), default=db.func.now())

class Hosts(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.Integer)
    ipaddress = db.Column(db.String(255))
    ipaddress_read = db.Column(db.String(255))
    port = db.Column(db.Integer)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at  = db.Column(db.DateTime(), default=db.func.now())
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())
    def serialize(self):
        return {
            "name": self.name,
            "type": host_types[self.type],
            "ipaddress": self.ipaddress,
            "port": self.port,
            "username": self.username,
            "user": Users.query.filter_by(id=self.id_user).first().serialize(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Databases(db.Model):
    __tablename__ = 'databases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    id_host = db.Column(db.Integer, db.ForeignKey('hosts.id'))
    type = db.Column(db.Integer)
    created_at  = db.Column(db.DateTime(), default=db.func.now())
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())   
    def serialize(self):
        return {
            "name": self.name,
            "type": self.type,
            "host": Hosts.query.filter_by(id=self.id_host).first().serialize(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        

class Tables(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    id_database = db.Column(db.Integer, db.ForeignKey('databases.id'))
    type = db.Column(db.Integer)
    created_at  = db.Column(db.DateTime(), default=db.func.now())
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())  
    __table_args__ = (db.UniqueConstraint('name', 'id_database', name='uix_tables_name_id_database'),)
    def serialize(self):
        return {
            "name" : self.name,
            "database": Databases.query.filter_by(id=self.id_database).first().serialize(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Config(db.Model):
    __tablename__ = 'config'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255))
        
class Sessions(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    writer = db.Column(db.Integer, default=0)
    approver = db.Column(db.Integer, default=None)
    access_start = db.Column(db.DateTime())
    access_end = db.Column(db.DateTime())
    status = db.Column(db.Integer, default=0)
    request_date = db.Column(db.DateTime(), default=db.func.now())
    approve_date = db.Column(db.DateTime(), default=None)
    description = db.Column(db.Text, default=None)
    datatree = db.Column(db.Text, default=None)
    password = db.Column(db.String(255), default=None)
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "user": Users.query.filter_by(id=self.user).first().username,
            "writer": self.writer,
            "approver": (Users.query.filter_by(id=self.approver).first() or None).username if self.approver else None,
            "access_start": self.access_start.strftime("%Y-%m-%d %H:%M"),
            "access_end" : self.access_end.strftime("%Y-%m-%d %H:%M") if self.access_end else None,
            "status": session_status_type[self.status],
            "request_date": self.request_date.strftime("%Y-%m-%d %H:%M"),
            "approve_date": (self.approve_date.strftime("%Y-%m-%d %H:%M") if self.approve_date else None),
            "description": self.description,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M")
        }


class SessionsHosts(db.Model):
    __tablename__ = 'sessions_hosts'
    id_session = db.Column(db.Integer, db.ForeignKey('sessions.id'), primary_key=True)
    id_host = db.Column(db.Integer, db.ForeignKey('hosts.id'), primary_key=True)
    create_date = db.Column(db.DateTime(), default=db.func.now())


class UsersPermissionsHosts(db.Model):
    __tablename__ = 'users_permissions_hosts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'))

    user = db.relationship('Users', backref=db.backref('hosts_associations'))
    host = db.relationship('Hosts', backref=db.backref('users_associations'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'host_id'),
    )


class ExternalConnectionByHostId:
    
    def __init__(self):
        self.external_engine = None
        self.external_session = None
        self.instance_id = uuid.uuid4()  # Cria um ID único para a instância

    def getConn(self, host_id, _database=False):
        from . import database
        
        # Get the host with the given host_id
        connections = database.get_id(Hosts, host_id)
        
        db_username = connections.username
        db_password = connections.password
        db_host = connections.ipaddress
        db_port = connections.port
        
        # Create a connection string
        connection_string = {
            0: f'mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}',
            1: f'postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}' + ("/" + _database if _database else ''),
            2: f'mssql+pyodbc://{db_username}:{db_password}@{db_host}:{db_port}?driver=ODBC+Driver+17+for+SQL+Server'
        }

        strconn = connection_string[connections.type]
        print(datetime.now().strftime("%Y-%m-%d %H:%M"))
        print(f'[{self.instance_id}] Conectando ao HOST: ' + db_host)
        
        # Create an engine instance
        self.external_engine = create_engine(strconn)
        _session = sessionmaker(bind=self.external_engine)
        self.external_session = _session()
        
        print(f'[{self.instance_id}] Conectado...')
        return self.external_session

    def closeConn(self):
        if self.external_session:
            self.external_session.close()
            self.external_session = None
            print(f'[{self.instance_id}] Sessão fechada.')
        if self.external_engine:
            self.external_engine.dispose()
            self.external_engine = None
            print(f'[{self.instance_id}] Engine fechada.')