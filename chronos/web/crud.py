from flask_login import login_required, current_user
from chronos.libs.crud import CrudView
from chronos.web.forms import UserForm, ExchangeForm, ApiKeyForm
from chronos.model import User, Exchange, ApiKey


class ApiKeyView(CrudView):
    decorators = [login_required]
    form = ApiKeyForm
    model = ApiKey
    cols = {'id': 'ID', 'exchange': 'Exchange', 'public_key': 'Public Key', 'private_key': 'Private Key'}
    if current_user:
        id = current_user.id
    # filters = (model.user_id > 1, )


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
    order_by = 'name'


def register(app, db_session):
    UserView.register(app, db_session)
    ExchangeView.register(app, db_session)
    ApiKeyView.register(app, db_session)
