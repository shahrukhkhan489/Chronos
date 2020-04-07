from flask import Blueprint, request, abort, render_template, Markup
from flask_nav.elements import Navbar, View
from flask_login import login_required, current_user
from chronos import data_helper
from chronos import config, log, nav
from chronos.libs import tools
from chronos.libs.json2html import json2html
import json

# Define blueprint and navigation menu
user = Blueprint('user', __name__)
nav.register_element('user', Navbar('user',
                                    View('Home', 'auth.index'),
                                    View('Orders', 'user.orders'),
                                    View('Profile', 'user.profile'),
                                    View('Logout', 'auth.logout')))


@user.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=current_user.username)


@user.route('/orders')
@login_required
def orders():
    open_orders = json.dumps(data_helper.get_open_orders('kraken'))
    closed_orders = json.dumps(data_helper.get_closed_orders('kraken'))
    open_orders_table = Markup(json2html.convert(json=open_orders,
                                                 table_attributes='class="table table-condensed table-bordered table-hover"'))
    closed_orders_table = Markup(json2html.convert(json=closed_orders,
                                                   table_attributes='class="table table-condensed table-bordered table-hover"'))
    return render_template('orders.html', open_orders=open_orders_table, closed_orders=closed_orders_table)


@user.route('/open')
@login_required
def open_positions():
    open_orders = json.dumps(data_helper.get_open_orders('kraken'))
    closed_orders = json.dumps(data_helper.get_closed_orders('kraken'))
    open_orders_table = Markup(json2html.convert(json=open_orders,
                                                 table_attributes='class="table table-condensed table-bordered table-hover"'))
    closed_orders_table = Markup(json2html.convert(json=closed_orders,
                                                   table_attributes='class="table table-condensed table-bordered table-hover"'))
    return render_template('orders.html', open_orders=open_orders_table, closed_orders=closed_orders_table)


@user.route('/status')
def status():
    return render_template('index.html', message='online')


@user.route('/example/list')
def list_example():
    my_list = ['Alvin', 'Simon', 'Theodore']
    return render_template('index.html', list_example=my_list)


@user.route('/example/user/<username>')
def uri_example(username):
    return render_template('index.html', username=username)


@user.route('/webhook', methods=['POST'])
def webhook():
    password = config.get('authentication', 'password')
    if request.method == 'POST':
        # Parse the string data from tradingview into a python dict
        log.info(request.get_data(as_text=True))
        data = data_helper.parse_webhook(request.get_data(as_text=True))
        # Check that the key is correct
        if (not password) or tools.get_token(password) == data['key']:
            log.info(' [Alert Received] ')
            log.info('POST Received: {}'.format(data))
            data_helper.send_order(data)
            return '', 200
        else:
            abort(403)
    else:
        abort(400)
