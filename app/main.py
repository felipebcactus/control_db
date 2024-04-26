from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from . import database

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    if current_user.type==0:
        return render_template('index.html', name=current_user.name)
    else:
        return redirect(url_for('main.user_get_access'))

@main.route('/user/getAccess/', methods=['GET'])
def user_get_access():
    return render_template('userGetAccess.html',  user_id=current_user.id, name=current_user.name)