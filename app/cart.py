from math import ceil
from collections import namedtuple
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import db_connector
import psycopg
from psycopg.rows import namedtuple_row

bp = Blueprint('cart', __name__, url_prefix='/cart')
MAX_PER_PAGE = 10

cart_tuple = namedtuple('cart_tuple', 'user_id furniture_id name price')


@bp.route('/')
@login_required
def index():
    session['previous_url'] = request.url

    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute('SELECT * FROM carts WHERE user_id=%s LIMIT %s OFFSET %s',
                       (user_id, MAX_PER_PAGE, (page - 1) * MAX_PER_PAGE,))
        cart_rows = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) as count FROM carts WHERE user_id=%s LIMIT %s OFFSET %s',
                       (user_id, MAX_PER_PAGE, ((page - 1) * MAX_PER_PAGE),))
        count_row = cursor.fetchone()
        record_count = count_row.count

        cart = []
        for product in cart_rows:
            cursor.execute("SELECT f.name as name, f.price as price FROM carts a "
                           "JOIN furniture f on a.furniture_id = f.id "
                           "WHERE f.id = %s", (product.furniture_id,))
            product_row = cursor.fetchone()

            cart.append(cart_tuple(user_id=product.user_id, furniture_id=product.furniture_id,
                                   name=product_row.name, price=product_row.price))

        page_count = ceil(record_count / MAX_PER_PAGE)
        pages = range(max(1, page - 3), min(page_count, page + 3) + 1)
    return render_template('cart/cart.html', cart=cart,
                           page=page, pages=pages, page_count=page_count)


@bp.route('/purchase')
@login_required
def purchase():
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        try:
            cursor.execute("INSERT INTO orders(user_id) VALUES(%s) RETURNING id",
                           (current_user.id,))
            order_id = cursor.fetchone().id

            cursor.execute("INSERT INTO orders_furniture(order_id, furniture_id) "
                           "SELECT %s, furniture_id FROM carts WHERE user_id = %s",
                           (order_id, current_user.id,))
            cursor.execute("DELETE FROM carts WHERE user_id = %s", (current_user.id,))

            flash('Заказ успешно сформирован', 'success')
            db_connector.connect().commit()
        except psycopg.DatabaseError:
            flash('Ошибка при создании заказа', 'danger')
            db_connector.connect().rollback()
    return redirect(url_for('cart.index'))


@bp.route('/<int:furniture_id>/delete', methods=['POST'])
@login_required
def delete(furniture_id):
    with db_connector.connect() as cursor:
        try:
            cursor.execute('DELETE FROM carts WHERE user_id=%s AND furniture_id=%s',
                           (current_user.id, furniture_id))
            db_connector.connect().commit()
            flash('Товар был удален', 'success')
        except psycopg.DatabaseError:
            flash('Ошибка при удалении', 'danger')
            db_connector.connect().rollback()
    return redirect(url_for('cart.index'))
