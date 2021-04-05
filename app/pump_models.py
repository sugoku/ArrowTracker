# coding: utf-8
# uses pumpout.db as a base but is redone in a new format
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

songartists = db.Table('songartists',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
    info={'bind_key': 'pump'}
)

songcharts = db.Table('songcharts',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('chart_id', db.Integer, db.ForeignKey('chart.id'), primary_key=True),
    info={'bind_key': 'pump'}
)

songversions = db.Table('songversions',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('version_id', db.Integer, db.ForeignKey('version.id'), primary_key=True),
    info={'bind_key': 'pump'}
)

songversions = db.Table('songversions',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('version_id', db.Integer, db.ForeignKey('version.id'), primary_key=True),
    db.Column('operation', db.String(10), nullable=True),
    info={'bind_key': 'pump'}
)
class Song(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.String(5), nullable=False, default='')
    length = db.Column(db.Integer, db.ForeignKey('length.id'), nullable=False)
    artist = db.Column(db.String(127), nullable=True)
    artists = db.relationship('Artist', secondary=songartists, lazy='subquery', backref=db.backref('songs', lazy=True))
    bpm_min = db.Column(db.Float, nullable=False, default=0.0)
    bpm_max = db.Column(db.Float, nullable=False, default=0.0)
    card = db.Column(db.String(127), nullable=True)
    charts = db.relationship('Chart', backref='song', lazy=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    internal_title = db.Column(db.String(127), nullable=False, default="")
    titles = db.relationship('SongTitle', backref='song', lazy=True)
    versions = db.relationship('Version', secondary=songversions, lazy='subquery', backref=db.backref('songs', lazy=True))

chartlabels = db.Table('chartlabels',
    db.Column('chart_id', db.Integer, db.ForeignKey('chart.id'), primary_key=True),
    db.Column('label_id', db.Integer, db.ForeignKey('label.id'), primary_key=True),
    info={'bind_key': 'pump'}
)

chartstepmakers = db.Table('chartstepmakers',
    db.Column('chart_id', db.Integer, db.ForeignKey('chart.id'), primary_key=True),
    db.Column('stepmaker_id', db.Integer, db.ForeignKey('stepmaker.id'), primary_key=True),
    info={'bind_key': 'pump'}
)

class Chart(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    labels = db.relationship('Label', secondary=chartlabels, lazy='subquery', backref=db.backref('charts', lazy=True))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    difficulties = db.relationship('ChartDifficulty', backref='chart', lazy=True)
    mode_id = db.Column(db.Integer, db.ForeignKey('mode.id'), nullable=False)  # no relationship for this one, actual relationship is in difficulties
    name = db.Column(db.String(10), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=0)
    new_rating = db.Column(db.Float, nullable=False, default=0.0)
    rerate_name = db.Column(db.String(127), nullable=False)
    stepmakers = db.relationship('Stepmaker', secondary=chartstepmakers, lazy='subquery', backref=db.backref('charts', lazy=True))
    weight = db.Column(db.Float, nullable=False, default=1.0)
    max_combo = db.Integer(db.Integer, nullable=True)

class ChartDifficulty(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    chart_id = db.Column(db.Integer, db.ForeignKey('chart.id'), nullable=False)
    mode_id = db.Column(db.Integer, db.ForeignKey('mode.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=0)
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'), nullable=False)

class Artist(db.Model):
    __bind_key__ = 'pump'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")

class Length(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

class SongTitle(db.Model):
    __bind_key__ = 'pump'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)

class Label(db.Model):
    __bind_key__ = 'pump'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    
class Mode(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")
    abbrev = db.Column(db.String(127), nullable=False, default="")
    pads_used = db.Column(db.Integer, nullable=False, default=1)
    panels_used = db.Column(db.Integer, nullable=False, default=5)
    coop = db.Column(db.Boolean, nullable=False)
    performance = db.Column(db.Boolean, nullable=False)
    chartdifficulties = db.relationship('ChartDifficulty', backref='mode', lazy=True)

class Stepmaker(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")

class Category(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    songs = db.relationship('Song', backref='category', lazy=True)

class GameMix(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), nullable=False, default="")
    parent_mix_id = db.Column(db.Integer, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    versions = db.relationship('Version', backref='gamemix', lazy=True)

class Version(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    gamemix_id = db.Column(db.Integer, db.ForeignKey('gamemix.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, default="")
    parent_version_id = db.Column(db.Integer, nullable=True)
    difficulties = db.relationship('ChartDifficulty', backref='version', lazy=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

class Language(db.Model):
    __bind_key__ = 'pump'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    songtitles = db.relationship('SongTitle', backref='language', lazy=True)