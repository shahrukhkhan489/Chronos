import alpaca_trade_api
from alpaca_trade_api.common import URL
from chronos import log


class Alpaca:
    alpaca_rest = None
    api_key = ''
    api_secret = ''
    base_url = ''
    markets = []

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = URL('https://api.alpaca.markets')

    def create_order(self, data: dict):
        """
        Create a new order.
        :see https://alpaca.markets/docs/trading-on-alpaca/orders
        :param data: dictionary with any or all of the following keys:
                - symbol: symbol or asset ID
                - quantity: int
                - side: buy or sell
                - order_type: market, limit, stop, stop_limit or trailing_stop
                - limit_price: str of float
                - stop_price: str of float
                - time_in_force: day, gtc, opg, cls, ioc, fok
                    day: for one day during regular trading hours
                    gtc: good until cancelled
                    opg: executes only during market opening auction
                    cls: executes only during market closing auction
                    ioc: immediate or cancel, order needs to be immediately filled; any unfilled portion will be cancelled
                    fok: fill or kill, order needs to be completely filled, otherwise it is cancelled
                - client_order_id:
                - extended_hours: bool. If true, order will be eligible to execute in premarket/afterhours.
                - order_class: simple, bracket, oco or oto
                    bracket: entry, take profit and stop loss order in one
                    oco: one cancels other, e.g. take profit and stoploss; only used in combination with a bracket order
                    oto: one triggers other, e.g. if you only want a stoploss attached to the position; only used in combination with a bracket order
                - take_profit: dict with field "limit_price" e.g {"limit_price": "298.95"}
                - stop_loss: dict with fields "stop_price" and "limit_price" e.g {"stop_price": "297.95", "limit_price": "298.95"}
                - trail_price: str of float
                - instructions: str
                - trail_percent: str of float
        """
        symbol = None
        param_info = ''
        if 'symbol' in data:
            symbol = data['symbol']
            param_info += "symbol: {}".format(symbol)
        quantity = None
        if 'quantity' in data:
            quantity = data['quantity']
            param_info += ", quantity: {}".format(quantity)
        side = None
        if 'side' in data:
            side = data['side']
            param_info += ", side: {}".format(side)
        order_type = None
        if 'type' in data:
            order_type = data['type']
            param_info += ", order_type: {}".format(order_type)
        limit_price = None
        if 'limit_price' in data:
            limit_price = data['limit_price']
            param_info += ", limit_price: {}".format(limit_price)
        stop_price = None
        if 'stop_price' in data:
            stop_price = data['stop_price']
            param_info += ", stop_price: {}".format(stop_price)
        time_in_force = None
        if 'time_in_force' in data:
            time_in_force = data['time_in_force']
            param_info += ", time_in_force: {}".format(time_in_force)
        client_order_id = None
        if 'client_order_id' in data:
            client_order_id = data['client_order_id']
            param_info += ", client_order_id: {}".format(client_order_id)
        extended_hours = None
        if 'extended_hours' in data:
            extended_hours = data['extended_hours']
            param_info += ", extended_hours: {}".format(extended_hours)
        order_class = None
        if 'order_class' in data:
            order_class = data['order_class']
            param_info += ", order_class: {}".format(order_class)
        take_profit = None
        if 'take_profit' in data:
            take_profit = data['take_profit']
            param_info += ", take_profit: {}".format(take_profit)
        stop_loss = None
        if 'stop_loss' in data:
            stop_loss = data['stop_loss']
            param_info += ", stop_loss: {}".format(stop_loss)
        trail_price = None
        if 'trail_price' in data:
            trail_price = data['trail_price']
            param_info += ", trail_price: {}".format(trail_price)
        trail_percent = None
        if 'trail_percent' in data:
            trail_percent = data['trail_percent']
            param_info += ", trail_percent: {}".format(trail_percent)
        instructions = None
        if 'instructions' in data:
            instructions = data['instructions']
            param_info += ", instructions: {}".format(instructions)

        if 'type' == 'market':
            limit_price = None

        result = None
        try:
            result = self.alpaca_rest.submit_order(symbol, quantity, side, order_type, time_in_force, limit_price,
                                                   stop_price, client_order_id, extended_hours, order_class,
                                                   take_profit, stop_loss, trail_price, instructions, trail_percent)
        except Exception as e:
            log.info(param_info)
            log.exception(e)
        return result

    def load_markets(self):
        try:
            response = self.alpaca_rest.list_assets(status='active')
            for i in range(len(response)):
                asset = response[i].__dict__['_raw']
                self.markets.append("{}:{}".format(asset['exchange'], asset['symbol']))
        except Exception as e:
            log.exception(e)


class AlpacaPaper(Alpaca):

    def __init__(self, api_key, api_secret):
        super().__init__(api_key, api_secret)
        self.base_url = URL('https://paper-api.alpaca.markets')
        self.alpaca_rest = alpaca_trade_api.REST(self.api_key, self.api_secret, base_url=self.base_url)

    def load_markets(self):
        super(AlpacaPaper, self).load_markets()
