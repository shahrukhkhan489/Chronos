import ast
import ccxt
from . import config, log


def send_order(data):
    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """
    result = False
    exchange = get_exchange(data['exchange'])
    if exchange:
        try:
            # the following issue: ccxt expects symbols to be [base]/[quote] (e.g. BTC/USD) whilst TradingView returns [base][quote] (e.g. BTCUSD)
            data['symbol'] = sanitize_symbol(data['symbol'], exchange)
            log.info('sending {}:{} {} {} {} {}'.format(data['exchange'].upper(), data['symbol'], data['type'], data['side'], data['amount'], calc_price(data['price'])))
            if symbol_exists(data['symbol'], exchange):
                # Send the order to the exchange, using the values from the tradingview alert.
                result = exchange.create_order(data['symbol'], data['type'], data['side'], data['amount'], calc_price(data['price']))
        # except ccxt.errors.AuthenticationError as auth_exception:
        #     log.warn("{} returned: invalid key/secret pair".format(data['exchange']))
        # except ccxt.errors.BadSymbol as bad_symbol_exception:
        #     log.exception("{} return: pair {} not listed".format(data['exchange'], data['symbol']))
        # This is the last step, the response from the exchange will tell us if it made it and what errors pop up if not.
        except Exception as e:
            log.exception(e)
        log.info('{}: {}'.format(data['exchange'], result))
    return result


def get_open_positions(exchange, symbol=None, since=None, limit=None):
    """
    Get the (latest) open orders.
    :param exchange:
    :param symbol:
    :param since:
    :param limit:
    :return: the response from the exchange.
    """
    result = False
    exchange = get_exchange(exchange)
    if exchange:
        log.info(exchange.id)
        try:
            symbol = sanitize_symbol(symbol, exchange)
            if symbol is None or symbol_exists(symbol, exchange):
                result = exchange.fetch_my_trades(symbol, since, limit)
        except Exception as e:
            log.exception(e)
    return result


def get_open_orders(exchange, symbol=None, since=None, limit=None):
    """
    Get the (latest) open orders.
    :param exchange:
    :param symbol:
    :param since:
    :param limit:
    :return: the response from the exchange.
    """
    result = False
    exchange = get_exchange(exchange)
    if exchange:
        try:
            symbol = sanitize_symbol(symbol, exchange)
            if symbol is None or symbol_exists(symbol, exchange):
                result = exchange.fetch_open_orders(symbol, since, limit)
        except Exception as e:
            log.exception(e)
    return result


def get_closed_orders(exchange, symbol=None, since=None, limit=None):
    """
    Get the (latest) closed orders.
    :param exchange:
    :param symbol:
    :param since:
    :param limit:
    :return: the response from the exchange.
    """
    result = False
    exchange = get_exchange(exchange)
    if exchange:
        try:
            symbol = sanitize_symbol(symbol, exchange)
            if symbol is None or symbol_exists(symbol, exchange):
                result = exchange.fetch_closed_orders(symbol, since, limit)
        except Exception as e:
            log.exception(e)
    return result


def get_order_by_id(exchange, order_id):
    """
    Get an order by id
    :param exchange:
    :param order_id:
    :return: the response from the exchange.
    """
    result = False
    exchange = get_exchange(exchange)
    if exchange:
        try:
            result = exchange.fetch_order(order_id)
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
    result = False
    exchange = get_exchange(exchange)
    if exchange:
        try:
            result = exchange.fetch_orders_by_ids(order_ids)
        except Exception as e:
            log.exception(e)
    return result


def is_exchange_enabled(exchange_name):
    """
    Check is the exchange is defined in chronos.cfg and if it is enabled
    :param exchange_name:
    :return: True, if defined and enabled
    """
    result = False
    settings = get_exchange_settings(exchange_name)
    if not settings:
        log.warn("exchange {} unspecified in chronos.cfg. Call ignored.".format(exchange_name))
    else:
        result = settings['enabled']
        if not result:
            log.warn("exchange {} disabled. Call ignored.".format(exchange_name))
    return result


def parse_webhook(webhook_data):
    """
    This function takes the string from tradingview and turns it into a python dict.
    :param webhook_data: POST data from tradingview, as a string.
    :return: Dictionary version of string.
    """
    data = ast.literal_eval(webhook_data)
    return data


def get_exchange(exchange_name):
    """
    Get the ccxt exchange based upon it's name
    :param exchange_name:
    :return: the ccxt exchange
    """
    exchange = None
    settings = get_exchange_settings(exchange_name)
    if is_exchange_enabled(exchange_name):
        if exchange_name.lower() == 'coinbase':
            exchange = ccxt.coinbase({
                # Inset your API key and secrets for exchange in question.
                'apiKey': settings['key'],
                'secret': settings['secret'],
                'enableRateLimit': settings['enableRateLimit'],
            })
        elif exchange_name.lower() == 'kraken':
            exchange = ccxt.kraken({
                # Inset your API key and secrets for exchange in question.
                'apiKey': settings['key'],
                'secret': settings['secret'],
                'enableRateLimit': settings['enableRateLimit'],
            })
        else:
            log.info("{} hasn't been implemented yet. Order ignored.".format(exchange_name))
        if exchange:
            # load the markets (this is cached so will be loaded only once, after which the exchange's cache will be used)
            exchange.load_markets()
    return exchange


def get_exchange_settings(exchange_name):
    """
    Checks if an exchange is present in the chronos.cfg, it's key/secret pair is set and if it is enabled
    :param exchange_name: the name of the exchange, e.g. Kraken (case insensitive)
    :return: exchange settings if present, false otherwise
    """
    exchange = exchange_name.lower()
    settings = False
    if config.has_section(exchange):
        settings = {'key': None, 'secret': None, 'enabled': False, 'enableRateLimit': True}
        if config.has_option(exchange, 'key'):
            settings['key'] = config.get(exchange, 'key')
        if config.has_option(exchange, 'secret'):
            settings['secret'] = config.get(exchange, 'secret')
        if config.has_option(exchange, 'enabled'):
            settings['enabled'] = config.get(exchange, 'enabled')

    return settings


def symbol_exists(symbol: str, exchange: ccxt.Exchange):
    """
    Checks if a symbol exists for a given exchange
    :param symbol: a ccxt style symbol, i.e. [base]/[quote] (e.g. BTC/USD)
    :param exchange: a ccxt exchange
    :return: True, if the symbol exists
    """
    exists = False
    if symbol and exchange:
        exists = symbol in exchange.markets
        if not exists:
            exchange.load_markets(True)
            exists = symbol in exchange.markets
        if not exists:
            log.exception("{}: pair {} not listed".format(exchange.id, symbol))
            log.warn()
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


def sanitize_symbol(symbol, exchange):
    """
    Converts TradingView style symbols [base][quote] (e.g. BTCUSD) to ccxt style symbols [base]/[quote] (e.g. BTC/USD)
    :param symbol:
    :param exchange:
    :return: ccxt style symbol
    """
    if symbol is None:
        return symbol
    if symbol not in exchange.markets:
        for i in range(len(symbol)):
            ccxt_symbol = "{}/{}".format(str(symbol)[0:i], str(symbol)[i:len(symbol)])
            if ccxt_symbol in exchange.markets:
                return ccxt_symbol

    # apparently we couldn't find the symbol; maybe the symbol got recently added; reload markets and try a 2nd time
    exchange.load_markets(True)
    if symbol not in exchange.markets:
        for i in range(len(symbol)):
            ccxt_symbol = "{}/{}".format(str(symbol)[0:i], str(symbol)[i:len(symbol)])
            if ccxt_symbol in exchange.markets:
                return ccxt_symbol

    return symbol
