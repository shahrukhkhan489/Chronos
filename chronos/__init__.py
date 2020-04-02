from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from chronos.libs import tools
# from flask_redis import FlaskRedis

# Globally accessible libraries
db = SQLAlchemy()
migrate = Migrate()
manager = Manager()
# r = FlaskRedis()

config = tools.get_config()
log = tools.create_log()
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    # app = Flask(__name__, template_folder="chronos/templates", static_folder="chronos/static")
    if config.has_option('postgresql', 'host') and config.has_option('postgresql', 'database') and config.has_option(
            'postgresql', 'user') and config.has_option('postgresql', 'password'):
        uri = 'postgresql://{}:{}@{}/{}'.format(config.get('postgresql', 'user'), config.get('postgresql', 'password'),
                                                config.get('postgresql', 'host'), config.get('postgresql', 'database'))
        app.config['SQLALCHEMY_DATABASE_URI'] = uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # app.config.from_object('config.Config')

    # Initialize Plugins
    db.init_app(app)
    migrate.init_app(app, db)
    manager.__init__(app)
    manager.add_command('db', MigrateCommand)

    # r.init_app(app)

    with app.app_context():
        # Include our Routes
        from . import controller
        # Register Blueprints @ see https://hackersandslackers.com/flask-blueprints
        # app.register_blueprint(auth.auth_bp)
        # app.register_blueprint(admin.admin_bp)
        return app
