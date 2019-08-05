from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Length, InputRequired
from flask_wtf.file import FileField, FileAllowed
from app import songlist_pairs, difficulties, lengthtype_pairs, gamemix_pairs, judgement_pairs
from app.scores.utils import prime_noteskin, other_noteskin
import json

weeklydiffs = json.load(open('weekly.json', 'r'))['diffs']
weeklydiffs = list(zip(weeklydiffs, weeklydiffs))

class ScoreForm(FlaskForm):
    song = SelectField('Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    lettergrade = SelectField('Letter Grade', coerce=str, choices=(('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')), validators=[DataRequired()])
    score = IntegerField('Score', validators=[InputRequired(), NumberRange(min=0)])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    platform = SelectField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'SF2 Keyboard'), ('sf2-pad', 'SF2 Pad')), validators=[DataRequired()])
    perfect = IntegerField('Perfect', validators=[InputRequired(), NumberRange(min=0)])
    great = IntegerField('Great', validators=[InputRequired(), NumberRange(min=0)])
    good = IntegerField('Good', validators=[InputRequired(), NumberRange(min=0)])
    bad = IntegerField('Bad', validators=[InputRequired(), NumberRange(min=0)])
    miss = IntegerField('Miss', validators=[InputRequired(), NumberRange(min=0)])
    maxcombo = IntegerField('Max Combo', validators=[InputRequired(), NumberRange(min=0)])
    #scrollspeed = DecimalField('Scroll Speed', places=1, validators=[NumberRange(min=0)])
    #autovelocity = IntegerField('Auto Velocity Speed', validators=[NumberRange(min=0)])
    noteskin = SelectField('Noteskin', coerce=int, choices=list(other_noteskin.items()) + list(prime_noteskin.items()), validators=[InputRequired(), NumberRange(min=0)])
    rushspeed = DecimalField('Rush Speed', places=1, validators=[NumberRange(min=0.7, max=1.5)])
    #gamemix = SelectField('Game Mix', coerce=str, choices=gamemix_pairs)
    #gameversion = SelectField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in gameversion_pairs])
    ranked = SelectField('Ranked?', coerce=str, choices=(('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    picture = FileField('Verification Score (Optional)', validators=[FileAllowed(['jpg', 'png', 'JPG', 'PNG'])])
    judgement = SelectField('Judgement', coerce=str, choices=judgement_pairs, validators=[DataRequired()])
    #tournamentid = IntegerField('Tournament ID', validators=[NumberRange(min=0)])
    submit = SubmitField('Submit')

class WeeklyForm(FlaskForm):
    lettergrade = SelectField('Letter Grade', coerce=str, choices=(('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')), validators=[DataRequired()])
    score = IntegerField('Score', validators=[DataRequired()])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    difficulty = SelectField('Difficulty', coerce=str, choices=weeklydiffs, validators=[DataRequired()])
    platform = SelectField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'SF2 Keyboard'), ('sf2-pad', 'SF2 Pad')), validators=[DataRequired()])
    perfect = IntegerField('Perfect', validators=[InputRequired(), NumberRange(min=0)])
    great = IntegerField('Great', validators=[InputRequired(), NumberRange(min=0)])
    good = IntegerField('Good', validators=[InputRequired(), NumberRange(min=0)])
    bad = IntegerField('Bad', validators=[InputRequired(), NumberRange(min=0)])
    miss = IntegerField('Miss', validators=[InputRequired(), NumberRange(min=0)])
    maxcombo = IntegerField('Max Combo', validators=[InputRequired(), NumberRange(min=0)])
    #scrollspeed = DecimalField('Scroll Speed', places=1, validators=[NumberRange(min=0)])
    #autovelocity = IntegerField('Auto Velocity Speed', validators=[NumberRange(min=0)])
    noteskin = SelectField('Noteskin', coerce=int, choices=list(other_noteskin.items()) + list(prime_noteskin.items()), validators=[InputRequired(), NumberRange(min=0)])
    #gamemix = SelectField('Game Mix', coerce=str, choices=gamemix_pairs)
    #gameversion = SelectField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in gameversion_pairs])
    ranked = SelectField('Ranked?', coerce=str, choices=(('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    picture = FileField('Verification Score (Optional)', validators=[FileAllowed(['jpg', 'png', 'JPG', 'PNG'])])
    judgement = SelectField('Judgement', coerce=str, choices=judgement_pairs, validators=[DataRequired()])
    #tournamentid = IntegerField('Tournament ID', validators=[NumberRange(min=0)])
    submit = SubmitField('Submit')
