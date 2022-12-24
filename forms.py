from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, SelectField, IntegerField, RadioField
from wtforms.validators import DataRequired, EqualTo, Length, Email


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")
    
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email("This field requires a valid email address")])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 1000, "Password must containt at least 6 characters")])
    repeat_password = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo('password', "passwords don't match")])
    submit = SubmitField("Submit")

class PlaylistGenerator(FlaskForm):
    name = StringField("Playlist Name", validators=[DataRequired()])
    songs = RadioField('How many songs do you want in your playlist?', choices=[('20','20'),('30','30'),('50','50')], default='30')
    submit = SubmitField("Generate")