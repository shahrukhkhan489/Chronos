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


def tunnel():
    """
    Use a 3rd party process to open up Chronos to the cruel outside world
    :return:
    """
    result = False

    if 'pagekite' in config and 'enabled' in config['pagekite'] and config.getboolean('pagekite', 'enabled'):
        if 'path' in config['pagekite'] and config['pagekite']['path']:
            filepath = config.get("pagekite", "path")
        else:
            filepath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "pagekite.py"
        kite = ''
        if 'kite' in config['pagekite'] and config['pagekite']['kite']:
            kite = str(config.get("pagekite", "kite"))
        if filepath and kite:
            log.info('starting pagekite ...')
            try:
                threading.Thread(target=list_pagekite, args=[filepath, kite]).start()
                log.info('pagekite {} started'.format(kite))
                result = True
            except Exception as e:
                log.exception(e)
    elif 'ngrok' in config and 'enabled' in config['ngrok'] and config.getboolean('ngrok', 'enabled'):
        if 'path' in config['ngrok'] and config['ngrok']['path']:
            filepath = config.get("ngrok", "path")
        else:
            filepath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "ngrok"
        protocol = ''
        port = ''
        if 'protocol' in config['ngrok'] and config['ngrok']['protocol']:
            protocol = str(config.get('ngrok', 'protocol'))
        if 'port' in config['ngrok'] and config['ngrok']['port']:
            port = str(config.get('ngrok', 'port'))
        log.info('starting ngrok ...')
        try:
            threading.Thread(target=list_ngrok, args=[filepath, protocol, port]).start()
            log.info('ngrok started on {}://localhost:{}'.format(protocol, port))
            result = True
        except Exception as e:
            log.exception(e)
    else:
        log.warning('no 3rd party tunneling software is installed and is enabled in chronos.cfg')
    return result


def list_ngrok(filepath='ngrok', protocol='http', port='5000'):
    ngrok = subprocess.run([filepath, protocol, port], stdout=sys.stdout, stderr=sys.stderr, text=True)
    log.info("Ngrok stopped with exit code was: %d" % ngrok.returncode)
    # log.info(check_output([filepath, protocol, port], shell=True))
    # log.info(check_output(["ngrok", "http", "5000"], shell=True))


def list_pagekite(filepath, kite):
    """
    Create a command line PageKite process to open up Chronos to the cruel outside world.
    You will need to download 'pagekite.py' which you can find at https://pagekite.net/downloads and perform a first
    time setup. Please, read their quickstart guide on how to do this.
    :param filepath: path to 'pagekite.py' which you can download
    :param kite: the name of your (sub)kite
    :return:
    """
    pagekite = subprocess.run(["python", filepath, kite], stdout=sys.stdout, stderr=sys.stderr)
    log.info("PageKite stopped with exit code was: %d" % pagekite.returncode)


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
    # threading.Thread(target=tunnel()).start()
    if tunnel():
        log.info("Chronos is set up to receive webhook requests")
    else:
        log.warning('Chronos is not set up to receive webhook requests')
    # threading.Thread(target=list_ngrok).start()
    # log.info("server listed with ngrok")


def test_kraken():
    print(data_helper.get_open_orders('kraken'))
    print(data_helper.get_closed_orders('kraken'))


main()
