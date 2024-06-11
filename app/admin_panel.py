from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from furniture import load_all_furniture
from auth import check_for_privelege
from app import db_connector
import psycopg
from psycopg.rows import namedtuple_row
from users_policy import UsersPolicy

bp = Blueprint('admin_panel', __name__, url_prefix='/admin_panel')


@bp.route('/')
@login_required
@check_for_privelege('read')
def index():
    session['previous_url'] = request.url

    name = request.args.get('name', '', type=str)

    furniture = load_all_furniture(name=name)
    return render_template('admin_panel/admin_panel.html', furniture=furniture)