from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional
from app import songlist_pairs, raw_songdata, judgement_pairs
from app.scores.utils import *

# Form classes defined here are what show up on the website as text inputs, dropdowns, etc.
# This for is for the leaderboard search.
class SearchForm(FlaskForm):
    filters = (
        ("all", "All"),
        ("verified", "Verified (AC)"),
        ("prime-verified", "Verified through PrimeServer (AC)"),
        ("unverified", "Unverified (SM/StepF2)"),
        ("old", "Old System (Only 'None' Lengths)")
    )
    comparators = (
        ('==', '=='), 
        ('!=', '!='), 
        ('>', '>'),
        ('<', '<'),
        ('>=', ">="),
        ('<=', "<=")
    )
    song = SelectField('Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs])
    lettergrade = SelectMultipleField('Letter Grade', coerce=str, choices=(('Any', 'Any'), ('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')), validators=[DataRequired()])
    scoremodifier = SelectField('Score Search Type', coerce=str, choices=comparators, validators=[DataRequired()])
    score = IntegerField('Score', validators=[Optional(), NumberRange(min=0)])
    exscoremodifier = SelectField('EX Score Search Type', coerce=str, choices=comparators, validators=[DataRequired()])
    exscore = IntegerField('EX Score', validators=[Optional(), NumberRange(min=0)])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('Any', 'Any'), ('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    filters = SelectMultipleField('Filter', coerce=str, choices=filters, validators=[DataRequired()])
    platform = SelectMultipleField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'SF2 Keyboard'), ('sf2-pad', 'SF2 Pad')))
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
    #gamemix = SelectMultipleField('Game Mix', coerce=str, choices=gamemix_pairs)
    #gameversion = SelectMultipleField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in gameversion_pairs])
    ranked = SelectMultipleField('Rank Mode', coerce=str, choices=(('Any', 'Any'), ('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    judgement = SelectMultipleField('Judgement', coerce=str, choices=(('Any', 'Any'),) + judgement_pairs, validators=[DataRequired()])
    #tournamentid = IntegerField('Tournament ID', validators=[NumberRange(min=0)])
    author = StringField('Author')
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

class TournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired()])
    description = StringField('Description')
    bracketlink = StringField('Bracket Link (Challonge or other)')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    submit = SubmitField('Submit')
    contactinfo = StringField('Contact Information')
    skill_lvl = SelectField('Skill Level', coerce=str, choices=(('Beginner', 'Beginner'),
                                                                ('Intermediate', 'Intermediate'),
                                                                ('Advanced', 'Advanced')),
                                                                validators=[DataRequired()])

class TournamentEditForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired()])
    description = StringField('Description')
    bracketlink = StringField('Bracket Link (Challonge or other)')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    submit = SubmitField('Submit')
    contactinfo = StringField('Contact Information')
    skill_lvl = SelectField('Skill Level', coerce=str, choices=(('Beginner', 'Beginner'),
                                                                ('Intermediate', 'Intermediate'),
                                                                ('Advanced', 'Advanced')),
                                                                validators=[DataRequired()])
