from flask_login import login_required
from flask_menu.classy import register_flaskview
from chronos.libs.crud import CrudView
from chronos.web.forms import UserForm, ExchangeForm, ApiKeyForm
from chronos.model import User, Exchange, ApiKey
from ..libs.permission import ADMIN


class ApiKeyView(CrudView):
    decorators = [login_required]
    form = ApiKeyForm
    model = ApiKey
    cols = {'id': 'ID', 'exchange': 'Exchange', 'public_key': 'Public Key', 'private_key': 'Private Key'}
    is_deletable = True


class UserView(CrudView):
    decorators = [login_required]
    form = UserForm
    model = User
    cols = {'id': 'ID', 'username': 'Username', 'email': 'Email', 'password': 'Password'}
    order_by = 'username'


class ExchangeView(CrudView):
    decorators = [login_required]
    form = ExchangeForm
    model = Exchange
    cols = {'id': 'ID', 'name': 'Name', 'ccxt_name': 'CCXT Name', 'class_name': 'Class Name'}
    is_creatable = ADMIN
    is_editable = ADMIN
    order_by = 'name'


def register(app, db_session):
    UserView.register(app, db_session)
    ExchangeView.register(app, db_session)
    ApiKeyView.register(app, db_session)

    register_flaskview(app, UserView)
    register_flaskview(app, ExchangeView)
    register_flaskview(app, ApiKeyView)
