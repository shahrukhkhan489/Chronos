# Generate a referrer link based on the request with a fallback
from flask import request, url_for

from chronos import log


def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


def set_boolean_values(form, item):
    """
    Checkboxes are not submitted unless they are checked. So, un-checking a WTFForm.BooleanField will not return a
    false value. The workaround is to test if the name of the checkbox made it into the request. If not, we assume
    that the checkbox is un-checked. If so, we can read the value of the checkbox, but it doesn't matter because it
    should be True anyway.
    NOTE: with 2+ checkboxes with the same name, if any checkbox is checked item's attribute will be set to True.
    :param form:
    :param item:
    :return:
    """
    if request.method == "POST":
        for attr, value in vars(item).items():
            if isinstance(value, bool) and hasattr(form, attr):
                checkbox = getattr(form, attr)
                checkbox_value = request.form.get(attr) is not None  # check if the checkbox name is in the request
                log.info("{}.{} = {}".format(item, attr, checkbox_value))
                if checkbox and hasattr(checkbox, 'data'):
                    setattr(checkbox, 'data', checkbox_value)
    else:
        for attr, value in vars(item).items():
            if isinstance(value, bool) and hasattr(form, attr):
                field = getattr(form, attr)
                if field and hasattr(field, 'data'):
                    setattr(field, 'data', value)
                if field and hasattr(field, ''):
                    setattr(field, 'default', value)
