from cryptography.fernet import InvalidToken, Fernet
from flask import Blueprint, request, url_for, flash, Markup, render_template, make_response, session
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
from chronos.libs.tools import encrypt, decrypt
from chronos.model import User
from chronos import db, log
from chronos.web.forms import LoginForm, SignupForm
from chronos.libs.flask_helpers import redirect_url

# Define blueprint and navigation menu
auth = Blueprint('auth', __name__)


@auth.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', exception=e), 404


@auth.route('/')
def index():
    return render_template('index.html')


@auth.route('/theme-test')
def theme_test():
    return render_template('theme_test.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    session_token = None

    form = LoginForm()
    if form.remember.data:
        form.email.data = request.form.get('email')

    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))  # if user doesn't exist or password is wrong, reload the page
        login_user(user, remember=remember, force=True)

        # load/generate token to encrypt sensitive date with
        if user.token is None:   # if the user doesn't have a token, then save it
            session_token = Fernet.generate_key()
            user.token = encrypt(session_token, password)
            user.save()
        else:
            try:
                session_token = decrypt(user.token, password)
            except InvalidToken as e:
                log.exception(e)
                pass

        log.info("session_token: {}".format(session_token))
        session['token'] = session_token
        assert('token' in session and session['token'])

        # redirect to the previous page (if any), or to the user role's default
        if user.is_admin:
            next_page = redirect_url(url_for('admin.dashboard'))
            # exclude auth.login as referrer
            if next_page.endswith(url_for('auth.login')):
                next_page = url_for('admin.dashboard')
        else:
            next_page = redirect_url(url_for('user.index'))
            # exclude auth.login as referrer
            if next_page.endswith(url_for('auth.login')):
                next_page = url_for('user.index')
        resp = make_response(redirect(next_page))

        # update user preferences cookies
        if user.theme:
            resp.set_cookie('chronos-preference-theme', user.theme)
        return resp
    return render_template('login.html', form=form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        session_token = Fernet.generate_key()

        user = User.query.filter_by(email=email).first()  # check if email address exists in database
        if user:  # leave a message if the email address exists
            flash(Markup('Email address already exists. Go to the <a href="login">login page</a>.'), 'danger')
            return redirect(url_for('auth.signup'))

        # noinspection PyArgumentList
        new_user = User(email=email,
                        username=username,
                        password=generate_password_hash(password, method='sha256'),
                        token=encrypt(session_token, password))
        session_token = decrypt(new_user.token, password)
        session['token'] = session_token

        if 'token' in session and session['token']:
            # add the new user to the database
            new_user.save()
            login_user(new_user)
            return redirect(url_for('user.index'))
        else:
            return render_template('signup.html', form=form)

    return render_template('signup.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
