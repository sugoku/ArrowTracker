from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
import wtforms
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional
from app import songlist_pairs, chart_pairs, judgement_pairs, category_pairs, gamemix_pairs
from app.models import post_status
from app.scores.utils import *

# Form classes defined here are what show up on the website as text inputs, dropdowns, etc.
# This for is for the leaderboard search.
class SearchForm(FlaskForm):
    # filters = [(k, v) for k, v in post_status.items()]
    comparators = (
        ('==', '=='), 
        ('!=', '!='), 
        ('>', '>'),
        ('<', '<'),
        ('>=', ">="),
        ('<=', "<=")
    )
    chart_id = SelectField('Chart', coerce=int, choices=chart_pairs)
    category_id = SelectField('Category', coerce=int, choices=category_pairs)
    minbpm = IntegerField('Minimum BPM', validators=[Optional(), NumberRange(min=0)])
    maxbpm = IntegerField('Maximum BPM', validators=[Optional(), NumberRange(min=0)])
    lettergrade = SelectMultipleField('Letter Grade', coerce=str, choices=(('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')))
    scoremodifier = SelectField('Score Search Type', coerce=str, choices=comparators, validators=[DataRequired()])
    score = IntegerField('Score', validators=[Optional(), NumberRange(min=0)])
    exscoremodifier = SelectField('EX Score Search Type', coerce=str, choices=comparators, validators=[DataRequired()])
    exscore = IntegerField('EX Score', validators=[Optional(), NumberRange(min=0)])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('Any', 'Any'), ('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    # filters = SelectMultipleField('Filter', coerce=str, choices=filters)
    platform = SelectMultipleField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'Simulator using Keyboard'), ('sf2-pad', 'Simulator using Pad')))
    perfect = IntegerField('Perfect', validators=[Optional(), NumberRange(min=0)])
    great = IntegerField('Great', validators=[Optional(), NumberRange(min=0)])
    good = IntegerField('Good', validators=[Optional(), NumberRange(min=0)])
    bad = IntegerField('Bad', validators=[Optional(), NumberRange(min=0)])
    miss = IntegerField('Miss', validators=[Optional(), NumberRange(min=0)])
    maxcombo = IntegerField('Max Combo', validators=[Optional(), NumberRange(min=0)])
    #scrollspeed = DecimalField('Scroll Speed', places=1, validators=[NumberRange(min=0)])
    #autovelocity = IntegerField('Auto Velocity Speed', validators=[NumberRange(min=0)])
    noteskin = SelectMultipleField('Noteskin', coerce=int, choices=[(-1, 'Any')] + list(other_noteskin.items()) + list(prime_noteskin.items()), validators=[DataRequired()])
    rushspeed = DecimalField('Rush Speed', places=1, validators=[Optional(), NumberRange(min=0.7, max=1.5)])
    gamemix_id = SelectMultipleField('Game Mix', coerce=int, choices=gamemix_pairs)
    #gameversion = SelectMultipleField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in gameversion_pairs])
    ranked = SelectField('Rank Mode', coerce=str, choices=(('Any', 'Any'), ('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    judgement = SelectMultipleField('Judgement', coerce=str, choices=judgement_pairs)
    #tournamentid = IntegerField('Tournament ID', validators=[NumberRange(min=0)])
    author = StringField('Author', validators=[wtforms.validators.Length(min=3, max=20)])
    submit = SubmitField('Search')

class ChartSearchForm(FlaskForm):
    filters = (
    ("all", "All"),
    ("verified", "Verified (AC)"),
    ("prime-verified", "Verified through PrimeServer (AC)"),
    ("unverified", "Unverified (SM/StepF2)"),
    ("old", "Old System (Only 'None' Lengths)"))
    song = SelectField('Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    filters = SelectField('Filter', coerce=str, choices=filters, validators=[DataRequired()])
    submit = SubmitField('Search')