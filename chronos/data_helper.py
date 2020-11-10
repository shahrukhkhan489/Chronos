import ast
import importlib
# import inspect
from datetime import datetime
# from types import FrameType
# from typing import cast
import ccxt
from .libs import alpaca
import cfscrape
# import jsonpickle as jsonpickle
from ccxt.kraken import kraken
from ccxt.binance import binance
from flask import session, json
from flask_login import current_user, AnonymousUserMixin
from . import log, db
from .libs.tools import find_files_and_folders, get_immediate_subdirectories, is_int, merge
from .model import Exchange

user_objects = dict()


def send_order(data):
    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """
    user_id = None
    if 'chronos_id' in data:
        user_id = data['chronos_id']

    result = False
    if is_int(data['exchange']):
        exchange = db.session.query(Exchange).filter_by(id=data['exchange']).first()
    else:
        exchange = db.session.query(Exchange).filter_by(name=data['exchange']).first()

    if exchange and exchange.is_ccxt():
        try:
            # the following issue: ccxt expects symbols to be [base]/[quote] (e.g. BTC/USD) whilst TradingView returns [base][quote] (e.g. BTCUSD)
            data['symbol'] = sanitize_symbol(data['symbol'], exchange)
            log.info('sending {}:{} {} {} {} {}'.format(data['exchange'].upper(), data['symbol'], data['type'], data['side'], data['quantity'], calc_price(data['price'])))
            if symbol_exists(data['symbol'], exchange):
                # Send the order to the exchange, using the values from the tradingview alert.
                result = exchange.create_order(data['symbol'], data['type'], data['side'], data['quantity'], calc_price(data['price']))
        # except ccxt.errors.AuthenticationError as auth_exception:
        #     log.warn("{} returned: invalid key/secret pair".format(data['exchange']))
        # except ccxt.errors.BadSymbol as bad_symbol_exception:
        #     log.exception("{} return: pair {} not listed".format(data['exchange'], data['symbol']))
        # This is the last step, the response from the exchange will tell us if it made it and what errors pop up if not.
        except Exception as e:
            log.exception(e)
        log.info('{}: {}'.format(data['exchange'], result))
    elif exchange.class_name == 'Alpaca' or exchange.class_name == 'AlpacaPaper':
        _alpaca = get_alpaca_exchange(exchange, user_id)
        result = _alpaca.create_order(data['symbol'], data['quantity'], data['side'], data['type'], calc_price(data['price']))
        log.info('{}: {}'.format(data['exchange'], result))
    return result


def get_data(*args):
    method_params = dict(args[0])
    del method_params['since']
    # method = cast(FrameType, cast(FrameType, inspect.currentframe()).f_back).f_code.co_name
    # exchange: Exchange = method_params['exchange']
    data = None
    # ExchangeData.query.filters(exchange_id=exchange.id, user_id=current_user.id, method=method, method_params=method_params)

    log.info(method_params)
    # log.info(method)
    return data


def get_open_positions(exchange: Exchange, symbol=None, since=None, limit=None):
    """
    Get the (latest) open orders.
    :param exchange:
    :param symbol:
    :param since:
    :param limit:
    :return: the response from the exchange.
    """
    result = {}
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange)
        if ccxt_exchange:
            try:
                symbol = sanitize_symbol(symbol, exchange)
                if symbol is None or symbol_exists(symbol, exchange):
                    result = ccxt_exchange.fetch_my_trades(symbol, since, limit)
            except Exception as e:
                log.exception(e)
    return result


def get_balance(exchange, since=None, limit=None):
    """
    Get the user balance.
    :param exchange:
    :param since:
    :param limit:
    :return: a list of symbols with their corresponding balance
    """
    if type(since) is datetime:
        since = since.timestamp()
    if limit is None:
        limit = exchange.limit
    extra_params = {}

    # get closed orders from the cache so we aren't unnecessarily requesting the exchange for data
    balance = []
    try:
        balance = update_balance(exchange, 'fetch_balance', since, limit)
    except Exception as e:
        log.exception(e)
    return balance


def get_open_orders(exchange, market=None, since=None, limit=None):
    """
    Get the (latest) open orders.
    :param exchange: exchange name used by ccxt
    :param market: e.g. BTCUSD
    :param since:
    :param limit:
    :return: the response from the exchange.
    """
    if type(since) is datetime:
        since = since.timestamp()
    if limit is None:
        limit = exchange.limit
    extra_params = {}

    # get closed orders from the cache so we aren't unnecessarily requesting the exchange for data
    open_orders = []
    try:
        update_orders(exchange, 'fetch_open_orders', open_orders, market, since, limit, extra_params)
    except Exception as e:
        log.exception(e)
    return open_orders


def get_orders(exchange, symbol=None, since: datetime = None, limit=None):
    """

    :param exchange:
    :param symbol:
    :param since: unix timestamp in milliseconds, or a datetime object
    :param limit:
    :return:
    """
    if type(since) is datetime:
        since = since.timestamp()
    if limit is None:
        limit = exchange.limit
    extra_params = {}

    # get closed orders from the cache so we aren't unnecessarily requesting the exchange for data
    orders = []
    cache = exchange.get_cache(current_user.id)
    if cache.closed_orders:
        orders = json.loads(cache.closed_orders)

    if update_orders(exchange, 'fetch_orders', orders, symbol, since, limit, extra_params):
        closed_orders = []
        if exchange.is_ccxt():
            for order in orders:
                if order['status'] == 'closed':
                    closed_orders.append(order)
        cache.update(closed_orders=json.dumps(closed_orders)).save()

    return orders


def get_closed_orders(exchange, symbol=None, since: datetime = None, limit=None, update=False):
    """

    :param exchange:
    :param symbol: e.g. BTCUSD
    :param since: unix timestamp in milliseconds, or a datetime object
    :param limit:
    :param update:
    :return:
    """
    if type(since) is datetime:
        since = since.timestamp()
    if limit is None:
        limit = exchange.limit
    extra_params = {}

    # get closed orders from the cache so we aren't unnecessarily requesting the exchange for data
    closed_orders = []
    cache = exchange.get_cache(current_user.id)
    if cache.closed_orders:
        closed_orders = json.loads(cache.closed_orders)
        log.debug('loaded closed orders from cache')
    else:
        update = True

    if update and update_orders(exchange, 'fetch_closed_orders', closed_orders, symbol, since, limit, extra_params):
        log.debug('updating closed orders')
        cache.update(closed_orders=json.dumps(closed_orders)).save()

    return closed_orders


def update_balance(exchange, method, since=None, limit=None):
    """
    Get the user's balance from an exchange
    :param exchange:
    :param method:
    :param since:
    :param limit:
    :return: the balance
    """
    result = []
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange)
        # log.info("{} is of type {}".format(exchange.ccxt_name, type(ccxt_exchange)))
        log.info("{}.{}".format(type(ccxt_exchange), method))
        if since is None:
            since = ccxt_exchange.parse8601('2015-01-01 00:00:00Z')
        if since is datetime:
            since = since.timestamp()
        try:
            # dt = datetime.fromtimestamp(since / 1000)
            # log.info("{} from {}".format(method, dt))
            previous_since = None
            count = 0
            while since < ccxt_exchange.milliseconds() and since != previous_since:
                previous_since = since
                class_method = 'ccxt_exchange.'+method
                log.info(class_method)
                # get the data from the exchange
                balance = eval(class_method)()
                log.info(balance)
                # update the exchange's cache with the information
                if len(balance):
                    result = balance
                    count += len(balance)
                    # since = max(orders[0]['timestamp'], orders[len(orders) - 1]['timestamp'])+1
                    # # log.info(since)
                    # for i in range(len(orders)):
                    #     found = False
                    #     for j in range(len(current_orders)):
                    #         if current_orders[j]['id'] == orders[i]['id']:
                    #             current_orders[j] = current_orders[i]
                    #             found = True
                    #             orders_updated = True
                    #     if not found:
                    #         current_orders.append(orders[i])
                    #         orders_updated = True
                    #     # log.info("found order {}? {}".format(orders[i]['id'], found))
                else:
                    break
            log.info('balance updated')

        except Exception as e:
            log.exception(e)
    return result


def update_orders(exchange, method, current_orders, symbol=None, since=None, limit=None, extra_params=None):
    """
    Get orders from the exchange by API call, then update current_orders
    :param exchange:
    :param method:
    :param current_orders: array of known orders. May be empty, i.e. []
    :param symbol:
    :param since:
    :param limit:
    :param extra_params:
    :return: True, when orders were updated
    """
    orders_updated = False

    if exchange.is_ccxt() and (symbol is None or symbol_exists(symbol, exchange)):
        ccxt_exchange = get_ccxt_exchange(exchange)
        # log.info("{} is of type {}".format(exchange.ccxt_name, type(ccxt_exchange)))
        log.info("{}.{}".format(type(ccxt_exchange), method))
        if since is None:
            if len(current_orders):
                since = max(current_orders[0]['timestamp'], current_orders[len(current_orders) - 1]['timestamp'])+1
            else:
                since = ccxt_exchange.parse8601('2015-01-01 00:00:00Z')
        elif since is datetime:
            since = since.timestamp()

        try:
            dt = datetime.fromtimestamp(since / 1000)
            # log.info("{} from {}".format(method, dt))
            previous_since = None
            count = 0
            while since < ccxt_exchange.milliseconds() and since != previous_since:
                previous_since = since
                class_method = 'ccxt_exchange.'+method
                # log.info(class_method)
                # get the data from the exchange
                orders = eval(class_method)(symbol, since, limit, extra_params)
                # log.info(orders)
                # exit(0)
                # update the exchange's cache with the information
                if len(orders):
                    count += len(orders)
                    since = max(orders[0]['timestamp'], orders[len(orders) - 1]['timestamp'])+1
                    # log.info(since)
                    for i in range(len(orders)):
                        found = False
                        for j in range(len(current_orders)):
                            if current_orders[j]['id'] == orders[i]['id']:
                                current_orders[j] = current_orders[i]
                                found = True
                                orders_updated = True
                        if not found:
                            current_orders.append(orders[i])
                            orders_updated = True
                        # log.info("found order {}? {}".format(orders[i]['id'], found))
                else:
                    break
            log.info('updated {} orders from {}'.format(count, dt))
            # log.info(current_orders)

        except Exception as e:
            log.exception(e)
    return orders_updated


def get_order_by_id(exchange: Exchange, order_id):
    """
    Get an order by id
    :param exchange:
    :param order_id:
    :return: the response from the exchange.
    """
    result = {}
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange)
        if ccxt_exchange:
            try:
                result = ccxt_exchange.fetch_order(order_id)
            except Exception as e:
                log.exception(e)
    return result


def get_orders_by_id(exchange, order_ids):
    """
    Get orders by id (max 20).
    :param exchange:
    :param order_ids:
    :return: the response from the exchange.
    """
    result = {}
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange)
        if ccxt_exchange:
            try:
                result = ccxt_exchange.fetch_orders_by_ids(order_ids)
            except Exception as e:
                log.exception(e)
    return result


def parse_webhook(webhook_data):
    """
    This function takes the string from tradingview and turns it into a python dict.
    :param webhook_data: POST data from tradingview, as a string.
    :return: Dictionary version of string.
    """
    data = ast.literal_eval(webhook_data)
    return data


def get_ccxt_exchange(exchange: Exchange, user_id=None):
    """
    Get the ccxt exchange based upon it's name
    :param exchange:
    :param user_id: int
    :return: the ccxt exchange
    """
    if not user_id:
        user_id = current_user.id

    if user_id not in user_objects:
        user_objects[user_id] = dict()
    if 'ccxt_exchanges' not in user_objects[user_id]:
        user_objects[user_id]['ccxt_exchanges'] = dict()

    if exchange.is_ccxt() and exchange.ccxt_name in ccxt.exchanges:
        if exchange.ccxt_name not in user_objects[user_id]['ccxt_exchanges']:
            settings = get_exchange_settings(exchange, user_id)
            if settings['bypassCloudflare']:
                ccxt_exchange = getattr(ccxt, exchange.ccxt_name)({
                    'session': cfscrape.create_scraper(),
                    'apiKey': settings['key'],
                    'secret': settings['secret'],
                    'enableRateLimit': settings['enableRateLimit'],
                })
            else:
                ccxt_exchange = getattr(ccxt, exchange.ccxt_name)({
                    'apiKey': settings['key'],
                    'secret': settings['secret'],
                    'enableRateLimit': settings['enableRateLimit'],
                })
            # module = importlib.import_module('ccxt.{}'.format(exchange.ccxt_name))
            # ccxt_class = getattr(module, exchange.ccxt_name)
            # ccxt_exchange = ccxt_class({
            #     'apiKey': settings['key'],
            #     'secret': settings['secret'],
            #     'enableRateLimit': settings['enableRateLimit'],
            # })
            ccxt_exchange.load_markets()
            user_objects[user_id]['ccxt_exchanges'][exchange.ccxt_name] = ccxt_exchange
    return user_objects[user_id]['ccxt_exchanges'][exchange.ccxt_name]


def get_alpaca_exchange(exchange: Exchange, user_id=None):
    """
    Get the ccxt exchange based upon it's name
    :param exchange: Exchange
    :param user_id: int
    :return: the ccxt exchange
    """
    if not user_id:
        user_id = current_user.id

    if user_id not in user_objects:
        user_objects[user_id] = dict()
    if 'exchanges' not in user_objects[user_id]:
        user_objects[user_id]['exchanges'] = dict()

    if exchange.class_name not in user_objects[user_id]['exchanges']:
        settings = get_exchange_settings(exchange, user_id)
        alpaca_exchange = getattr(alpaca, exchange.class_name)(settings['key'], settings['secret'])
        user_objects[user_id]['exchanges'][exchange.class_name] = alpaca_exchange
    return user_objects[user_id]['exchanges'][exchange.class_name]


def get_exchange_settings(exchange: Exchange, user_id=None):
    if not user_id:
        user_id = current_user.id
    if exchange.is_ccxt():
        settings = {'key': None,
                    'secret': None,
                    'enabled': True,
                    'enableRateLimit': exchange.enable_rate_limit,
                    'bypassCloudflare': exchange.bypass_cloudflare}
    else:
        settings = {'key': None,
                    'secret': None,
                    'enabled': True}

    for api_key in exchange.api_keys:
        if api_key.user_id == user_id:
            settings['key'] = api_key.public_key
            settings['secret'] = api_key.get_private_key(session['token'])
    return settings


def symbol_exists(symbol: str, exchange: Exchange):
    """
    Checks if a symbol exists for a given exchange
    :param symbol: a ccxt style symbol, i.e. [base]/[quote] (e.g. BTC/USD)
    :param exchange: a ccxt exchange
    :return: True, if the symbol exists
    """
    exists = False
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange)
        if ccxt_exchange and symbol:
            exists = symbol in ccxt_exchange.markets
            if not exists:
                ccxt_exchange.load_markets(True)
                exists = symbol in ccxt_exchange.markets
            if not exists:
                log.exception("{}: pair {} not listed".format(exchange.name, symbol))
    return exists


def calc_price(given_price):
    """
    Will use this function to calculate the price for limit orders.
    :return: calculated limit price
    """
    if given_price is None:
        price = given_price
    else:
        price = given_price
    return price


def sanitize_symbol(symbol, exchange: Exchange, user_id=None):
    """
    Converts TradingView style symbols [base][quote] (e.g. BTCUSD) to ccxt style symbols [base]/[quote] (e.g. BTC/USD)
    :param symbol:
    :param exchange:
    :param user_id: int
    :return: ccxt style symbol
    """
    if symbol is None:
        return symbol
    if exchange.is_ccxt():
        ccxt_exchange = get_ccxt_exchange(exchange, user_id)
        if ccxt_exchange and symbol not in exchange.markets:
            for i in range(len(symbol)):
                ccxt_symbol = "{}/{}".format(str(symbol)[0:i], str(symbol)[i:len(symbol)])
                if ccxt_symbol in ccxt_exchange.markets:
                    return ccxt_symbol

        # apparently we couldn't find the symbol; maybe the symbol got recently added; reload markets and try a 2nd time
        ccxt_exchange.load_markets(True)
        if symbol not in ccxt_exchange.markets:
            for i in range(len(symbol)):
                ccxt_symbol = "{}/{}".format(str(symbol)[0:i], str(symbol)[i:len(symbol)])
                if ccxt_symbol in ccxt_exchange.markets:
                    return ccxt_symbol

    return symbol


def get_themes():
    # find 'themes' directory recursively
    result = []
    dirs, files = find_files_and_folders('themes')
    for path in dirs:
        if path.endswith('\\themes'):
            result = get_immediate_subdirectories(path)
            break

    return result
