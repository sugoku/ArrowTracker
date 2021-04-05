import os
import logging
import traceback
import json
from flask import render_template, request, Blueprint, current_app, session, redirect, url_for, flash, Markup, jsonify
from flask_login import current_user, login_required
from app.tournaments.forms import TournamentForm
from app.scores.forms import ScoreForm
from app.users.forms import APIKeyForm
from app.main.utils import *
from app.models import Post, Tournament, Match, Game, APIKey
from app import songlist_pairs, difficulties, db, raw_songdata, approved_ips, apikey_required

tournaments = Blueprint('tournaments', __name__)

@tournaments.route("/tournaments/view")
@login_required
def view_tournaments():
    page = request.args.get('page', 1, type=int)
    tournaments = Tournament.query.order_by(Tournament.date_posted.desc()).paginate(per_page=16, page=page)
    return render_template("tournaments.html", tournaments=tournaments)

@tournaments.route("/tournaments/create", methods=["GET", "POST"])
@login_required
def create_tournament():
    form = TournamentForm(request.form)
    picture_file = "None"
    if form.validate_on_submit():
        try:
            file = request.files['file']
        except:
            file = None
            flash('No file uploaded', 'info')
        if file != None:
            if file.filename == '':
                flash('No file selected!', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                picture_file = save_picture(file, 'tournament')
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                flash('You can\'t upload that!', 'error')
        tournament = Tournament(name = form.name.data, skill_lvl = form.skill_lvl.data, description = form.description.data, bracketlink = form.bracketlink.data, image_file = picture_file, contactinfo = form.contactinfo.data, user_id = current_user.id)
        db.session.add(tournament)
        db.session.commit()
        flash('Tournament created!', 'success')
        return redirect(url_for('main.tournaments'))
    return render_template("create_tournament.html", form=form)

@tournaments.route("/tournaments/<int:tournament_id>/edit", methods=["GET", "POST"])
@login_required
def edit_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    form = TournamentForm()
    if form.validate_on_submit():
        try:
            file = request.files['file']
        except:
            picture_file = "None"
            file = None
            flash('No file uploaded', 'info')
        if file != None:
            if file.filename == '':
                flash('No file selected!', 'error')
                picture_file = "None"
                return redirect(request.url)
            if file and allowed_file(file.filename):
                picture_file = save_picture(file, 'tournament')
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                picture_file = "None"
                flash('You can\'t upload that!', 'error')
        tournament.image_file = picture_file
        tournament.name = form.name.data
        tournament.description = form.description.data
        tournament.skill_lvl = form.skill_lvl.data
        tournament.bracketlink = form.bracketlink.data
        tournament.contactinfo = form.contactinfo.data
        db.session.commit()
        flash('Tournament info updated!', 'success')
        return redirect(url_for('main.tournaments'))
    form.name.data = tournament.name
    form.description.data = tournament.description
    form.skill_lvl.data = tournament.skill_lvl
    form.bracketlink.data = tournament.bracketlink
    form.contactinfo.data = tournament.contactinfo
    if tournament.user_id != current_user.id:
        abort(403)
    return render_template('edit_tournament.html', tournament=tournament, form=form)

@tournaments.route('/tournaments/<int:tournament_id>')
def tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    return render_template('tournament.html', tournament=tournament)

@tournaments.route('/tournaments/<int:tournament_id>/match/<int:match_id>')
def tournament_match(tournament_id, match_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    match = Match.query.get_or_404(match_id)
    return render_template('tournament_match.html', tournament=tournament, match=match)

@tournaments.route('/tournaments/<int:tournament_id>/queue')
@login_required
def tournament_queue(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if current_user.id not in tournament.organizers():
        abort(403)
    return render_template('tournamentqueue.html', tournament=tournament)

@tournaments.route('/tournaments/<int:tournament_id>/matches')
@login_required
def tournament_matches(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if current_user.id not in tournament.organizers():
        abort(403)
    return render_template('tournament_matches.html', tournament=tournament)

@tournaments.route("/tournaments/<int:tournament_id>/creatematch", methods=["GET", "POST"])
@login_required
def create_match():
    form = TournamentForm(request.form)
    picture_file = "None"
    if form.validate_on_submit():
        try:
            file = request.files['file']
        except:
            file = None
            flash('No file uploaded', 'info')
        if file != None:
            if file.filename == '':
                flash('No file selected!', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                picture_file = save_picture(file, 'tournament')
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                flash('You can\'t upload that!', 'error')
        tournament = Tournament(name = form.name.data, skill_lvl = form.skill_lvl.data, description = form.description.data, bracketlink = form.bracketlink.data, image_file = picture_file, contactinfo = form.contactinfo.data, user_id = current_user.id)
        db.session.add(tournament)
        db.session.commit()
        flash('Match created!', 'success')
        return redirect(url_for('main.tournaments'))
    return render_template("create_tournament.html", form=form)


@tournaments.route('/tournaments/<int:tournament_id>/delete', methods=["POST"])
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if tournament.user_id != current_user.id:
        abort(403)
    if tournament.image_file != "None":
        os.remove(os.path.join(current_app.root_path, pic_directories['tournament'], tournament.image_file))
    db.session.delete(tournament)
    db.session.commit()
    flash('Your tournament has been deleted!', 'success')
    return redirect(url_for('main.tournaments'))
