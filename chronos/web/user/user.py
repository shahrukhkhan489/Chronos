import base64

from flask import Blueprint, request, abort, render_template, Markup, flash, url_for, make_response, session, jsonify
from flask_login import login_required, current_user, login_user, mixins
from werkzeug import local
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
from cryptography.fernet import Fernet, InvalidToken
from chronos.data_helper import get_ccxt_exchange
from chronos.libs.flask_helpers import redirect_url, set_boolean_values
from chronos.libs.json2html import json2html
from chronos.libs import tools
from chronos.libs.tools import decrypt, encrypt, utf8len
from chronos.model import ApiKey, Exchange, User
from chronos import data_helper, db, config, log, csrf
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

    # set the form's data with current_user's data
    user_profile = User.query.filter_by(id=current_user.id).first()

    form.username.data = user_profile.username
    form.email.data = user_profile.email
    form.theme.data = user_profile.theme or 'moon-base-alpha'
    set_boolean_values(form, user_profile)

    # add 'was-validated' tag to form in order to display hints and/or (error) messages
    if request.method == 'POST':
        form.extra_classes = "was-validated"

    if form.validate_on_submit():
        user_profile.email = request.form.get('email')
        user_profile.username = request.form.get('username')
        user_profile.email_verified = request.form.get('email_verified') is not None
        user_profile.theme = request.form.get('theme')

        # save new password (if any) and generate a new token if necessary
        old_password = request.form.get('current_password')
        new_password = request.form.get('password')
        if new_password:
            if check_password_hash(user_profile.password, old_password):

                if 'token' in session and session['token']:
                    # hash the new password
                    user_profile.password = generate_password_hash(new_password, method='sha256')
                    # hash the user's token data with the new password, so that we may continue to use the token to for decryption and encryption purposes
                    session_token = decrypt(session['token'], old_password)
                    user_profile.token = encrypt(session_token, new_password)
                    session['token'] = decrypt(user_profile.token, new_password)
                else:
                    flash("Your session is transpired. You have been logged out for security reasons.", "danger")
                    redirect(url_for('auth.logout'))
            else:
                flash("Invalid password", "danger")
                return redirect(url_for('user.profile'))
        # save model
        user_profile.save()

        # save theme to a cookie
        resp = make_response(redirect(redirect_url()))
        resp.set_cookie('chronos-preference-theme', user_profile.theme)
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
                             private_key=encrypt(private_key, session['token']))
        # add the new user to the database
        new_api_key.save()
        return redirect('/api-key/')
    return render_template('add.html', form=form, action=url_for('user.create_api_key'), title="Add API key pair")


@user.route('/orders', methods=['GET'])
@login_required
def orders():
    exchanges = db.session.query(Exchange).filter_by(enabled=True)
    open_orders = {}
    closed_orders = {}

    for exchange in exchanges:
        log.info(exchange.name)
        for api_key in exchange.api_keys:
            if api_key.user_id == current_user.id and api_key.exchange_id == exchange.id:
                resp = data_helper.get_open_orders(exchange)
                log.info(resp)
                html = json2html.convert(json=json.dumps(resp), table_attributes='class="table table-condensed table-bordered table-hover"')
                if html:
                    open_orders[exchange.name] = Markup(html)
                if exchange.ccxt_name in ['binance']:
                    resp = data_helper.get_orders(exchange)
                else:
                    resp = data_helper.get_closed_orders(exchange)
                html = json2html.convert(json=json.dumps(resp), table_attributes='class="table table-condensed table-bordered table-hover"')
                if html:
                    closed_orders[exchange.name] = Markup(html)

    return render_template('orders.html', open_orders=open_orders, closed_orders=closed_orders)


