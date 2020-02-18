import threading
from time import sleep
from subprocess import check_output
from chronos import webhook_bot


def start_flask():
    webhook_bot.run()


def list_ngrok():
    webhook_bot.log.info(check_output("ngrok http 5000", shell=True))


def main():
    from chronos.tools import tools
    config = tools.get_config()
    password = config.get('authentication', 'password')
    key = ""
    if password:
        key = tools.get_token(password)
    output = "{'exchange': '{{exchange}}', 'type': 'market', 'side': 'buy', 'amount': 1, 'symbol': '{{ticker}}', 'price': {{close}}, 'key': '" + key + "'}"
    print()
    webhook_bot.log.info("Example webhook message: {}".format(output))
    print()
    # start a thread with the server
    webhook_bot.log.info("creating server")
    threading.Thread(target=start_flask).start()
    sleep(1)
    # list the server with ngrok
    threading.Thread(target=list_ngrok).start()
    webhook_bot.log.info("server listed with ngrok")


main()
