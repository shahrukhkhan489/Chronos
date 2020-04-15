from flask_login import current_user, user_logged_in

ADMIN = 2
USER = 1


def check_permission(permission):
    if permission == ADMIN:
        return user_logged_in and hasattr(current_user, 'is_admin') and current_user.is_admin
    else:
        return permission
