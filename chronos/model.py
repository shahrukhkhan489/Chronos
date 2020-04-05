import os

from flask_script import Command
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, manager
from flask_login import UserMixin
# from manage import db, manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    is_anonymous = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    ccxt_name = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return '<Exchange %r>' % self.name


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String, nullable=True)
    api_secret_hash = db.Column(db.String(128), nullable=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('api_key_exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('api_key_user', lazy=True))

    def set_api_secret(self, api_secret):
        self.api_secret_hash = generate_password_hash(api_secret)

    def check_api_secret(self, api_secret):
        return check_password_hash(self.password_hash, api_secret)

    def __repr__(self):
        return '<APIKey %r>' % self.api_key


class ExchangeData(db.Model):
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
        return '<Exchange %r>' % self.exchange.name


def create():
    db.create_all()


def delete():
    db.drop_all()


class Update(Command):

    def run(self):
        os.system('python model.py db migrate')
        os.system('python model.py db upgrade')


def manage():
    manager.add_command('update', Update())
    manager.run()
