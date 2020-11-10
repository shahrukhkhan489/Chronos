import logging
import os
import subprocess
import sys
import threading
from time import sleep
from subprocess import check_output
from chronos import data_helper
from chronos import config, log


def start_flask():
    import manage
    manage.run()


def list_ngrok():
    log.info(check_output(["ngrok", "http", "5000"], shell=True))


def list_pagekite():
    # TODO implement pagekite after they have migrated to Python 3
    # see https://pagekite.net/downloads
    # log.info('pagekite not implemented')
    filename = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "pagekite.py"
    pagekite = subprocess.run(["python", filename, "timelyart.pagekite.me"], stdout=sys.stdout, stderr=sys.stderr)
    log.info("The exit code was: %d" % pagekite.returncode)
    # log.info(check_output(["python", filename, "timelyart.pagekite.me"], shell=True, text=True))


def main():
    from chronos.libs import tools
    password = config.get('security', 'webhook_password')
    key = ""
    if password:
        key = tools.get_token(password)

    # test_kraken()

    output = "{'exchange': '{{exchange}}', 'type': 'limit', 'side': 'buy', 'quantity': 1, 'symbol': '{{ticker}}', 'price': {{close}}, 'key': '" + key + "'}"
    print()
    log.info("Example webhook message: {}".format(output))
    print()
    # start a thread with the server
    # log.info("creating server")
    threading.Thread(target=start_flask).start()
    sleep(1)
    # print(useless_cat_call.stdout)
    threading.Thread(target=list_pagekite()).start()
    log.info("server listed with pagekite")
    # threading.Thread(target=list_ngrok).start()
    # log.info("server listed with ngrok")


def test_kraken():
    print(data_helper.get_open_orders('kraken'))
    print(data_helper.get_closed_orders('kraken'))


main()
