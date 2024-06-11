from collections import namedtuple
from math import ceil

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db_connector
import psycopg
from psycopg.rows import namedtuple_row

bp = Blueprint('orders', __name__, url_prefix='/orders')
MAX_PER_PAGE = 10

Order = namedtuple('Order', 'id user_id total_price furniture_name datetime')


@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    user_id = current_user.get_id()
    with db_connector.connect().cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute('SELECT * FROM orders WHERE user_id=%s LIMIT %s OFFSET %s',
                       (user_id, MAX_PER_PAGE, (page - 1) * MAX_PER_PAGE,))
        orders = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) FROM orders WHERE user_id=%s', (user_id,))
        count = cursor.fetchone().count

        new_orders = []
        for order in orders:
            cursor.execute("SELECT c.name, c.price FROM orders a "
                           "JOIN orders_furniture b on a.id = b.order_id "
                           "JOIN furniture c on b.furniture_id = c.id WHERE a.id = %s", (order.id,))
            furniture = cursor.fetchall()

            total_price = 0
            name_lst = []
            for fur in furniture:
                total_price += fur.price
                name_lst.append(fur.name)
            name = ", ".join(name_lst) + "."

            new_order = Order(id=order.id, user_id=order.user_id, total_price=total_price,
                              furniture_name=name, datetime=order.datetime)
            new_orders.append(new_order)

        page_count = ceil(count / MAX_PER_PAGE)
        pages = range(max(1, page - 3), min(page_count, page + 3) + 1)
    current_app.logger.info(msg=f'page:{page}, pages:{pages}, page_count:{page_count}')
    return render_template('orders/orders.html', orders=new_orders,
                           page=page, pages=pages, page_count=page_count)


@bp.route('/<int:order_id>/delete', methods=['POST'])
@login_required
def delete(order_id):
    with db_connector.connect() as cursor:
        try:
            cursor.execute('DELETE FROM orders WHERE id = %s',
                           (order_id,))
            db_connector.connect().commit()
            flash('Заказ был удален', 'success')
        except psycopg.DatabaseError:
            flash('Ошибка при удалении', 'danger')
            db_connector.connect().rollback()
    return redirect(url_for('orders.index'))
