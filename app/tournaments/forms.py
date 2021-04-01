from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField, DecimalField, DateTimeField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError
from app.tournaments.utils import *
from app.models import *
from app import songlist_pairs
from titles import titles

class TournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired()])
    description = StringField('Description')
    picture = FileField('Tournament Icon (Optional)', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    submit = SubmitField('Submit')
    contact_info = StringField('Contact Information')
    skill_lvl = SelectField('Skill Level', coerce=str, choices=(('Beginner', 'Beginner'),
                                                                ('Intermediate', 'Intermediate'),
                                                                ('Advanced', 'Advanced'),
                                                                ('Expert', 'Expert'),
                                                                ('Master', 'Master'),),
                                                                validators=[DataRequired()])
    titles_required = SelectMultipleField('Required Titles', coerce=str, choices=[(title, title) for title in titles], validators=[DataRequired()])
    signup_start_time = DateTimeField(validators=[DataRequired()])
    signup_end_time = DateTimeField(validators=[DataRequired()])
    score_type = SelectField('Score Type', coerce=str, choices=list(score_types.items()), validators=[DataRequired()])

    def validate_signup_end_time(form, field):
        if field.data < form.signup_start_time.data:
            raise ValidationError("Signup end time must be after the start time!")

class MatchForm(FlaskForm):
    participants = SelectField('Participants', coerce=str, validators=[DataRequired()])
    start_time = DateTimeField(validators=[DataRequired()])
    end_time = DateTimeField(validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_end_time(form, field):
        if field.data < form.start_time.data:
            raise ValidationError("End time must be after the start time!")

class GameForm(FlaskForm):
    song = SelectField('Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    submit = SubmitField('Submit')