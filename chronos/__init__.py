from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_nav import Nav
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from chronos.libs import tools
from chronos.web.http_error import page_not_found

db = SQLAlchemy()
migrate = Migrate()
manager = Manager()
nav = Nav()

config = tools.get_config()
log = tools.create_log()
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False, template_folder='web/templates', static_folder='web/static')
    if config.has_option('security', 'webserver_password'):
        app.config['SECRET_KEY'] = config.get('security', 'webserver_password')
    if config.has_option('database', 'connection_string'):
        app.config['SQLALCHEMY_DATABASE_URI'] = config.get('database', 'connection_string')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config.from_object('config.Config')
    app.register_error_handler(404, page_not_found)

    # Initialize Plugins
    db.init_app(app)
    migrate.init_app(app, db)
    manager.__init__(app)
    manager.add_command('db', MigrateCommand)
    nav.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    CSRFProtect(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .model import User
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    with app.app_context():
        # Include our Routes
        # blueprint for auth routes in our app
        from chronos.web.authentication.auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)
        auth_blueprint.template_folder = 'templates'
        auth_blueprint.static_folder = 'static'

        # blueprint for non-auth parts of app
        from chronos.web.user.user import user as user_blueprint
        app.register_blueprint(user_blueprint)
        user_blueprint.template_folder = 'templates'
        user_blueprint.static_folder = 'static'

        # blueprint for non-auth parts of app
        from chronos.web.admin.admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, template_folder='web/admin/templates', static_folder='static')
        admin_blueprint.template_folder = 'templates'
        admin_blueprint.static_folder = 'static'

        return app
