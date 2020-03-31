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
from flask import Flask, request, abort, render_template, Markup
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from chronos.tools import debug, tools
from chronos.tools.json2html import json2html
from chronos import data_helper

log = debug.create_log()
config = tools.get_config()

# Create Flask object called app.
app = Flask(__name__)

if config.has_option('postgresql', 'host') and config.has_option('postgresql', 'database') and config.has_option('postgresql', 'user') and config.has_option('postgresql', 'password'):
    """
    Although this is the view, relaying user requests to the controller, we need to generate the model from here as 
    Flask-SQLAlchemy needs the Flask app as a parameter. 
    """
    uri = 'postgresql://{}:{}@{}/{}'.format(config.get('postgresql', 'user'), config.get('postgresql', 'password'),                                            config.get('postgresql', 'host'), config.get('postgresql', 'database'))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    from chronos import model
    model.update_schema()
    # model.create()

# Setup jinja2
# print(os.path.join(os.path.dirname(__file__), "static"))
# loader = jinja2.FileSystemLoader(
#         [os.path.join(os.path.dirname(__file__), "static"),
#          os.path.join(os.path.dirname(__file__), "templates")])
# environment = jinja2.Environment(loader=loader)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/orders')
def orders():
    open_orders = json.dumps(data_helper.get_open_orders('kraken'))
    closed_orders = json.dumps(data_helper.get_closed_orders('kraken'))
    open_orders_table = Markup(json2html.convert(json=open_orders, table_attributes='class="table table-condensed table-bordered table-hover"'))
    closed_orders_table = Markup(json2html.convert(json=closed_orders, table_attributes='class="table table-condensed table-bordered table-hover"'))
    return render_template('orders.html', open_orders=open_orders_table, closed_orders=closed_orders_table)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', exception=e), 404


@app.route('/status')
def status():
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


def run():

    app.run()
    # app.run(debug=True, use_reloader=False)
