import sys
import hashlib
import os

from flask import Blueprint, render_template, flash, session, request, redirect, url_for, current_app
from flask_login import current_user, login_required
from auth import check_for_privelege
from app import db_connector
import psycopg
from werkzeug.utils import secure_filename
from psycopg.rows import namedtuple_row

bp = Blueprint('furniture', __name__, url_prefix='/furniture')


def save_furniture_image(cursor, image):
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        file_content = image.read()
        md5_hash = hashlib.md5(file_content).hexdigest()
        mime_type = image.mimetype

        cursor.execute("""
            INSERT INTO furniture_image(file_name, mime_type, md5_hash)
            VALUES (%s, %s, %s) RETURNING id
        """, (filename, mime_type, md5_hash,))
        cover_id = cursor.fetchone().id

        file_path = os.path.join('static/images', filename)

        image.seek(0)
        image.save(file_path)

        return cover_id
    return None


def load_furniture(furniture_id):
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("SELECT furniture.id, name, price, description, file_name "
                       "FROM furniture LEFT JOIN furniture_image "
                       "ON furniture.image_id = furniture_image.id WHERE furniture.id = %s", (furniture_id,))
        furniture = cursor.fetchone()
        return furniture


def load_all_furniture(name='', min_price=0, max_price=sys.maxsize):
    result = []
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("SELECT furniture.id, name, price, description, file_name "
                       "FROM furniture LEFT JOIN furniture_image "
                       "ON furniture.image_id = furniture_image.id WHERE price >= %s AND price <= %s",
                       (min_price, max_price,))
        furniture = cursor.fetchall()
        for fur in furniture:
            if name.lower() in fur.name.lower():
                result.append(fur)
        return result


@bp.route('/<int:furniture_id>/view')
def view(furniture_id):
    return render_template('furniture/view.html', furniture=load_furniture(furniture_id))


@bp.route('/redirect_back')
def redirect_back():
    previous_url = session.get('previous_url', None)
    if previous_url:
        return redirect(previous_url)
    else:
        return redirect(url_for('index'))


@bp.route('/<int:furniture_id>/buy', methods=['GET', 'POST'])
def buy(furniture_id):
    user_id = current_user.get_id()
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("SELECT * FROM carts WHERE furniture_id = %s AND user_id = %s", (furniture_id, user_id))
        if cursor.fetchone() is not None:
            flash('Товар уже есть в корзине', 'danger')
            return render_template('index.html', furniture=load_all_furniture())
        try:
            cursor.execute("INSERT INTO carts(user_id, furniture_id) VALUES (%s, %s)", (user_id, furniture_id,))
            flash('Товар успешно добавлен', 'success')
            db_connector.connect().commit()
        except psycopg.DatabaseError:
            flash('Ошибка при добавлении', 'danger')
            db_connector.connect().rollback()
    return render_template('index.html', furniture=load_all_furniture())


@bp.route('/<int:furniture_id>/delete', methods=['POST'])
@check_for_privelege('delete')
def delete(furniture_id):
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        try:
            cursor.execute("DELETE FROM furniture WHERE id = %s", (furniture_id,))
            flash('Товар был удален', 'success')
            db_connector.connect().commit()
        except psycopg.DatabaseError:
            flash('Ошибка при удалении', 'danger')
            db_connector.connect().rollback()

    return redirect(url_for('admin_panel.index'))


@bp.route('/new', methods=['GET', 'POST'])
@check_for_privelege('create')
def create():
    if request.method == 'POST':
        fields = ('name', 'price', 'description')
        furniture_data = {field: request.form[field] or None for field in fields}

        if not furniture_data['price'].isdigit():
            flash('Цена должна быть целым числом', 'danger')
            return redirect(url_for('furniture.create'))
        with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
            try:
                furniture_image = request.files.get('furniture-image')
                image_id = save_furniture_image(cursor, furniture_image)

                cursor.execute("INSERT INTO furniture(name, price, description, image_id) VALUES (%s, %s, %s, %s)",
                               (furniture_data['name'], furniture_data['price'],
                                furniture_data['description'], image_id,))
                db_connector.connect().commit()
                flash('Товар успешно добавлен', 'success')
            except BaseException:
                db_connector.connect().rollback()
                flash('Произошла ошибка при создании товара', 'danger')
        return redirect(url_for('admin_panel.index'))
    return render_template('furniture/new.html')


@bp.route('/<int:furniture_id>/edit', methods=['GET', 'POST'])
@check_for_privelege('update')
def update(furniture_id):
    furniture_data = load_furniture(furniture_id)
    if furniture_data is None:
        flash('Товара нет в базе данных', 'danger')
        return redirect(url_for('admin_panel.index'))
    if request.method == 'POST':
        fields = ['name', 'price', 'description']
        furniture_data = {field: request.form[field] or None for field in fields}
        with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
            try:
                cursor.execute("UPDATE furniture SET name = %s, price = %s, description = %s WHERE id = %s",
                               (furniture_data['name'], furniture_data['price'],
                                furniture_data['description'], furniture_id,))

                furniture_image = request.files.get('furniture-image')
                if furniture_image:
                    image_id = save_furniture_image(cursor, furniture_image)
                    cursor.execute("UPDATE furniture SET image_id = %s WHERE id = %s",
                                   (image_id, furniture_id,))

                db_connector.connect().commit()
                flash('Товар успешно изменен', 'success')
                return redirect(url_for('admin_panel.index'))
            except psycopg.DatabaseError:
                flash('Ошибка при изменении товара', 'danger')
                db_connector.connect().rollback()

    return render_template('furniture/edit.html', furniture_data=furniture_data)
