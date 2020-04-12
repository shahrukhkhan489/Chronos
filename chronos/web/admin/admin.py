from flask import Blueprint, abort, render_template
from flask_nav.elements import Navbar, View
from chronos import db, nav
from flask_login import login_required, current_user

admin = Blueprint('admin', __name__)
nav.register_element('admin', Navbar('admin',
                                     View('Home', 'auth.index'),
                                     View('Dashboard', 'admin.dashboard'),
                                     View('Orders', 'user.orders'),
                                     View('Profile', 'user.profile'),
                                     View('Logout', 'auth.logout')))


def check_admin():
    """
    Prevent non-admins from accessing the page
    """
    if not (current_user and current_user.is_admin):
        abort(403)


@admin.route('/dashboard')
@login_required
def dashboard():
    check_admin()
    return render_template('dashboard.html')
