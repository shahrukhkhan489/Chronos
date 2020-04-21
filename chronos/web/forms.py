from flask_wtf import FlaskForm
from sqlalchemy import text
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import current_user
from wtforms_sqlalchemy.fields import QuerySelectField
from chronos import log


class ContactForm(FlaskForm):
    extra_classes = "was-validated"
    css_class = ".form-horizontal.labels-left"
    field_css_class = "form-control form-control-lg"
    """Contact form."""
    name = StringField('Name', [
        DataRequired()])
    email = StringField('Email', [
        Email(message='Not a valid email address.'),
        DataRequired()])
    body = StringField('Message', [
        DataRequired(),
        Length(min=4, message='Your message is too short.')])
    # recaptcha = RecaptchaField()
    submit = SubmitField('Submit')


class SignupForm(FlaskForm):
    extra_classes = "was-validated"
    """Sign up for a user account."""
    css_class = ".form-horizontal.labels-left"
    field_css_class = "form-control form-control-lg"
    username = StringField('Username',
                           [DataRequired()],
                           render_kw={'class': field_css_class, 'placeholder': 'Username', 'autofocus': ''})
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': field_css_class, 'placeholder': 'Email'})
    password = PasswordField('Password',
                             [DataRequired(message="Please enter a password."),
                              EqualTo('confirm_password', message='Passwords must match')],
                             render_kw={'class': field_css_class, 'placeholder': 'Password'})
    confirm_password = PasswordField('Repeat Password',
                                     [DataRequired()],
                                     render_kw={'class': field_css_class, 'placeholder': 'Repeat Password'})
    # title = SelectField('Title', [DataRequired()],
    #                     choices=[('Farmer', 'farmer'),
    #                              ('Corrupt Politician', 'politician'),
    #                              ('No-nonsense City Cop', 'cop'),
    #                              ('Professional Rocket League Player', 'rocket'),
    #                              ('Lonely Guy At A Diner', 'lonely'),
    #                              ('Pokemon Trainer', 'pokemon')])
    # website = StringField('Website', validators=[URL()])
    # birthday = DateField('Your Birthday')
    # recaptcha = RecaptchaField()
    submit = SubmitField('Send', render_kw={'class': 'btn btn-primary btn-lg'})


class LoginForm(FlaskForm):
    extra_classes = "was-validated"
    css_class = ".form-horizontal labels-left"
    field_css_class = "form-control form-control-lg"
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': field_css_class, 'placeholder': 'Email', 'autofocus': ''})
    password = PasswordField('Password',
                             [DataRequired(message='Please enter a password.')],
                             render_kw={'class': field_css_class, 'placeholder': 'Password'})
    remember = BooleanField('Remember me', false_values=False, render_kw={'value': 'n'})
    submit = SubmitField('Send', render_kw={'class': 'btn btn-primary btn-lg'})


class UserForm(FlaskForm):
    extra_classes = "was-validated"
    css_class = ".form-horizontal.labels-left"
    field_css_class = "form-control form-control-lg"
    username = StringField('Username',
                           [DataRequired()],
                           render_kw={'class': field_css_class, 'placeholder': 'Username', 'autofocus': ''})
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': field_css_class, 'placeholder': 'Email'})
    password = PasswordField('Password',
                             [DataRequired(message="Please enter a password."),
                              EqualTo('confirm_password', message='Passwords must match')],
                             render_kw={'class': field_css_class, 'placeholder': 'Password'})
    confirm_password = PasswordField('Repeat Password',
                                     render_kw={'class': field_css_class, 'placeholder': 'Repeat Password'})
    submit = SubmitField('Save', render_kw={'class': 'btn btn-primary btn-lg'})


class ProfileForm(FlaskForm):
    from chronos.data_helper import get_themes

    extra_classes = ""
    css_class = ".form-horizontal.labels-left"
    field_css_class = "form-control form-control-lg"
    username = StringField('Username',
                           [DataRequired()],
                           render_kw={'class': field_css_class, 'placeholder': 'Username', 'autofocus': ''})
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': field_css_class, 'placeholder': 'Email'})
    password = PasswordField('Password',
                             [EqualTo('confirm_password', message='Passwords must match')],
                             render_kw={'class': field_css_class, 'placeholder': 'Password'})
    password.data = ""
    confirm_password = PasswordField('Repeat Password',
                                     render_kw={'class': field_css_class, 'placeholder': 'Repeat Password'})
    confirm_password.data = ""
    themes = []
    for theme in get_themes():
        themes.append([theme, theme])
    if not themes:
        themes = [('moon-base-alpha', 'moon-base-alpha')]
    theme = SelectField('Theme', choices=themes, render_kw={'class': field_css_class})

    submit = SubmitField('Save', render_kw={'class': 'btn btn-primary btn-lg'})


class ExchangeForm(FlaskForm):
    extra_classes = "was-validated"
    css_class = ".form-horizontal labels-left"
    field_css_class = "form-control form-control-lg"
    name = StringField('Name',
                       [DataRequired()],
                       render_kw={'class': field_css_class, 'placeholder': 'Name', 'autofocus': ''})
    ccxt_name = StringField('CCXT name', render_kw={'class': field_css_class, 'placeholder': 'CCXT name'})
    class_name = StringField('Class name', render_kw={'class': field_css_class, 'placeholder': 'Class name'})
    submit = SubmitField('Save', render_kw={'class': 'btn btn-primary btn-lg'})


def make_query_factory(model, _order_by=""):
    return lambda: model.query.order_by(text(_order_by)).all()


def get_primary_key(model):
    return model.id


class ApiKeyForm(FlaskForm):
    from ..model import Exchange
    title = 'Add API key pair'
    css_class = "form-control form-control-lg"
    user_id = None
    if current_user:
        user_id = current_user.id
    exchange_id = QuerySelectField('exchange_id',
                                   [DataRequired()],
                                   query_factory=make_query_factory(Exchange),
                                   get_pk=get_primary_key,
                                   allow_blank=False,
                                   render_kw={'class': css_class, 'placeholder': 'Exchange', 'autofocus': ''})
    public_key = StringField('Public Key',
                             [DataRequired()],
                             render_kw={'class': css_class, 'placeholder': 'Public Key'})
    private_key = StringField('Private Key',
                              [DataRequired()],
                              render_kw={'class': css_class, 'placeholder': 'Private Key'})
    submit = SubmitField('Save', render_kw={'class': 'button is-block is-info is-large is-fullwidth'})
