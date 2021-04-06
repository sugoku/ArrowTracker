from flask import (render_template, url_for, flash, redirect, request, abort, Blueprint, current_app)
from flask_login import current_user, login_required
from app import db, logging, roles_required
from app.models import *
from app.pump_models import *
from app.users.utils import update_user_sp
from app.scores.forms import ScoreForm
from app.scores.utils import *
from app.main.utils import *
import os
import json
from weekly import get_current_weekly, randomize_weekly
from calc_performance import calc_performance
from sqlalchemy import and_

scores = Blueprint('scores', __name__)

@scores.route('/post/new_score', methods=["GET", "POST"])
@login_required
def new_score():
    form = ScoreForm()
    if flask.request.method == "GET":
        form.song.data = request.form.get('song')
        form.lettergrade.data = request.form.get('lettergrade')
        form.stagepass.data = request.form.get('stagepass')
        form.platform.data = request.form.get('platform')
        try:
            if request.form.get('score') is not None:
                form.score.data = int(request.form.get('score'))
            if request.form.get('perfect') is not None:
                form.perfect.data = int(request.form.get('perfect'))
            if request.form.get('great') is not None:
                form.great.data = int(request.form.get('great'))
            if request.form.get('good') is not None:
                form.good.data = int(request.form.get('good'))
            if request.form.get('bad') is not None:
                form.bad.data = int(request.form.get('bad'))
            if request.form.get('miss') is not None:
                form.miss.data = int(request.form.get('miss'))
            if request.form.get('maxcombo') is not None:
                form.maxcombo.data = int(request.form.get('maxcombo'))
            if request.form.get('noteskin') is not None:
                form.noteskin.data = int(request.form.get('noteskin'))
            if request.form.get('rushspeed') is not None:
                form.rushspeed.data = float(request.form.get('rushspeed'))
        except:
            pass
        form.gamemix.data = request.form.get('gamemix')
        form.ranked.data = request.form.get('ranked')
        form.judgement.data = request.form.get('judgement')
    current_app.logger.info(request.form)
    if form.validate_on_submit():
        current_app.logger.info("Form validated.")
        difficulty = request.form.get('diffDrop')
        try:
            file = request.files['file']
        except:
            picture_file = "None"
            file = None
            flash('No file uploaded', 'info')
        if file.filename != '':
            if file and allowed_file(file.filename):
                picture_file = save_picture(file, 'score')
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                picture_file = "None"
                flash('You can\'t upload that!', 'error')
        else:
            picture_file = "None"
        current_app.logger.info("Converting to post type...")
        chart = Chart.query.get(form.chart_id.data)
        if chart is None:
            flash('Error: chart does not exist. Weird.', 'error')
        post = Post(
            song_id = chart.song.id,
            score = form.score.data,
            exscore = calc_exscore(form.perfect.data, form.great.data, form.good.data, form.bad.data, form.miss.data),
            lettergrade = form.lettergrade.data, 
            chart_id = chart.id,
            platform = form.platform.data, 
            stagepass = form.stagepass.data, 
            perfect = form.perfect.data,
            great = form.great.data,
            good = form.good.data,
            bad = form.bad.data,
            miss = form.miss.data,
            maxcombo = form.maxcombo.data,
            modifiers = mods_to_int(request.form.getlist('modifiers'), form.judgement.data),
            noteskin = form.noteskin.data,
            rushspeed = form.rushspeed.data if form.rushspeed.data != None else 1.0,
            gamemix_id = form.gamemix_id.data,
            # version_id = form.version_id.data,
            ranked = form.ranked.data, 
            length_id = chart.song.length_id, 
            acsubmit = False,
            author = current_user,
            image_file = picture_file
        )
        if current_app.debug:
            current_app.logger.debug("Created Post object, checking post...")
        analysis = check_post(post)
        if analysis == POST_APPROVED:
            approve_post(post)
            flash('Score has been submitted!', 'success')
        elif analysis == POST_PENDING:
            queue_post(post)
            flash('Score has been submitted for moderator review.', 'success')
        elif analysis == POST_UNRANKED:
            unrank_post(post)
            flash('Score has been submitted as unranked!', 'success')
        # elif analysis == POST_DRAFT:  # i don't think this should happen
        #     draft_post(post)
        #     flash('Score draft has been saved!', 'success')
        elif analysis == None:
            flash('Error: your score contains something that is impossible and was rejected. Please try again, making sure your info is correct.', 'error')
        # handle any other cases
        else:
            flash('Error: something odd happened. Please try again.', 'error')
        return redirect(url_for('main.home'))
    return render_template("new_score.html", title="New Score", form=form)

