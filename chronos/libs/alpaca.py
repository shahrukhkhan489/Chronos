import alpaca_trade_api
from alpaca_trade_api.common import URL


class Alpaca:
    alpaca_rest = None
    api_key = ''
    api_secret = ''
    base_url = ''

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = URL('https://api.alpaca.markets')
        self.alpaca_rest = alpaca_trade_api.REST(self.api_key, self.api_secret, base_url=self.base_url)

    def create_order(self,
                     symbol: str,
                     quantity: int,
                     side: str,
                     order_type: str,
                     limit_price: str = None,
                     stop_price: str = None,
                     time_in_force: str = 'gtc',
                     client_order_id: str = None,
                     extended_hours: bool = None,
                     order_class: str = None,
                     take_profit: dict = None,
                     stop_loss: dict = None,
                     trail_price: str = None,
                     trail_percent: str = None,
                     instructions: str = None):
        """
        :param symbol: symbol or asset ID
        :param quantity: int
        :param side: buy or sell
        :param order_type: market, limit, stop, stop_limit or trailing_stop
        :param limit_price: str of float
        :param stop_price: str of float
        :param time_in_force: day, gtc, opg, cls, ioc, fok
        :param client_order_id:
        :param extended_hours: bool. If true, order will be eligible to execute
               in premarket/afterhours.
        :param order_class: simple, bracket, oco or oto
        :param take_profit: dict with field "limit_price" e.g
               {"limit_price": "298.95"}
        :param stop_loss: dict with fields "stop_price" and "limit_price" e.g
               {"stop_price": "297.95", "limit_price": "298.95"}
        :param trail_price: str of float
        :param trail_percent: str of float
        :param instructions: str
        """
        return self.alpaca_rest.submit_order(symbol, quantity, side, order_type, time_in_force, limit_price, stop_price,
                                             client_order_id, extended_hours, order_class, take_profit, stop_loss,
                                             trail_price, instructions, trail_percent)


class AlpacaPaper(Alpaca):

    def __init__(self, api_key, api_secret):
        super().__init__(api_key, api_secret)
        self.base_url = URL('https://paper-api.alpaca.markets')
        self.alpaca_rest = alpaca_trade_api.REST(self.api_key, self.api_secret, base_url=self.base_url)