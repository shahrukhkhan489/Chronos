"""
Tradingview-webhooks-bot is a python bot that works with tradingview's webhook alerts!
This bot is not affiliated with tradingview and was created by @robswc

You can follow development on github at: github.com/robswc/tradingview-webhook-bot

I'll include as much documentation here and on the repo's wiki!  I
expect to update this as much as possible to add features as they become available!
Until then, if you run into any bugs let me know!
"""
from flask import Flask, request, abort
from chronos import actions
from chronos.tools import debug, tools, flask_ngrok

log = debug.create_log()
config = tools.get_config()
ngrox_url = None

# Create Flask object called app.
app = Flask(__name__)


# Create root to easily let us know its on/working.
@app.route('/')
def root():
    return 'online'


@app.route('/webhook', methods=['POST'])
def webhook():
    password = config.get('authentication', 'password')
    if request.method == 'POST':
        # Parse the string data from tradingview into a python dict
        log.info(request.get_data(as_text=True))
        data = actions.parse_webhook(request.get_data(as_text=True))
        # Check that the key is correct
        if (not password) or tools.get_token(password) == data['key']:
            log.info(' [Alert Received] ')
            log.info('POST Received: {}'.format(data))
            actions.send_order(data)
            return '', 200
        else:
            abort(403)
    else:
        abort(400)


def run():
    flask_ngrok.start_ngrok()
    app.run()
    # app.run(debug=True, use_reloader=False)
