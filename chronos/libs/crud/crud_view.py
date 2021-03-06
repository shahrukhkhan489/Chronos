"""
Copyright (c) 2014, Andrew Plummer
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Modified by timelyart, timelyart@protonmail.com, https://github.com/timelyart
"""
from flask_classful import FlaskView, route
from flask import render_template, request, redirect, url_for
from os.path import join as path_join
from chronos.libs.flask_helpers import set_boolean_values
from ..permission import check_permission
from flask_login import current_user
from sqlalchemy.sql import text

# noinspection PyUnusedLocal
from chronos import log


# noinspection PyUnusedLocal
class CrudView(FlaskView):
    """Gives a quick template

    form, a form class

    model, assumed to be a model that implements both save_form(form)
    and delete() methods

    presenter, a callable that when called with a list of models gives
    something that should be sent out to the template

    template_directory, name of the directory that all of the
    templates are in

    index_template, name of the template to use for the index page,
    defaults to index.html

    show_template, name of the template to use for the show page,
    defaults to show.html

    add_template, name of the template to use for the add page,
    defaults to add.html

    edit_template, name of the template to use for the edit page,
    defaults to edit.html

    """

    index_template = 'index.html'
    show_template = 'show.html'
    add_template = 'add.html'
    edit_template = 'edit.html'

    template_directory = ''
    presenter = list

    db_session = None
    addto_index_field = None
    form = None
    model = None
    filters = None
    order_by = None
    is_creatable = False  # False, True or ADMIN
    is_showable = False  # False, True or ADMIN
    is_editable = False  # False, True or ADMIN
    is_deletable = False  # False, True or ADMIN
    cols = []
    navbar = None
    # model = None

    methods = ['index', 'add', 'edit', 'show', 'delete']

    # noinspection PyMethodOverriding
    @classmethod
    def register(cls, app, db_session, *args, **kwargs):
        cls.db_session = db_session
        for key, value in kwargs.items():
            if hasattr(cls, key):
                cls.key = value
                log.info('{}={}'.format(key, cls.key))
        super(CrudView, cls).register(app, *args, **kwargs)

    def _url_for_index(self):
        return url_for(self.__class__.__name__ + ':index')

    def _success_redirect_url(self, item, prev=None):
        return self._url_for_index()

    # @staticmethod
    # def _set_boolean_values(form, item):
    #     """
    #     Checkboxes are not submitted unless they are checked. So, un-checking a WTFForm.BooleanField will not return a
    #     false value. The workaround is to test if the name of the checkbox made it into the request. If not, we assume
    #     that the checkbox is un-checked. If so, we can read the value of the checkbox, but it doesn't matter because it
    #     should be True anyway.
    #     NOTE: with 2+ checkboxes with the same name, the last checkbox will override the others.
    #     :param form:
    #     :param item:
    #     :return:
    #     """
    #     if request.method == "POST":
    #         for attr, value in vars(item).items():
    #             if isinstance(value, bool) and hasattr(form, attr):
    #                 checkbox = getattr(form, attr)
    #                 checkbox_value = len(request.form.getlist(attr)) > 0  # check if the checkbox name is in the request
    #                 setattr(checkbox, 'data', checkbox_value)
    #     else:
    #         for attr, value in vars(item).items():
    #             if isinstance(value, bool):
    #                 field = getattr(form, attr)
    #                 if field and hasattr(field, 'data'):
    #                     setattr(field, 'data', value)
    #                 setattr(field, 'default', value)

    @classmethod
    def _template_path(cls, template_name):
        return path_join(cls.template_directory, template_name)

    # noinspection PyArgumentList
    def index(self):
        if 'index' not in self.methods:
            return render_template('404.html')
            # abort(404)
        items = self._index_items()
        if self.presenter:
            items = self.presenter(items)
        # log.info('is_editable = {}'.format(self.is_editable))
        # log.info('is_deletable = {}'.format(self.is_deletable))
        return render_template(self._template_path(self.index_template),
                               columns=self.cols, items=items, is_editable=check_permission(self.is_editable), is_deletable=check_permission(self.is_deletable),
                               **self._index_extras(items))

    def _index_items(self):
        # Only ever return records that are of the logged in user (where applicable), e.g. api_keys, orders, et cetera
        if hasattr(self.model, 'user_id'):
            if self.filters:
                self.filters = self.filters + (self.model.user_id == int(current_user.id), )
            else:
                self.filters = (self.model.user_id == int(current_user.id), )

        try:
            if self.filters and self.order_by:
                return self.model.query.filter(*self.filters).order_by(text(self.order_by)).all()
            elif self.filters:
                return self.model.query.filter(*self.filters).all()
            elif self.order_by:
                return self.model.query.order_by(text(self.order_by)).all()
            else:
                return self.model.query.all()
        except Exception as e:
            log.exception(e)
            return {}

    @staticmethod
    def _index_extras(items):
        return {}

    @route('/add/', methods=['POST', 'GET'])
    def add(self):
        if 'add' not in self.methods:
            return render_template('404.html')
        if not check_permission(self.is_creatable):
            return render_template('403.html')
        form = self.form(request.form)
        if form.validate_on_submit():
            item = self.model()
            item.save_form(form, session=self.db_session)
            return redirect(self._success_redirect_url(item, 'add'))
        return render_template(self._template_path(self.add_template), form=form)

    @route('/addto/<int:id_>', methods=['POST', 'GET'])
    def addto(self, id_):
        if 'addto' not in self.methods:
            return render_template('404.html')
        if not check_permission(self.is_creatable):
            return render_template('403.html')
        form = self.form(request.form)
        if form.validate_on_submit():
            item = self.model()
            if self.addto_index_field:
                extras = {self.addto_index_field: id_}
            else:
                extras = {}
            item.save_form(form, session=self.db_session, extras=extras)
            return redirect(self._success_redirect_url(item, 'addto'))
        return render_template(self._template_path(self.add_template), form=form, **self._addto_extras(id_))

    @staticmethod
    def _addto_extras(id_):
        return {}

    @route('/show/<int:id_>')
    def show(self, id_):
        if 'show' not in self.methods:
            return render_template('404.html')
        if not check_permission(self.is_showable):
            return render_template('403.html')
        item = self.model.query.get_or_404(id_)
        return render_template(self._template_path(self.show_template), item=item, **self._show_extras(item))

    @staticmethod
    def _show_extras(item):
        return {}

    @route('/edit/<int:id_>', methods=['POST', 'GET'])
    def edit(self, id_):
        if 'edit' not in self.methods:
            return render_template('404.html')
        if not check_permission(self.is_editable):
            return render_template('403.html')
        item = self.model.query.get_or_404(id_)
        form = self.form(request.form, obj=item)

        # WTForms do not check/uncheck on the basis of the item's attribute value
        set_boolean_values(form, item)

        if form.validate_on_submit():
            # WTForms do not take into account that un-checked checkboxes will not POST when submitting a form
            set_boolean_values(form, item)
            item.save_form(form, session=self.db_session)
            return redirect(self._success_redirect_url(item, 'edit'))
        return render_template(self._template_path(self.edit_template), form=form, **self._edit_extras(item))

    @staticmethod
    def _edit_extras(item):
        return {}

    @route('/delete/<int:id_>', methods=['POST'])
    def delete(self, id_):
        if 'delete' not in self.methods:
            return render_template('404.html')
        if not check_permission(self.is_deletable):
            return render_template('403.html')
        item = self.model.query.get_or_404(id_)
        item = self.model.query.get_or_404(id_)
        item.delete(session=self.db_session)
        return redirect(self._success_redirect_url(item, 'delete'))