@scores.route('/post/<int:score_id>')
def score(score_id):
    bluegrades = ['a', 'b', 'c', 'd']
    goldgrades = ['s', 'ss', 'sss']
    redgrades = ['f']
    score = Post.query.get_or_404(score_id)
    songtitle = SongTitle.query.join(Language).filter_by(song=score.song).filter(Language.code == 'en').first()
    if songtitle is None:
        current_app.logger.error("Error: song title not found for song ID {score.song.id}!")
        abort(500)

    if score.status != POST_APPROVED and not (score.author == current_user or current_user.has_any_role("Moderator", "Admin")):
        current_app.logger.info(f"Access denied for user {current_user} to access score {score_id}, returning 404")
        abort(404)

    return render_template('score.html', score=score, songtitle=songtitle, length=score.length, bluegrades=bluegrades, goldgrades=goldgrades, redgrades=redgrades, int_to_mods=int_to_mods, modlist_to_modstr=modlist_to_modstr, int_to_noteskin=int_to_noteskin)

@scores.route('/post/<int:score_id>/edit', methods=["GET", "POST"])
def edit_score(score_id):
    form = ScoreForm()
    current_app.logger.info(request.form)

    post = Post.query.get(score_id)
    if not post or not (post.author == current_user or current_user.has_any_role("Moderator", "Admin")):
        current_app.logger.info(f"Access denied for user {current_user} to edit score {score_id}, returning 403")
        abort(403)

    if flask.request.method == "GET":
        form.score.data = post.score
        form.lettergrade.data = post.lettergrade
        form.platform.data = post.platform
        form.stagepass.data = post.stagepass
        form.perfect.data = post.perfect
        form.great.data = post.great
        form.good.data = post.good
        form.bad.data = post.bad
        form.miss.data = post.miss
        form.maxcombo.data = post.maxcombo
        modifiers, form.judgement.data = int_to_mods(post.modifiers, separate_judge=True)
        form.noteskin.data = post.noteskin
        form.rushspeed.data = post.rushspeed
        form.ranked.data = post.ranked

        if request.form.get('lettergrade') is not None:
            form.lettergrade.data = request.form.get('lettergrade')
        if request.form.get('stagepass') is not None:
            form.stagepass.data = request.form.get('stagepass')
        if request.form.get('platform') is not None:
            form.platform.data = request.form.get('platform')
        try:
            if request.form.get('score') is not None:
                form.score.data = int(request.form.get('score'))
            if request.form.get('perfect') is not None:
                form.perfect.data = int(request.form.get('perfect'))
            if request.form.get('great') is not None:
                form.great.data = int(request.form.get('great'))
            if request.form.get('good') is not None:
                form.good.data = int(request.form.get('good'))
            if request.form.get('bad') is not None:
                form.bad.data = int(request.form.get('bad'))
            if request.form.get('miss') is not None:
                form.miss.data = int(request.form.get('miss'))
            if request.form.get('maxcombo') is not None:
                form.maxcombo.data = int(request.form.get('maxcombo'))
            if request.form.get('noteskin') is not None:
                form.noteskin.data = int(request.form.get('noteskin'))
            if request.form.get('rushspeed') is not None:
                form.rushspeed.data = float(request.form.get('rushspeed'))
        except:
            pass
        if request.form.get('gamemix') is not None:
            form.gamemix.data = request.form.get('gamemix')
        if request.form.get('ranked') is not None:
            form.ranked.data = request.form.get('ranked')
        if request.form.get('judgement') is not None:
            form.judgement.data = request.form.get('judgement')

    if form.validate_on_submit():
        current_app.logger.info("Form validated.")
        difficulty = request.form.get('diffDrop')
        try:
            file = request.files['file']
        except:
            picture_file = "None"
            file = None
            flash('No file uploaded', 'info')
        if file.filename != '':
            if file and allowed_file(file.filename):
                picture_file = save_picture(file, 'score')
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                picture_file = "None"
                flash('You can\'t upload that!', 'error')
        else:
            picture_file = "None"
        current_app.logger.info("Updating post info...")
        # instead of converting form to a post, edit an existing post ID and update some info
        post = Post.query.get(score_id)

        post.score = form.score.data
        post.exscore = calc_exscore(form.perfect.data, form.great.data, form.good.data, form.bad.data, form.miss.data)
        post.lettergrade = form.lettergrade.data
        post.platform = form.platform.data
        post.stagepass = form.stagepass.data
        post.perfect = form.perfect.data
        post.great = form.great.data
        post.good = form.good.data
        post.bad = form.bad.data
        post.miss = form.miss.data
        post.maxcombo = form.maxcombo.data
        post.modifiers = mods_to_int(request.form.getlist('modifiers'), form.judgement.data)
        post.noteskin = form.noteskin.data
        post.rushspeed = form.rushspeed.data if form.rushspeed.data != None else 1.0
        post.ranked = form.ranked.data
        if picture_file != None:
            post.image_file = picture_file 
        
        # SP should always be calculated in score submission, non-approved posts will get ignored
        post.sp = calc_performance(Post.query.get(post.chart_id).first(), post.perfect, post.great, post.good, post.bad, post.miss, int_to_judge(post.modifiers), post.rushspeed, post.stagepass == "True")
        
        # if already unranked before, do not set to pending
        post.status = POST_PENDING if post.sp >= 0 and post.status != POST_UNRANKED else POST_UNRANKED
        if post.acsubmit:
            post.status = POST_APPROVED
        
        current_app.logger.info("Committing to database...")
        db.session.commit()

        update_user_sp(current_user)
        current_app.logger.info("Updated user SP.")
        
        flash('Score has been edited! If your score was approved before it has re-entered the moderator queue. If it was unranked it stays unranked.', 'success')
        return redirect(url_for('scores.score', score_id=score_id))
    # generate form from post here
    return render_template("new_score.html", title="Edit Score", form=form, currpost=post)

