from flask import Blueprint, request, abort, render_template, Markup, flash, url_for, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import redirect
from chronos.libs.flask_helpers import redirect_url
from chronos.libs.json2html import json2html
from chronos.libs import tools
from chronos.model import ApiKey
from chronos import data_helper, db, config, log
from chronos.web.forms import ApiKeyForm, ProfileForm
import json

# Define blueprint and navigation menu
user = Blueprint('user', __name__)


@user.route('/')
@login_required
def index():
    return render_template('index.html')


@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.theme.data = current_user.theme or 'moon-base-alpha'

    if form.validate_on_submit():
        current_user.email = request.form.get('email')
        current_user.username = request.form.get('username')
        if request.form.get('password'):
            current_user.password = generate_password_hash(request.form.get('password'), method='sha256')
        current_user.theme = request.form.get('theme')
        # save theme to a cookie
        resp = make_response(redirect(redirect_url()))
        resp.set_cookie('chronos-preference-theme', current_user.theme)
        current_user.save(db.session)
        return resp

    return render_template('profile.html', form=form)


@user.route('/api-key/add', methods=['GET', 'POST'])
@login_required
def create_api_key():
    form = ApiKeyForm()
    if form.validate_on_submit():
        user_id = current_user.id
        exchange_id = request.form.get('exchange_id')
        public_key = request.form.get('public_key')
        private_key = request.form.get('private_key')

        api_key = ApiKey.query.filter_by(user_id=user_id, exchange_id=exchange_id, public_key=public_key).first()

        if api_key:  # leave a message if the public key already exists
            flash(Markup('Public key already exists.'))
            return redirect(url_for('user.create_api_key'))

        # noinspection PyArgumentList
        new_api_key = ApiKey(user_id=user_id,
                             exchange_id=exchange_id,
                             public_key=public_key,
                             private_key=generate_password_hash(private_key, method='sha256'))
        # add the new user to the database
        new_api_key.save(db.session)
        return redirect('/api-key/')
    return render_template('add.html', form=form, action=url_for('user.create_api_key'), title="Add API key pair")


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
