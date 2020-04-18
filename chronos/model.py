from sqlalchemy.sql import ClauseElement, text
from chronos import db, manager
# from chronos import log
from flask_login import UserMixin
from .libs.crud import CrudBase


def get_or_create(model, defaults=None, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        return instance


class User(UserMixin, CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    is_anonymous = db.Column(db.Boolean, nullable=False, server_default=text("False"))
    is_admin = db.Column(db.Boolean, nullable=False, server_default=text("False"))
    email_verified = db.Column(db.Boolean, nullable=False, server_default=text("False"))
    theme = db.Column(db.String())

    def __repr__(self):
        return self.username


class Exchange(CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    ccxt_name = db.Column(db.String)
    class_name = db.Column(db.String)
    api_keys = db.relationship('ApiKey', backref='exchange_api_keys')

    def __repr__(self):
        return self.name


class ApiKey(CrudBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_key = db.Column(db.String, nullable=False)
    private_key = db.Column(db.String(80), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('api_key_exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('api_key_user', lazy=True))

    def __repr__(self):
        return '{}.{}'.format(self.exchange.name, self.public_key)


class ExchangeData(CrudBase, db.Model):
    """
    Aggregates all data that comes from exchanges such as orders and positions
    """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.TIMESTAMP)
    request = db.Column(db.String)  # we might need to hash this since we don't want to see API key/secret information
    data = db.Column(db.UnicodeText)  # we might need LargeBinary here instead
    data_type = db.Column(db.String(20))  # open_orders, open_positions, closed_orders, closed_positions, etc
    data_type_is_open = db.Column(db.Boolean)  # open vs closed, i.e. 'open' orders/positions vs 'closed' orders/positions
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('exchange_data_exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('exchange_data_user', lazy=True))

    def __repr__(self):
        return '{}.data}'.format(self.exchange.name)


# class Trade(CrudBase, db.Model):


def create():
    db.create_all()


def delete():
    db.drop_all()


def manage():
    manager.run()
