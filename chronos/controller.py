"""
CONTROLLER

Tradingview-webhooks-bot is a python bot that works with tradingview's webhook alerts!
This bot is not affiliated with tradingview and was created by @robswc

You can follow development on github at: github.com/robswc/tradingview-webhook-bot

I'll include as much documentation here and on the repo's wiki!  I
expect to update this as much as possible to add features as they become available!
Until then, if you run into any bugs let me know!
"""
import json
from flask import request, abort, render_template, Markup, make_response
from chronos.libs import tools
from chronos.libs.json2html import json2html
from chronos import data_helper
from . import config, log
from flask import current_app as app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/orders', methods=['GET'])
def orders():
    if request.method != 'GET':
        return make_response('Malformed request', 400)
    open_orders = json.dumps(data_helper.get_open_orders('kraken'))
    closed_orders = json.dumps(data_helper.get_closed_orders('kraken'))
    open_orders_table = Markup(json2html.convert(json=open_orders, table_attributes='class="table table-condensed table-bordered table-hover"'))
    closed_orders_table = Markup(json2html.convert(json=closed_orders, table_attributes='class="table table-condensed table-bordered table-hover"'))
    return render_template('orders.html', open_orders=open_orders_table, closed_orders=closed_orders_table)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', exception=e), 404


@app.route('/status', methods=['GET'])
def status():
    if request.method != 'GET':
        return render_template('404.html', exception='Malformed request'), 400
    return render_template('index.html', message='online')


@app.route('/example/list')
def list_example():
    my_list = ['Alvin', 'Simon', 'Theodore']
    return render_template('index.html', list_example=my_list)


@app.route('/example/user/<username>')
def uri_example(username):
    return render_template('index.html', username=username)


@app.route('/webhook', methods=['POST'])
def webhook():
    password = config.get('authentication', 'password')
    if request.method == 'POST':
        # Parse the string data from tradingview into a python dict
        log.info(request.get_data(as_text=True))
        data = data_helper.parse_webhook(request.get_data(as_text=True))
        # Check that the key is correct
        if (not password) or tools.get_token(password) == data['key']:
            log.info(' [Alert Received] ')
            log.info('POST Received: {}'.format(data))
            data_helper.send_order(data)
            return '', 200
        else:
            abort(403)
    else:
        abort(400)


# def run():
#     app.run()