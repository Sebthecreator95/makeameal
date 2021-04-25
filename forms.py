from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, URL, Optional




class SignUpForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[Optional(),URL()])
    password = PasswordField('Password', validators=[Length(min=6)])


class LogInForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class DeleteForm(FlaskForm):
    """Delete form -- this form is intentionally blank."""
