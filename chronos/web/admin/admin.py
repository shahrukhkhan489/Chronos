from flask import Blueprint, request, abort, render_template, Markup, make_response
from flask_login import login_required, current_user
from chronos import data_helper
from chronos import config, log
from chronos.libs import tools

admin = Blueprint('admin', __name__)
