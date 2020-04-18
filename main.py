import threading
from time import sleep
from subprocess import check_output
from chronos import data_helper
from chronos import config, log


def start_flask():
    import manage
    manage.run()


def list_ngrok():
    log.info(check_output("ngrok http 5000", shell=True))


def main():
    from chronos.libs import tools
    password = config.get('security', 'webhook_password')
    key = ""
    if password:
        key = tools.get_token(password)

    # test_kraken()

    output = "{'exchange': '{{exchange}}', 'type': 'market', 'side': 'buy', 'amount': 1, 'symbol': '{{ticker}}', 'price': {{close}}, 'key': '" + key + "'}"
    print()
    log.info("Example webhook message: {}".format(output))
    print()
    # start a thread with the server
    # log.info("creating server")
    threading.Thread(target=start_flask).start()
    sleep(1)
    # list the server with ngrok
    threading.Thread(target=list_ngrok).start()
    log.info("server listed with ngrok")


def test_kraken():
    print(data_helper.get_open_orders('kraken'))
    print(data_helper.get_closed_orders('kraken'))


main()
