from flask import Blueprint, abort, render_template, url_for
from flask_login import login_required, current_user, user_logged_out
from werkzeug.utils import redirect

admin = Blueprint('admin', __name__)


def check_admin():
    """
    Prevent non-admins from accessing the page
    """
    if user_logged_out:
        return redirect(url_for('auth.login'))
    elif not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        abort(403)


@admin.route('/dashboard')
@login_required
def dashboard():
    check_admin()
    return render_template('dashboard.html')
