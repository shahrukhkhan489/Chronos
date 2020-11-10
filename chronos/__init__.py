import os
import urllib.parse
from flask import Flask, request
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, user_logged_out
from flask_migrate import Migrate, MigrateCommand
from flask_nav import Nav, register_renderer
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_themer import Themer
from flask_wtf import CSRFProtect
from sqlalchemy.sql import ClauseElement
from chronos.libs import tools
from chronos.web.http_error import page_not_found
from chronos.web.nav import Bootstrap3Renderer, Bootstrap4Renderer, NeonLightsRenderer, top_nav


def init_db(database):

    """Add a save() function to db.Model"""
    def save(model):
        try:
            database.session.add(model)
            database.session.commit()
        except Exception as e:
            log.exception(e)

    def update(model, defaults=None, **kwargs):
        try:
            params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
            params.update(defaults or {})
            for param in params:
                setattr(model, param, params[param])
        except Exception as e:
            log.exception(e)
        return model

    database.Model.save = save
    database.Model.update = update


csrf = CSRFProtect()
db = SQLAlchemy()
init_db(db)
login_manager = LoginManager()
migrate = Migrate()
manager = Manager()
nav = Nav()
themer = Themer()
config = tools.get_config()
mode = 'a'  # append
if config.getboolean('logging', 'clear_on_start_up'):
    mode = 'w'  # overwrite
log = tools.create_log(mode)
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False, template_folder='web/templates', static_folder='web/static', static_url_path="/static")
    if config.has_option('security', 'webserver_password'):
        app.config['SECRET_KEY'] = config.get('security', 'webserver_password')
    if config.has_option('database', 'connection_string'):
        from sqlalchemy_utils import create_database, database_exists
        connection_string = config.get('database', 'connection_string')
        connect_args = {"options": "-c timezone=utc"}
        app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": connect_args}
        app.config['DATABASE_CREATED'] = False
        if not database_exists(connection_string):
            create_database(connection_string)
            app.config['DATABASE_CREATED'] = True

    csrf.init_app(app)
    # app.config.from_object('config.Config')
    app.register_error_handler(404, page_not_found)

    # Initialize Plugins
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations'))
    manager.__init__(app)
    manager.add_command('db', MigrateCommand)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    nav.init_app(app)
    nav.register_element('top', top_nav)
    register_renderer(app, 'bootstrap', Bootstrap4Renderer)
    register_renderer(app, 'neon-lights', NeonLightsRenderer)
    themer.init_app(app)
    # CSRFProtect(app)
    Bootstrap(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .model import User
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    @app.context_processor
    def get_navigation():
        if user_logged_out:
            navigation = {'.index': 'Home', '.signup': 'Sign Up', '.login': 'Login'}
        else:
            if current_user.is_admin:
                navigation = {'.dashboard': 'Dashboard', '.admin': 'Admin', '.profile': 'Profile', '.logout': 'Logout'}
            else:
                navigation = {'.dashboard': 'Dashboard', '.profile': 'Profile', '.logout': 'Logout'}
        return navigation

    @themer.current_theme_loader
    def get_current_theme():
        if hasattr(current_user, 'theme') and current_user.theme:
            return current_user.theme
        elif request and request.cookies and request.cookies.get('chronos-preference-theme'):
            return request.cookies.get('chronos-preference-theme')
        else:
            return 'moon-base-alpha'

    @app.context_processor
    def context_processor():

        def url_for_static(filename):
            # root = os.path.join(os.curdir, 'chronos\web\static')
            return urllib.parse.urljoin('/chronos/web/static/', filename)
            # return os.path.abspath(os.path.join(os.path.join(root, 'chronos\web\static'), filename))

        return dict(url_for_static=url_for_static)

    app.add_url_rule('/static/favicon/<path:filename>/', endpoint='favicon',
                     view_func=app.send_static_file)
    app.add_url_rule('/static/js/<path:filename>/', endpoint='js',
                     view_func=app.send_static_file)
    with app.app_context():
        # Include our Routes
        # blueprint for non-auth routes in our app
        from chronos.web.authentication.auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, template_folder='templates', static_folder='static')
        auth_blueprint.template_folder = 'templates'
        auth_blueprint.static_folder = 'static'

        # blueprint for regular user parts of app
        from chronos.web.user.user import user as user_blueprint
        app.register_blueprint(user_blueprint, template_folder='templates', static_folder='static')
        user_blueprint.template_folder = 'templates'
        user_blueprint.static_folder = 'static'

        # blueprint for admin user parts of app
        from chronos.web.admin.admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, template_folder='templates', static_folder='static')
        admin_blueprint.template_folder = 'templates'
        admin_blueprint.static_folder = 'static'

        from chronos.web import crud
        crud.UserView.register(admin_blueprint, db.session)
        crud.ExchangeView.register(admin_blueprint, db.session)
        crud.ApiKeyView.register(user_blueprint, db.session)

        crud.register(app, db.session)

        return app