@scores.route('/post/<int:score_id>/accept', methods=["POST"])
def accept_score(score_id):
    if not current_user.has_any_role("Moderator", "Admin"):
        current_app.logger.info(f"Access denied for user {current_user} to accept score {score_id}, returning 403")
        abort(403)

    score = Post.query.get_or_404(score_id)

    approve_post(score)
    flash('The score has been accepted!', 'success')

    return redirect(url_for('main.home'))

@scores.route('/post/<int:score_id>/delete', methods=["POST"])
def delete_score(score_id):
    score = Post.query.get(score_id)

    if not score or not (score.author == current_user or current_user.has_any_role("Moderator", "Admin")):
        current_app.logger.info(f"Access denied for user {current_user} to delete score {score_id}, returning 403")
        abort(403)
    
    if score.image_file != "None":
        try:
            os.remove(os.path.join(current_app.root_path, pic_directories['score'], score.image_file))
        except:
            flash('Score screenshot couldn\'t be found.', 'info')
    db.session.delete(score)
    db.session.commit()
    update_user_sp(score.author)
    flash('The score has been deleted!', 'success')

    return redirect(url_for('main.home'))

@scores.route('/challenge/weekly', methods=["GET", "POST"])
@login_required
def weekly():
    weekly_id = get_current_weekly()
    weekly_chart = Chart.query.get(weekly_id)
    if weekly_chart is None:
        current_app.logger.error('Weekly chart could not be found!')
        abort(500)
    # https://stackoverflow.com/questions/6558535/find-the-date-for-the-first-monday-after-a-given-date
    last_monday = datetime.date.today() - datetime.timedelta(days=date.weekday())
    next_monday = datetime.date.today() + datetime.timedelta(days=(-date.weekday()+7)%7)
    ldb = Post.query.filter_by(chart_id=weekly_id, status=POST_APPROVED).filter(Post.date_posted >= last_monday,
                                                                    Post.date_posted <= next_monday).order_by(Post.score.desc()).all()
    return render_template('weekly.html', current_weekly=weekly_chart, ldb=ldb)

@scores.route('/leaderboard/main')
def main_ldb():
    users = User.query.filter(User.sp != 0).order_by(User.sp.desc()).all()
    ldbtype = "Main"
    return render_template('ldbsp.html', users=users, ldbtype=ldbtype)

@scores.route('/leaderboard/total')
def total_ldb():
    users = User.query.all()
    scores = {}
    ldbtype = "Total Score"
    for user in users:
        usertotal = []
        allscores = Post.query.filter_by(author=user, status=POST_APPROVED).all()
        for score in allscores:
            usertotal.append(score.score)
        total = sum(usertotal)
        if total != 0:
            scores[user.username] = total
        scores = {k:v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
    return render_template('ldb.html', scores=scores, ldbtype=ldbtype)

@scores.route('/leaderboard/singles')
def singles_ldb():
    users = User.query.all()
    scores = {}
    ldbtype = "Singles Total"
    for user in users:
        usertotal = []
        allscores = Post.query.filter_by(author=user, status=POST_APPROVED).all()
        for score in allscores:
            if score.type.startswith('s'):
                usertotal.append(score.score)
        total = sum(usertotal)
        if total != 0:
            scores[user.username] = total
        scores = {k:v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
    return render_template('ldb.html', scores=scores, ldbtype=ldbtype)

@scores.route('/leaderboard/doubles')
def doubles_ldb():
    users = User.query.all()
    scores = {}
    ldbtype = "Doubles Total"
    for user in users:
        usertotal = []
        allscores = Post.query.filter_by(author=user, status=POST_APPROVED).all()
        for score in allscores:
            if score.type.startswith('d'):
                usertotal.append(score.score)
        total = sum(usertotal)
        if total != 0:
            scores[user.username] = total
        scores = {k:v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
    return render_template('ldb.html', scores=scores, ldbtype=ldbtype)

@scores.route('/completion/<string:user>')
@login_required
def completion(user):
    completion = return_completion(user, "singles")
    return render_template('completion.html', completion=completion)

@roles_required(['Moderator', 'Admin'])
@scores.route('/modqueue')
def mod_queue():
    scores = Post.query.filter_by(status=POST_PENDING).order_by(Post.date_posted.desc()).all()
    return render_template('modqueue.html', scores=scores)

@login_required
@scores.route('/postqueue')
def post_queue():
    scores = Post.query.filter_by(and_(author=current_user, status=POST_PENDING)).order_by(Post.date_posted.desc()).all()
    return render_template('postqueue.html', scores=scores)