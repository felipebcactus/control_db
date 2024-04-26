from flask import Flask
from flask_login import LoginManager
from sqlalchemy import event
from werkzeug.security import generate_password_hash

from .models import db
from . import config

def create_app():
    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_CONNECTION_URI
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.app_context().push()
    db.init_app(flask_app)
    db.create_all()
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(flask_app)

    from .models import Users
            
    @event.listens_for(Users.__table__, 'after_create')
    def create_admin_user(*args, **kwargs):
        db.session.add(Users(name="Admin", email="admin@admin.com", type=0, status=1, password=generate_password_hash("123!@#", method='pbkdf2:sha256')))
        db.session.commit()
    if Users.query.count() == 0:
        create_admin_user()
    
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return Users.query.get(int(user_id))
    
    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    flask_app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    flask_app.register_blueprint(main_blueprint)
    
    return flask_app
