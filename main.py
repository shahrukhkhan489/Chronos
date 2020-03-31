import threading
from time import sleep
from subprocess import check_output
from chronos import data_helper, controller


def start_flask():
    controller.run()


def list_ngrok():
    controller.log.info(check_output("ngrok http 5000", shell=True))


def main():
    from chronos.libs import tools
    config = tools.get_config()
    password = config.get('authentication', 'password')
    key = ""
    if password:
        key = tools.get_token(password)

    # if config.has_option('postgresql', 'host') and config.has_option('postgresql', 'database') and config.has_option('postgresql', 'user') and config.has_option('postgresql', 'password'):
    #     try:
    #         db.connect(config.get('postgresql', 'host'), config.get('postgresql', 'database'), config.get('postgresql', 'user'), config.get('postgresql', 'password'))
    #     except Exception as e:
    #         print(e)
    # test_kraken()
    output = "{'exchange': '{{exchange}}', 'type': 'market', 'side': 'buy', 'amount': 1, 'symbol': '{{ticker}}', 'price': {{close}}, 'key': '" + key + "'}"
    print()
    controller.log.info("Example webhook message: {}".format(output))
    print()
    # start a thread with the server
    controller.log.info("creating server")
    threading.Thread(target=start_flask).start()
    sleep(1)
    # list the server with ngrok
    threading.Thread(target=list_ngrok).start()
    controller.log.info("server listed with ngrok")


def test_kraken():
    print(data_helper.get_open_orders('kraken'))
    print(data_helper.get_closed_orders('kraken'))


main()
