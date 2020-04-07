from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
# from flask_wtf import RecaptchaField
# from wtforms import SelectField, DateField
# from wtforms.validators import URL


class ContactForm(FlaskForm):
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
    """Sign up for a user account."""
    css_class = "input is-large"
    username = StringField('Username',
                           [DataRequired()],
                           render_kw={'class': css_class, 'placeholder': 'Username', 'autofocus': ''})
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': css_class, 'placeholder': 'Email'})
    password = PasswordField('Password',
                             [DataRequired(message="Please enter a password."),
                              EqualTo('confirm_password', message='Passwords must match')],
                             render_kw={'class': css_class, 'placeholder': 'Password'})
    confirm_password = PasswordField('Repeat Password',
                                     render_kw={'class': css_class, 'placeholder': 'Repeat Password'})
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
    submit = SubmitField('Send', render_kw={"class": "button is-block is-info is-large is-fullwidth"})


class LoginForm(FlaskForm):
    css_class = "input is-large"
    email = StringField('Email',
                        [Email(message='Not a valid email address.'), DataRequired()],
                        render_kw={'class': css_class, 'placeholder': 'Email', 'autofocus': ''})
    password = PasswordField('Password',
                             [DataRequired(message='Please enter a password.')],
                             render_kw={'class': css_class, 'placeholder': 'Password'})
    remember = BooleanField('Remember me', false_values=False, render_kw={'value': 'n'})
    submit = SubmitField('Send', render_kw={'class': 'button is-block is-info is-large is-fullwidth'})
