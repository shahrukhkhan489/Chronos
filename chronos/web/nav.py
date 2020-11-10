"""
This file was part of Bootstrap-Flask and was modified under the terms of its Apache License.
https://github.com/mbr/flask-bootstrap/blob/master/flask_bootstrap/nav.py
"""

from hashlib import sha1
from dominate import tags
from flask_login import user_logged_in, current_user
from flask_nav.elements import Navbar, View
from flask_nav.renderers import Renderer


# noinspection PyPep8Naming
class Bootstrap3Renderer(Renderer):
    def __init__(self, html5=True, _id=None):
        self.html5 = html5
        self._in_dropdown = False
        self.id = _id

    def visit_Navbar(self, node):
        # create a navbar id that is somewhat fixed, but do not leak any
        # information about memory contents to the outside
        node_id = self.id or sha1(str(id(node)).encode()).hexdigest()

        root = tags.nav() if self.html5 else tags.div(role='navigation')
        root['class'] = 'navbar navbar-default'

        cont = root.add(tags.div(_class='container-fluid'))

        # collapse button
        header = cont.add(tags.div(_class='navbar-header'))
        btn = header.add(tags.button())
        btn['type'] = 'button'
        btn['class'] = 'navbar-toggle collapsed'
        btn['data-toggle'] = 'collapse'
        btn['data-target'] = '#' + node_id
        btn['aria-expanded'] = 'false'
        btn['aria-controls'] = 'navbar'

        btn.add(tags.span('Toggle navigation', _class='sr-only'))
        btn.add(tags.span(_class='icon-bar'))
        btn.add(tags.span(_class='icon-bar'))
        btn.add(tags.span(_class='icon-bar'))

        # title may also have a 'get_url()' method, in which case we render
        # a brand-link
        if node.title is not None:
            if hasattr(node.title, 'get_url'):
                header.add(tags.a(node.title.text, _class='navbar-brand',
                                  href=node.title.get_url()))
            else:
                header.add(tags.span(node.title, _class='navbar-brand'))

        bar = cont.add(tags.div(
            _class='navbar-collapse collapse',
            id=node_id,
        ))
        bar_list = bar.add(tags.ul(_class='nav navbar-nav'))

        for item in node.items:
            bar_list.add(self.visit(item))

        return root

    def visit_Text(self, node):
        if not self._in_dropdown:
            return tags.p(node.text, _class='navbar-text')
        return tags.li(node.text, _class='dropdown-header')

    # noinspection PyMethodMayBeStatic
    def visit_Link(self, node):
        item = tags.li()
        item.add(tags.a(node.text, href=node.get_url()))

        return item

    # noinspection PyUnusedLocal
    def visit_Separator(self, node):
        if not self._in_dropdown:
            raise RuntimeError('Cannot render separator outside Subgroup.')
        return tags.li(role='separator', _class='divider')

    def visit_Subgroup(self, node):
        if not self._in_dropdown:
            li = tags.li(_class='dropdown')
            if node.active:
                li['class'] = 'active'
            a = li.add(tags.a(node.title, href='#', _class='dropdown-toggle'))
            a['data-toggle'] = 'dropdown'
            a['role'] = 'button'
            a['aria-haspopup'] = 'true'
            a['aria-expanded'] = 'false'
            a.add(tags.span(_class='caret'))

            ul = li.add(tags.ul(_class='dropdown-menu'))

            self._in_dropdown = True
            for item in node.items:
                ul.add(self.visit(item))
            self._in_dropdown = False

            return li
        else:
            raise RuntimeError('Cannot render nested Subgroups')

    # noinspection PyMethodMayBeStatic
    def visit_View(self, node):
        item = tags.li()
        item.add(tags.a(node.text, href=node.get_url(), title=node.text))
        if node.active:
            item['class'] = 'active'

        return item


