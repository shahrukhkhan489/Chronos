import os
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from chronos.libs import tools

config = tools.get_config()
log = tools.create_log()
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))

app = Flask(__name__)
if config.has_option('postgresql', 'host') and config.has_option('postgresql', 'database') and config.has_option('postgresql', 'user') and config.has_option('postgresql', 'password'):
    uri = 'postgresql://{}:{}@{}/{}'.format(config.get('postgresql', 'user'), config.get('postgresql', 'password'), config.get('postgresql', 'host'), config.get('postgresql', 'database'))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
log.info("test")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    webhook_password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_webhook_password(self, webhook_password):
        self.password_hash = generate_password_hash(webhook_password)

    def check_webhook_password(self, webhook_password):
        return check_password_hash(self.password_hash, webhook_password)

    def __repr__(self):
        return '<User %r>' % self.username


class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    # ccxt_name = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return '<Exchange %r>' % self.name


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String, nullable=True)
    api_secret_hash = db.Column(db.String(128), nullable=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('user', lazy=True))

    def set_api_secret(self, api_secret):
        self.api_secret_hash = generate_password_hash(api_secret)

    def check_api_secret(self, api_secret):
        return check_password_hash(self.password_hash, api_secret)

    def __repr__(self):
        return '<APIKey %r>' % self.api_key


def create():
    print('create')
    db.create_all()


def delete():
    print('drop')
    db.drop_all()


def init():
    os.system('db init')


class Update(Command):

    def run(self):
        os.system('python model.py db migrate')
        os.system('python model.py db upgrade')


if __name__ == '__main__':
    manager.add_command('update', Update())
    manager.run()
