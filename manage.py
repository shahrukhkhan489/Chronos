"""
This file is here to be able to do updates to the database without reverting to DROP TABLE, i.e. to use Flask-Migrate
"""
import os
import subprocess
from chronos import create_app, manager, log

app = create_app()


def seed():
    """Add seed data to the database."""
    from chronos.model import Exchange, get_or_create
    print("Updating records... ", end="")
    # Exchanges
    exchange = get_or_create(Exchange, name='Kraken')
    exchange.ccxt_name = 'kraken'
    exchange.class_name = None
    exchange.save()
    exchange = get_or_create(Exchange, name='Kraken Futures')
    exchange.ccxt_name = None
    exchange.class_name = 'KrakenFutures'
    exchange.save()
    print("OK")


def init():
    file = os.path.abspath(__file__)
    try:
        print("Setting up Flask-Migrate ... ")
        result = subprocess.run(['python', file, 'db', 'init'], shell=True)
        if result.returncode == 0:
            print("OK")
        else:
            print("FAILED")
    except Exception as e:
        log.exception(e)


def migrate():
    file = os.path.abspath(__file__)
    try:
        print("Generating migration script from model... ")
        # result = subprocess.run(['dir'], shell=True)
        result = subprocess.run(['python', file, 'db', 'migrate'], shell=True)
        if result.returncode == 0:
            print("OK")
        else:
            print("FAILED")
    except Exception as e:
        log.exception(e)


def upgrade():
    file = os.path.abspath(__file__)
    try:
        print("Executing migration script to database... ")
        result = subprocess.run(['python', file, 'db', 'upgrade'], shell=True)
        if result.returncode == 0:
            print("OK")
        else:
            print("FAILED")
    except Exception as e:
        log.exception(e)


@manager.command
def update():
    migrate()
    upgrade()
    seed()
    print("===============================")
    print("Database Update Complete")


def first_time_setup():
    init()
    file = os.path.abspath(__file__)
    try:
        subprocess.run(['python', file, 'db', 'update'], shell=True)
    except Exception as e:
        log.exception(e)


if app.config['DATABASE_CREATED']:
    first_time_setup()

if __name__ == '__main__':
    from chronos import model
    model.manage()


def run():
    app.run()