# noinspection PyPep8Naming
class Bootstrap4Renderer(Renderer):
    def __init__(self, html5=True, _id=None):
        self.html5 = html5
        self._in_dropdown = False
        self.id = _id

    def visit_Navbar(self, node):
        # create a navbar id that is somewhat fixed, but do not leak any
        # information about memory contents to the outside
        node_id = self.id or sha1(str(id(node)).encode()).hexdigest()

        root = tags.nav() if self.html5 else tags.div(role='navigation')
        root['class'] = 'navbar navbar-expand-lg navbar-light bg-light'

        # cont = root.add(tags.div(_class='container-fluid'))

        # collapse button
        # header = cont.add(tags.div(_class='navbar-header'))
        btn = root.add(tags.button())
        btn['class'] = 'navbar-toggler'
        btn['type'] = 'button'
        btn['data-toggle'] = 'collapse'
        btn['data-target'] = '#' + node_id
        btn['aria-controls'] = node_id
        btn['aria-expanded'] = 'false'
        btn['aria-label'] = 'Toggle navigation'
        # btn.add(tags.span('Toggle navigation', _class='sr-only'))
        # btn.add(tags.span(_class='icon-bar'))
        # btn.add(tags.span(_class='icon-bar'))
        # btn.add(tags.span(_class='icon-bar'))
        bar = root.add(tags.div(
            _class='navbar-collapse collapse',
            id=node_id,
        ))
        if node.title is not None:
            if hasattr(node.title, 'get_url'):
                bar.add(tags.a(node.title.text, _class='navbar-brand',
                               href=node.title.get_url()))
            else:
                bar.add(tags.a(node.title, _class='navbar-brand', href='/'))
        bar_list = bar.add(tags.ul(_class='nav navbar-nav'))

        for item in node.items:
            bar_list.add(self.visit(item))

        return root

    def visit_Text(self, node):
        if not self._in_dropdown:
            return tags.p(node.text, _class='navbar-text')
        return tags.li(node.text, _class='dropdown-header')

    # noinspection PyMethodMayBeStatic
    def visit_Link(self, node):
        item = tags.li()
        item.add(tags.a(node.text, href=node.get_url()))

        return item

    # noinspection PyUnusedLocal
    def visit_Separator(self, node):
        if not self._in_dropdown:
            raise RuntimeError('Cannot render separator outside Subgroup.')
        return tags.li(role='separator', _class='divider')

    def visit_Subgroup(self, node):
        if not self._in_dropdown:
            li = tags.li(_class='dropdown')
            if node.active:
                li['class'] = 'active'
            a = li.add(tags.a(node.title, href='#', _class='dropdown-toggle'))
            a['data-toggle'] = 'dropdown'
            a['role'] = 'button'
            a['aria-haspopup'] = 'true'
            a['aria-expanded'] = 'false'
            a.add(tags.span(_class='caret'))

            ul = li.add(tags.ul(_class='dropdown-menu'))

            self._in_dropdown = True
            for item in node.items:
                ul.add(self.visit(item))
            self._in_dropdown = False

            return li
        else:
            raise RuntimeError('Cannot render nested Subgroups')

    # noinspection PyMethodMayBeStatic
    def visit_View(self, node):
        item = tags.li()
        item.add(tags.a(node.text, _class='nav-link', href=node.get_url(), title=node.text))
        if node.active:
            item['class'] = 'nav-item active'
        else:
            item['class'] = 'nav-item'
        return item


