import ast
import ccxt
from chronos.tools import tools

config = tools.get_config()
log = tools.create_log()
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))


def parse_webhook(webhook_data):

    """
    This function takes the string from tradingview and turns it into a python dict.
    :param webhook_data: POST data from tradingview, as a string.
    :return: Dictionary version of string.
    """

    data = ast.literal_eval(webhook_data)
    return data


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


def send_order(data):
    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """
    result = False
    settings = get_exchange_settings(data['exchange'])
    if not settings:
        log.info("exchange unspecified in chronos.cfg. Order ignored.")
    elif settings['enabled']:
        if data['exchange'].lower() == 'coinbase':
            exchange = ccxt.coinbase({
                # Inset your API key and secrets for exchange in question.
                'apiKey': settings['key'],
                'secret': settings['secret'],
                'enableRateLimit': settings['enableRateLimit'],
            })
        elif data['exchange'].lower() == 'kraken':
            exchange = ccxt.kraken({
                # Inset your API key and secrets for exchange in question.
                'apiKey': settings['key'],
                'secret': settings['secret'],
                'enableRateLimit': settings['enableRateLimit'],
            })
        else:
            log.info("{} hasn't been implemented yet. Order ignored.".format(data['exchange']))
            return result

        try:
            # load the markets (this is cached so will be loaded only once, after which the exchange's cache will be used)
            exchange.load_markets()
            # the following issue: ccxt expects symbols to be [base]/[quote] (e.g. BTC/USD) whilst TradingView returns [base][quote] (e.g. BTCUSD)
            if not data['symbol'] in exchange.markets:
                for i in range(len(data['symbol'])):
                    symbol = "{}/{}".format(str(data['symbol'])[0:i], str(data['symbol'])[i:len(data['symbol'])])
                    if symbol in exchange.markets:
                        data['symbol'] = symbol
                        break
            log.info('sending {}:{} {} {} {} {}'.format(data['exchange'].upper(), data['symbol'], data['type'], data['side'], data['amount'], calc_price(data['price'])))
            if data['symbol'] in exchange.markets:
                # Send the order to the exchange, using the values from the tradingview alert.
                result = exchange.create_order(data['symbol'], data['type'], data['side'], data['amount'], calc_price(data['price']))
            else:
                log.exception("{}: pair {} not listed".format(data['exchange'], data['symbol']))
        # except ccxt.errors.AuthenticationError as auth_exception:
        #     log.warn("{} returned: invalid key/secret pair".format(data['exchange']))
        # except ccxt.errors.BadSymbol as bad_symbol_exception:
        #     log.exception("{} return: pair {} not listed".format(data['exchange'], data['symbol']))
        # This is the last step, the response from the exchange will tell us if it made it and what errors pop up if not.
        except Exception as e:
            log.exception(e)
        log.info('{}: {}'.format(data['exchange'], result))
    else:
        log.info("ignoring order; exchange disabled")
    return result


def get_exchange_settings(exchange: str):
    """
    Checks if an exchange is present in the chronos.cfg, it's key/secret pair is set and if it is enabled
    :param exchange: the name of the exchange, e.g. Kraken (case insensitive)
    :return: exchange settings if present, false otherwise
    """
    global config
    config = tools.get_config()

    exchange = exchange.lower()
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
