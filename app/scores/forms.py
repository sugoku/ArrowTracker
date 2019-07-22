from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Length
from flask_wtf.file import FileField, FileAllowed
from app import songlist_pairs, difficulties, lengthtype_pairs
import json

weeklydiffs = json.load(open('weekly.json', 'r'))['diffs']
weeklydiffs = list(zip(weeklydiffs, weeklydiffs))

class ScoreForm(FlaskForm):
    song = SelectField('Song', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    lettergrade = SelectField('Letter Grade', coerce=str, choices=(('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')), validators=[DataRequired()])
    score = IntegerField('Score', validators=[DataRequired()])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    platform = SelectField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'SF2 Keyboard'), ('sf2-pad', 'SF2 Pad')), validators=[DataRequired()])
    perfect = IntegerField('Perfect', validators=[DataRequired(), NumberRange(min=0)])
    great = IntegerField('Great', validators=[DataRequired(), NumberRange(min=0)])
    good = IntegerField('Good', validators=[DataRequired(), NumberRange(min=0)])
    bad = IntegerField('Bad', validators=[DataRequired(), NumberRange(min=0)])
    miss = IntegerField('Miss', validators=[DataRequired(), NumberRange(min=0)])
    maxcombo = IntegerField('Max Combo', validators=[DataRequired(), NumberRange(min=0)])
    scrollspeed = DecimalField('Scroll Speed', places=1, validators=[DataRequired(), NumberRange(min=0)])
    noteskin = SelectField('Noteskin', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    modifiers = IntegerField('Modifiers', validators=[DataRequired(), NumberRange(min=0)])
    gamemix = SelectField('Game Mix', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    gameversion = SelectField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    ranked = SelectField('Ranked?', coerce=str, choices=(('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    picture = FileField('Verification Score (Optional)', validators=[FileAllowed(['jpg', 'png', 'JPG', 'PNG'])])
    length = SelectField('Length', coerce=str, choices=lengthtype_pairs, validators=[DataRequired()])
    accesscode = HiddenField('Access Code', coerce=str, validators=[Length(min=32, max=32)])
    acsubmit = HiddenField('Submitted via Machine', coerce=str)
    submit = SubmitField('Submit')

class WeeklyForm(FlaskForm):
    lettergrade = SelectField('Letter Grade', coerce=str, choices=(('f', 'F'), ('d', 'D'), ('c', 'C'), ('b', 'B'), ('a', 'A'), ('s', 'S'), ('ss', 'SS'), ('sss', 'SSS')), validators=[DataRequired()])
    score = IntegerField('Score', validators=[DataRequired()])
    stagepass = SelectField('Stage Pass', coerce=str, choices=(('True', 'True'), ('False', 'False')), validators=[DataRequired()])
    platform = SelectField('Platform', coerce=str, choices=(('pad', 'Pad'), ('keyboard', 'SF2 Keyboard'), ('sf2-pad', 'SF2 Pad')), validators=[DataRequired()])
    perfect = IntegerField('Perfects', validators=[DataRequired(), NumberRange(min=0)])
    great = IntegerField('Greats', validators=[DataRequired(), NumberRange(min=0)])
    good = IntegerField('Goods', validators=[DataRequired(), NumberRange(min=0)])
    bad = IntegerField('Bads', validators=[DataRequired(), NumberRange(min=0)])
    miss = IntegerField('Misses', validators=[DataRequired(), NumberRange(min=0)])
    maxcombo = IntegerField('Max Combo', validators=[DataRequired(), NumberRange(min=0)])
    scrollspeed = DecimalField('Scroll Speed', places=1, validators=[DataRequired(), NumberRange(min=0)])
    noteskin = SelectField('Noteskin', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    modifiers = IntegerField('Modifiers', validators=[DataRequired(), NumberRange(min=0)])
    gamemix = SelectField('Game Mix', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    gameversion = SelectField('Version', coerce=str, choices=[tuple(map(lambda x: x.decode('utf-8'), tup)) for tup in songlist_pairs], validators=[DataRequired()])
    ranked = SelectField('Ranked?', coerce=str, choices=(('False', 'Unranked'), ('True', 'Ranked')), validators=[DataRequired()])
    picture = FileField('Verification Score (Optional)', validators=[FileAllowed(['jpg', 'png', 'JPG', 'PNG'])])
    length = SelectField('Length', coerce=str, choices=lengthtype_pairs, validators=[DataRequired()])
    submit = SubmitField('Submit')
