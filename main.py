import threading
from chronos import webhook_bot


def start_flask():
    webhook_bot.run()


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
    webhook_bot.log.info("server listed with ngrok")


main()