@user.route('/balance', methods=['GET'])
@login_required
def balance():
    exchanges = db.session.query(Exchange).filter_by(enabled=True)
    balances = dict()
    open_orders = dict()
    threshold = 0.01    # only show balance higher than the threshold

    # fields: symbol, balance, exchange
    # search field
    # sort symbol, exchange
    for exchange in exchanges:
        # base_pairs = ["USD", "EUR"]
        # if str(exchange.name).lower().index("kraken") >= 0:
        #     base_pairs.append("XBT")
        # else:
        #     base_pairs.append("BTC")
        # market_pairs = []
        # if exchange.is_ccxt():
        #     markets = get_ccxt_exchange(exchange).markets
        #     for market_pair, info in markets.items():
        #         market_pairs.append(market_pair)
        # log.info(market_pairs)
        # log.info(exchange.name)

        for api_key in exchange.api_keys:
            if api_key.user_id == current_user.id and api_key.exchange_id == exchange.id:
                exchange_open_orders = {}
                try:
                    resp = data_helper.get_balance(exchange)
                    for k, v in resp['total'].items():
                        # if k not in base_pairs and v >= threshold:
                        if v >= threshold:
                            balances["{}.{}".format(k, exchange.name)] = v
                            # asset_open_orders = None
                            # for base in base_pairs:
                            #     try:
                            #         asset_open_orders = data_helper.get_open_orders(exchange, "{}/{}".format(k, base))
                            #     except Exception as e:
                            #         log.exception(e)
                            #     log.info(asset_open_orders)
                            #     open_orders["{}.{}".format(k, exchange.name)] = asset_open_orders
                except Exception as e:
                    log.exception(e)
                try:
                    resp = data_helper.get_open_orders(exchange)
                    for order_data in resp:
                        log.info(order_data)
                        if 'info' in order_data and 'descr' in order_data['info']:
                            pair = order_data['info']['descr']['pair']
                            exchange_open_orders[pair] = []
                            log.info(pair)
                            exchange_open_orders[pair].append({
                                'id': order_data['id'],
                                'order_status': order_data['info']['status'],
                                'exchange': exchange.name,
                                'pair': pair,
                                'type': order_data['info']['descr']['type'],
                                'amount': order_data['info']['vol'],
                                'price': order_data['info']['descr']['price'],
                                'order_type': order_data['info']['descr']['ordertype'],
                                'leverage': order_data['info']['descr']['leverage'],
                                'filled': order_data['info']['vol_exec'],
                                'created': order_data['info']['opentm'],
                                'start': order_data['info']['starttm'],
                                'expire': order_data['info']['expiretm']
                            })
                    open_orders[exchange.name] = exchange_open_orders
                    log.info(open_orders[exchange.name])
                except Exception as e:
                    log.exception(e)
                # resp = dict((k, v)
                # resp = {k + '.' + exchange.name: v for k, v in resp.items()}
                # for key, value in resp['total'].items():
                #     key = key + '.' + exchange.name
                # result = {**result, **resp}
                break

                # log.info(resp['total'])
                # html = json2html.convert(json=json.dumps(resp), table_attributes='class="table table-condensed table-bordered table-hover"')
                # balance = resp['total']
                # log.info(type(resp['total']))
                # result = dict((k, v) for k, v in resp['total'].items() if v >= 0.01)
                # result = {**result, **dict((k, v) for k, v in resp['total'].items() if v >= threshold)}
                # html += '<p>' + json2html.convert(json=json.dumps(result), collapsible_sub_tables=False, table_attributes='class="table-bordered table-hover"') + '</p>'
                # log.info(html)
                # if html:
                #     balances[exchange.name] = Markup(html)

    html = '<table class="table table-condensed table-bordered table-hover js-table"><thead><tr><th>Asset</th><th>Balance</th><th>Exchange</th></tr></thead><tbody>'
    for key, value in balances.items():
        log.info(key)
        asset, exchange_name = key.rsplit('.', 1)
        # exchange = get_ccxt_exchange(exchange_name)
        # open_orders = data_helper.get_open_orders(exchange, asset)
        # log.info(open_orders)
        html += '<tr><td>{}</td><td><span style="float: right">{}</span></td><td>{}</td></tr>'.format(asset, value, exchange_name)
    html += '</tbody></table>'
    return render_template('balance.html', balances=balances, open_orders=open_orders, html=html)


@user.route('/positions')
@login_required
def positions():
    exchanges = db.session.query(Exchange).filter_by(enabled=True)
    open_positions = {}
    closed_orders = {}
    for exchange in exchanges:
        open_positions[exchange.name] = Markup(json2html.convert(
            json=json.dumps(data_helper.get_open_positions(exchange)),
            table_attributes='class="table table-condensed table-bordered table-hover"'))
        # closed_orders[exchange.name] = Markup(json2html.convert(
        #     json=json.dumps(data_helper.get_closed_orders(exchange)),
        #     table_attributes='class="table table-condensed table-bordered table-hover"'))
    return render_template('orders.html', open_positions=open_positions)


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
@csrf.exempt
def webhook():
    """
    Expected request data in JSON format for CCXT:
        chronos_id: int
        exchange: Kraken, Binance, etc
        symbol: symbol or asset ID
        quantity: int
        side: buy or sell
        type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER
        price: limit price

    Expected request data in JSON format for Alpaca:
        chronos_id: int
        exchange: Alpaca or AlpacaPaper
        symbol: symbol or asset ID
        quantity: int
        side: buy or sell
        type: market, limit, stop, stop_limit or trailing_stop
        limit_price: str of float
        stop_price: str of float
        time_in_force: day, gtc, opg, cls, ioc, fok
        client_order_id:
        extended_hours: bool. If true, order will be eligible to execute in premarket/afterhours.
        order_class: simple, bracket, oco or oto
        take_profit: dict with field "limit_price" e.g {"limit_price": "298.95"}
        stop_loss: dict with fields "stop_price" and "limit_price" e.g {"stop_price": "297.95", "limit_price": "298.95"}
        trail_price: str of float
        trail_percent: str of float
        instructions: str

    """
    # password = config.get('authentication', 'password')
    password = config.get('security', 'webhook_password')
    if request.method == 'POST':
        # Parse the string data from tradingview into a python dict
        log.info(request.get_data(as_text=True))
        data = data_helper.parse_webhook(request.get_data(as_text=True))

        # Check that the key is correct
        if (not password) or tools.get_token(password) == data['key']:
            if not ('pwd' in data):
                return "Missing attribute 'pwd'", 401
            if not ('chronos_id' in data):
                return "Missing attribute 'chronos_id'", 401
            # If the user has no session, create a session token
            pwd = data['pwd']
            if isinstance(current_user, mixins.AnonymousUserMixin) or isinstance(current_user, local.LocalProxy):
                session_token = None
                webhook_user = User.query.filter_by(id=data['chronos_id']).first()
                login_user(webhook_user, force=True)

                # load/generate token to encrypt sensitive date with
                if webhook_user.token is None:  # if the user doesn't have a token, then save it
                    session_token = Fernet.generate_key()
                    webhook_user.token = encrypt(session_token, pwd)
                    webhook_user.save()
                else:
                    try:
                        session_token = decrypt(webhook_user.token, pwd)
                    except InvalidToken as e:
                        log.exception(e)
                        pass

                session['token'] = session_token
                assert ('token' in session and session['token'])

            # log.info('POST Received: {}'.format(data))
            data_helper.send_order(data)
            return '', 200
        else:
            abort(403)
    else:
        abort(400)
