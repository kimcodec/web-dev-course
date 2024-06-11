import sys

from flask import Flask, render_template, request, session
from postgres import DBConnector

app = Flask(__name__, template_folder='templates')
application = app
app.config.from_pyfile('config.py')

db_connector = DBConnector(app)

from orders import bp as orders_bp
from cart import bp as cart_bp
from auth import bp as auth_bp, init_login_manager
from admin_panel import bp as admin_panel_bp
from furniture import bp as furniture_bp, load_all_furniture

app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(furniture_bp)
app.register_blueprint(admin_panel_bp)
init_login_manager(app)


@app.route('/')
def index():
    session['previous_url'] = request.url

    name = request.args.get('name', '', type=str)
    min_price = request.args.get('min_price', 0, type=int)
    max_price = request.args.get('max_price', sys.maxsize, type=int)

    furniture = load_all_furniture(name=name, min_price=min_price, max_price=max_price)
    return render_template('index.html', furniture=furniture)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
