"""
This file is here to be able to do updates to the database without reverting to DROP TABLE, i.e. to use Flask-Migrate
"""
import os
import subprocess
from chronos import create_app, manager, log

app = create_app()


def update_records():
    """Add seed data to the database."""
    from chronos.model import get_or_create, Exchange
    print("Updating records... ", end="")
    # Exchanges
    get_or_create(Exchange, name='Kraken').update(ccxt_name='kraken', class_name=None).save()
    get_or_create(Exchange, name='Kraken Futures').update(ccxt_name=None, class_name='KrakenFutures').save()
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
    update_records()
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
