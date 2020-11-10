from sqlalchemy import func
from sqlalchemy.sql import ClauseElement, text
from sqlalchemy_utils.types.json import json
from chronos import db, manager
# noinspection PyUnresolvedReferences
from chronos import log
from flask_login import UserMixin
from .libs.crud import CrudBase
from .libs.tools import decrypt


def get_or_create(model, defaults=None, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        # log.info(**params)
        instance = model(**params)
        return instance


class User(UserMixin, CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False, server_default=text("False"))
    is_admin = db.Column(db.Boolean, nullable=False, default=False, server_default=text("False"))
    email_verified = db.Column(db.Boolean, nullable=False, default=False, server_default=text("False"))
    theme = db.Column(db.String())
    token = db.Column(db.Binary, nullable=True)

    # relationships
    order_cache = db.relationship('Cache', order_by='Cache.exchange_id')

    def get_order_cache(self, exchange_id):
        for cache in self.order_cache:
            if cache.exchange_id == exchange_id:
                return cache
        return None

    def __repr__(self):
        return repr(self.username)


class Exchange(CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    limit = db.Column(db.Integer, nullable=False, default=20, server_default="20")  # maximum records returned per API call
    ccxt_name = db.Column(db.String)
    class_name = db.Column(db.String)
    bypass_cloudflare = db.Column(db.Boolean, nullable=False, default=False, server_default=text("False"))
    enable_rate_limit = db.Column(db.Boolean, nullable=False, default=True, server_default=text("True"))
    enabled = db.Column(db.Boolean, nullable=False, default=True, server_default=text("True"))

    # relationships
    api_keys = db.relationship('ApiKey', backref='exchange_api_keys')
    exchange_data = db.relationship('ExchangeData', backref='exchange_exchange_data', order_by='ExchangeData.since.desc()')
    caches = db.relationship('Cache', backref='exchange_cache', order_by='Cache.user_id')

    def __repr__(self):
        return self.name

    def is_ccxt(self):
        return not bool(self.ccxt_name is None or self.ccxt_name == "")

    def get_cache(self, user_id):
        for cache in self.caches:
            if cache.user_id == user_id:
                return cache
        Cache().update(user_id=user_id, exchange_id=self.id).save()
        for cache in self.caches:
            if cache.user_id == user_id:
                return cache
        return None


class Cache(db.Model):
    """
    Cache for user's closed orders and trades
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    closed_orders = db.Column(db.String, nullable=True)  # JSON
    closed_trades = db.Column(db.String, nullable=True)  # JSON

    # relationships
    user = db.relationship('User', backref=db.backref('cache_user', lazy=True))
    exchange = db.relationship('Exchange', backref=db.backref('cache__exchange', lazy=True))


class ApiKey(CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_key = db.Column(db.String, nullable=False)
    private_key = db.Column(db.Binary, nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # relationships
    exchange = db.relationship('Exchange', backref=db.backref('api_key_exchange', lazy=True))
    user = db.relationship('User', backref=db.backref('api_key_user', lazy=True))

    def __repr__(self):
        return '{}.{}'.format(self.exchange.name, self.public_key)

    def get_private_key(self, token):
        return decrypt(self.private_key, token).decode()


class ExchangeData(CrudBase, db.Model):
    """
    Aggregates all data that comes from exchanges such as orders and positions
    """
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, server_default=func.now(), nullable=False)
    method = db.Column(db.String, nullable=False)
    method_params = db.Column(db.String, nullable=True)
    since = db.Column(db.TIMESTAMP, nullable=True)  # unix timestamp
    data = db.Column(db.UnicodeText, nullable=False)  # we might need LargeBinary here instead
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # relationships
    exchange = db.relationship('Exchange', backref=db.backref('exchange_data_exchange', lazy=True))
    user = db.relationship('User', backref=db.backref('exchange_data_user', lazy=True))

    def __repr__(self):
        return '<ExchangeData {}>'.format(self.method_params)


# class Trade(CrudBase, db.Model):


def create():
    db.create_all()


def delete():
    db.drop_all()


def manage():
    manager.run()
