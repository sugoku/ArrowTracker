from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from flask_login import current_user
from app.models import User
from app import songlist_pairs, raw_songdata, judgement_pairs
from app.scores.utils import *

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    # if RECAPTCHA_ENABLED: recaptcha = RecaptchaField()
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That user already exists!')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email has already been taken!')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Submit')

class UpdateAccountForm(FlaskForm):
    picture = FileField('Upload a Profile Image', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio (Max 500 chars)', validators=[Length(max=500)])
    favsong = SelectField('Favourite Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That user already exists!')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email has already been taken!')

class UpdateAccountPrimeServerForm(UpdateAccountForm):
    ign = StringField('PrimeServer Username', validators=[DataRequired(), Length(min=1, max=12)])
    noteskin = SelectField('Preferred Noteskin', coerce=int, choices=list(prime_noteskin.items()), validators=[InputRequired(), NumberRange(min=0)])
    scrollspeed = DecimalField('Preferred Speed Mod', places=1, validators=[NumberRange(min=0, max=5)])
    judgement = SelectField('Preferred Judgement', coerce=str, choices=judgement_pairs, validators=[DataRequired()])
    psupdate = BooleanField('Force these settings every round in PrimeServer')

    def validate_username_primeserver(self, ign):
        if ign.data != current_user.ign:
            user = User.query.filter_by(ign=ign.data).first()
            if user:
                raise ValidationError('That PrimeServer username already exists!')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with this email!')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Reset')

class APIKeyForm(FlaskForm):
    class Meta:
        csrf = False
    name = StringField('Machine Name', validators=[DataRequired(), Length(min=1, max=50)])
    country = StringField('Country ID', validators=[DataRequired(), Length(min=1, max=2)])

class MessageForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=1, max=100)])
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=1, max=10000)])
    submit = SubmitField('Submit')