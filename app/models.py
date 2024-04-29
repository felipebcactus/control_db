import flask_sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin

db = flask_sqlalchemy.SQLAlchemy()

host_types = {
    0: "MySQL",
    1: "Postgres",
    2: "SQL Server"
}

db_name_ignore_per_type = {
    0: ['information_schema','mysql','sys','performance_schema']
}

user_types = {
    0: "Admin - Both",
    1: "System Only",
    2: "DB Only"
}

user_status = {
    0: "Inactive",
    1: "Active"
}

table_type = {
    0: "Restrict",
    1: "Open"
}

session_status_type = {
    -1: 'New',
    0: 'Waiting Approve',
    1: 'Approved' ,
    2: 'Revoked'  ,
    3: 'Expired' 
}
class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(255))
    type = db.Column(db.Integer)
    status = db.Column(db.Integer, default=0) # 0-Inactive; 1-Active
    parent = db.Column(db.Integer, default=None)
    created_at  = db.Column(db.DateTime(), default=db.func.now())
    updated_at = db.Column(db.DateTime(), onupdate=db.func.now())

class Hosts(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.Integer)
    ipaddress = db.Column(db.String(255))
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
    def serialize(self):
        return {
            "name" : self.name,
            "database": Databases.query.filter_by(id=self.id_database).first().serialize(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Sessions(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
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
            "name": self.name,
            "user": Users.query.filter_by(id=self.user).first().username,
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


class ExternalConnectionByHostId():
    
    def getConn(host_id):
        from . import database
        
        # Get the host with the given host_id
        connections = database.get_id(Hosts, host_id)
        # print(connections.__dict__)
        
        db_username = connections.username
        db_password = connections.password
        db_host = connections.ipaddress
        db_port = connections.port
        
        # Connect to the external database
        # Create a connection string
        connection_string = {}
        connection_string[0] = f'mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}'
        connection_string[1] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}'
        connection_string[2] = f'mssql+pyodbc://{db_username}:{db_password}@{db_host}:{db_port}?driver=ODBC+Driver+17+for+SQL+Server'
        
        # print("Iniciando atualização do HOST: "+connections.name) 
        # print("Connection string: "+connection_string[connections.type])

        # Create an engine instance
        external_engine = create_engine(connection_string[connections.type])
        external_session = sessionmaker(bind=external_engine)
        external_session = external_session()
        
        return external_session