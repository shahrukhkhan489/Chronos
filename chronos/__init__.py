import os
import urllib.parse

from flask import Flask, request
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, user_logged_out, user_logged_in
from flask_migrate import Migrate, MigrateCommand
from flask_nav import Nav, register_renderer
from flask_nav.elements import Navbar, View
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_themer import Themer
from flask_wtf import CSRFProtect
# from flask_menu import Menu, register_menu
from sqlalchemy.sql import ClauseElement
from chronos.libs import tools
from chronos.web.http_error import page_not_found
from chronos.web.nav import Bootstrap3Renderer, Bootstrap4Renderer, NeonLightsRenderer


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


def top_nav():
    # user_id = login_manager.id_attribute
    # log.info('__init__.top_nav() called; user_id = {}'.format(user_id))
    if user_logged_in and hasattr(current_user, 'is_admin') and current_user.is_admin:
        return Navbar('Chronos/Admin',
                      View('Home', 'auth.index'),
                      View('Dashboard', 'admin.dashboard'),
                      View('Exchanges', 'ExchangeView:index'),
                      View('Users', 'UserView:index'),
                      View('API Keys', 'ApiKeyView:index'),
                      View('Orders', 'user.orders'),
                      View('Profile', 'user.profile'),
                      View('Logout', 'auth.logout'))
    elif user_logged_in and hasattr(current_user, 'is_admin'):
        return Navbar('Chronos',
                      View('Home', 'auth.index'),
                      View('API Keys', 'ApiKeyView:index'),
                      View('Orders', 'user.orders'),
                      View('Profile', 'user.profile'),
                      View('Logout', 'auth.logout'))
    else:
        return Navbar('Chronos',
                      View('Home', 'auth.index'),
                      View('Sign Up', 'auth.signup'),
                      View('Login', 'auth.login'))


db = SQLAlchemy()
init_db(db)
login_manager = LoginManager()
migrate = Migrate()
manager = Manager()
nav = Nav()
themer = Themer()
config = tools.get_config()
log = tools.create_log()
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
        app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DATABASE_CREATED'] = False
        if not database_exists(connection_string):
            create_database(connection_string)
            app.config['DATABASE_CREATED'] = True

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
    CSRFProtect(app)
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