# noinspection PyPep8Naming
class NeonLightsRenderer(Renderer):
    def __init__(self, html5=True, _id=None):
        self.html5 = html5
        self._in_dropdown = False
        self.id = _id

    def visit_Navbar(self, node):
        # create a navbar id that is somewhat fixed, but do not leak any
        # information about memory contents to the outside
        # node_id = self.id or sha1(str(id(node)).encode()).hexdigest()

        root = tags.div()
        root['class'] = "navbar-dark text-white"
        container = root.add(tags.div())
        container['class'] = "container"
        root = tags.nav() if self.html5 else tags.div(role='navigation')
        root['class'] = 'navbar px-0 navbar-expand-lg navbar-dark'

        # collapse button
        # header = nav.add(tags.div(_class='navbar-header'))
        # btn = header.add(tags.button())
        btn = root.add(tags.button())
        btn['type'] = 'button'
        btn['class'] = 'navbar-toggler'
        btn['data-toggle'] = 'collapse'
        btn['data-target'] = '#navbarNavAltMarkup'
        btn['aria-expanded'] = 'false'
        btn['aria-controls'] = 'navbarNavAltMarkup'
        btn['aria-label'] = 'Toggle navigation'
        btn.add(tags.span(_class='navbar-toggler-icon'))

        bar = root.add(tags.div(id='navbarNavAltMarkup', _class='navbar-collapse collapse'))
        bar_list = bar.add(tags.div(_class='navbar-nav'))

        for item in node.items:
            bar_list.add(self.visit_Link(item))

        return root

    def visit_Text(self, node):
        if not self._in_dropdown:
            return tags.p(node.text, _class='navbar-text')
        return tags.li(node.text, _class='dropdown-header')

    # noinspection PyMethodMayBeStatic
    def visit_Link(self, node):
        return tags.a(node.text, href=node.get_url(), _class="p-3 text-decoration-none text-light")

    # noinspection PyUnusedLocal
    def visit_Separator(self, node):
        if not self._in_dropdown:
            raise RuntimeError('Cannot render separator outside Subgroup.')
        return tags.li(role='separator', _class='divider')

    def visit_Subgroup(self, node):
        if not self._in_dropdown:
            li = tags.li(_class='dropdown')
            if node.active:
                li['class'] = 'active'
            a = li.add(tags.a(node.title, href='#', _class='dropdown-toggle'))
            a['data-toggle'] = 'dropdown'
            a['role'] = 'button'
            a['aria-haspopup'] = 'true'
            a['aria-expanded'] = 'false'
            a.add(tags.span(_class='caret'))

            ul = li.add(tags.ul(_class='dropdown-menu'))

            self._in_dropdown = True
            for item in node.items:
                ul.add(self.visit(item))
            self._in_dropdown = False

            return li
        else:
            raise RuntimeError('Cannot render nested Subgroups')

    # noinspection PyMethodMayBeStatic
    def visit_View(self, node):
        item = tags.li()
        item.add(tags.a(node.text, href=node.get_url(), title=node.text))
        if node.active:
            item['class'] = 'active'

        return item


def top_nav():
    # user_id = login_manager.id_attribute
    # log.info('__init__.top_nav() called; user_id = {}'.format(user_id))
    if user_logged_in and hasattr(current_user, 'is_admin') and current_user.is_admin:
        return Navbar('Chronos/Admin',
                      View('Home', 'auth.index'),
                      View('Balance', 'user.balance'),
                      View('Orders', 'user.orders'),
                      View('Profile', 'user.profile'),
                      View('API Keys', 'ApiKeyView:index'),
                      View('Dashboard', 'admin.dashboard'),
                      View('Exchanges', 'ExchangeView:index'),
                      View('Users', 'UserView:index'),
                      View('Theme - test', 'auth.theme_test'),
                      View('Logout', 'auth.logout'))
    elif user_logged_in and hasattr(current_user, 'is_admin'):
        return Navbar('Chronos',
                      View('Home', 'auth.index'),
                      View('Balance', 'user.balance'),
                      View('Orders', 'user.orders'),
                      View('Profile', 'user.profile'),
                      View('API Keys', 'ApiKeyView:index'),
                      View('Logout', 'auth.logout'))
    else:
        return Navbar('Chronos',
                      View('Home', 'auth.index'),
                      View('Sign Up', 'auth.signup'),
                      View('Login', 'auth.login'))