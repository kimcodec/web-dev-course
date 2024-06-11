from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

from app import db_connector
import psycopg
from psycopg.rows import namedtuple_row
from users_policy import UsersPolicy

bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пройдите авторизацию для доступа к этому ресурсу'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)


class User(UserMixin):
    def __init__(self, user_id, user_login, role_id):
        self.id = user_id
        self.user_login = user_login
        self.role_id = role_id

    def is_admin(self):
        return self.role_id == current_app.config['ADMIN_ROLE_ID']

    def can(self, action, user=None):
        policy = UsersPolicy(user)
        return getattr(policy, action, lambda: False)()


def load_user(user_id):
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("SELECT id, login, role_id FROM users WHERE id = %s;", (user_id,))
        user = cursor.fetchone()
    if user is not None:
        return User(user.id, user.login, user.role_id)
    return None


def check_for_privelege(action):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user = None
            if 'user_id' in kwargs.keys():
                with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
                    cursor.execute("SELECT * FROM users WHERE id = %s;", (kwargs.get('user_id'),))
                    user = cursor.fetchone()
            if not (current_user.is_authenticated and current_user.can(action, user)):
                flash('Недостаточно прав для доступа к этой странице', 'warning')
                return redirect(url_for('index'))
            return function(*args, **kwargs)

        return wrapper

    return decorator


@bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me', None) == 'on'
        with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(
                "SELECT id, login, role_id FROM users WHERE login = %s AND password = CAST(SHA256(%s) AS VARCHAR)",
                (login, password)
            )
            user = cursor.fetchone()

            if user:
                flash('Авторизация прошла успешно', 'success')
                login_user(User(user.id, user.login, user.role_id), remember=remember_me)
                next_url = request.args.get('next', url_for('index'))
                return redirect(next_url)
            flash('Неправильный логин или пароль', 'danger')
    return render_template('login.html')


@bp.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        login = request.form['username']
        password = request.form['password']
        fist_name = request.form['first_name']
        last_name = request.form['last_name']
        remember_me = request.form.get('remember_me', None) == 'on'
        with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
            try:
                cursor.execute(
                    "INSERT INTO users (login, password, first_name, last_name, role_id) "
                    "VALUES (%s, CAST(SHA256(%s) AS VARCHAR), %s, %s, %s) RETURNING *",
                    (login, password, fist_name, last_name, current_app.config['USER_ROLE_ID'])
                )
                user = cursor.fetchone()
                db_connector.connect().commit()
                flash('Учетная запись успешно создана', 'success')

                if user:
                    flash('Авторизация прошла успешно', 'success')
                    login_user(User(user.id, user.login, user.role_id), remember=remember_me)
                    next_url = request.args.get('next', url_for('index'))
                    return redirect(next_url)
            except psycopg.Error as e:
                current_app.logger.error(e)
                db_connector.connect().rollback()
    return render_template('register.html')


@bp.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из учетной записи!', 'success')
    return redirect(url_for('index'))
