import threading
from subprocess import check_output
from chronos import webhook_bot


def start_flask(arg1):
    webhook_bot.log.info("creating server")
    webhook_bot.run()


def list_ngrok(arg1):
    check_output("ngrok http 5000", shell=True)
    webhook_bot.log.info("server listed with ngrok")


def main():
    # start a thread with the server
    threading.Thread(target=start_flask, args=('arg1',)).start()
    # list the server with ngrok
    threading.Thread(target=list_ngrok, args=('arg1',)).start()


main()
