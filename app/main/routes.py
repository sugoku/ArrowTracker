import os
import logging
import traceback
import json
import re
from flask import render_template, request, Blueprint, current_app, session, redirect, url_for, flash, Markup, jsonify, abort
from flask_login import current_user, login_required
from app.main.forms import SearchForm, ChartSearchForm
from app.tournaments.forms import TournamentForm, TournamentEditForm
from app.scores.forms import ScoreForm
from app.users.forms import APIKeyForm
from app.models import Post, Tournament, APIKey
from app import songlist_pairs, difficulties, db, raw_songdata, approved_ips, apikey_required
from sqlalchemy import desc, or_
from app.config import GetChangelog
from app.main.utils import save_picture, allowed_file, valid_api_key, generate_unique_key
from app.users.utils import accesscode_to_user, user_to_primeprofile, update_user_with_primeprofile, update_user_sp, add_exp, add_pp
from app.scores.utils import *
from calc_performance import calc_performance
from werkzeug.exceptions import BadRequestKeyError
from sqlalchemy.sql.functions import func

# We can define all of the "@main" decorators below as a "blueprint" that
# allows us to easily call or redirect the user to any of them from anywhere.
main = Blueprint('main', __name__)

@main.context_processor
def add_songdata():
    return dict(songdata=raw_songdata)

# The route for the main homepage.
@main.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    scores = Post.query.filter_by(approved=1).order_by(Post.date_posted.desc()).paginate(per_page=15, page=page)
    # total = db.engine.execute('select count(*) from Post').scalar()
    total = db.session.execute(Post.query.filter_by(approved=1).statement.with_only_columns([func.count()]).order_by(None)).scalar()
    return render_template("home.html", scores=scores, total=total, songdata=raw_songdata)

@main.route('/about')
def about():
    return render_template("about.html")

STATUS_PENDING = 0   # For suspicious or initial scores
STATUS_APPROVED = 1
STATUS_PASS_PENDING = 2  # For PrimeServer scores

@main.route('/submit', methods=['POST'])
def submit():
    response = {
        'status': 'success'
    }
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            if int(request.form['Score']) > 0:
                if current_app.debug:
                    current_app.logger.debug("Score above 0, submitting score...")
                u = accesscode_to_user(request.form['AccessCode'].lower())
                if u == None:
                    current_app.logger.error("Access code does not resolve to a valid user!")
                    raise
                s = id_to_songname(hex(int(request.form['SongID'])).replace('0x', '').upper())
                if s == None:
                    current_app.logger.error("Song ID does not resolve to a valid song!")
                    raise
                post = Post(
                    approved = STATUS_PASS_PENDING,
                    song = s,
                    song_id = int(request.form['SongID']),
                    score = int(request.form['Score']),
                    exscore = calc_exscore(int(request.form['Perfect']), int(request.form['Great']), int(request.form['Good']), int(request.form['Bad']), int(request.form['Miss'])),
                    lettergrade = prime_grade[int(request.form['Grade']) % 0x100],
                    type = prime_charttype[int(request.form['Type'])],
                    difficultynum = int(request.form['ChartLevel']),
                    difficulty = get_diffstr(prime_charttype[int(request.form['Type'])], int(request.form['ChartLevel'])),
                    platform = 'pad',
                    perfect = int(request.form['Perfect']),
                    great = int(request.form['Great']),
                    good = int(request.form['Good']),
                    bad = int(request.form['Bad']),
                    miss = int(request.form['Miss']),
                    maxcombo = int(request.form['MaxCombo']),
                    pp = int(request.form['PP']),
                    runningstep = int(request.form['RunningStep']),
                    kcal = float(request.form['Kcal']),
                    scrollspeed = (int(request.form['NoteSkinSpeed']) % 0x100) / 4.0,
                    noteskin = int(request.form['NoteSkinSpeed']) // 0x10000,
                    modifiers = int(request.form['Modifiers']),
                    rushspeed = float(request.form['RushSpeed']),
                    #gamemix = request.form['Gamemix'],
                    gameversion = request.form['GameVersion'],
                    gameflag = int(request.form['Flag']),
                    ranked = 'True' if request.form['Flag'] == '128' else 'False',
                    #length = prime_songcategory[int(request.form['SongCategory'])],
                    length = raw_songdata[s]['length'], 
                    accesscode = request.form['AccessCode'],
                    acsubmit = 'True',
                    user_id = u.id
                )
                if current_app.debug:
                    current_app.logger.debug("Created post object.")
                prime_to_xx_diff(post)
                if current_app.debug:
                    current_app.logger.debug("Converted Prime difficulty to XX difficulty.")
                if post.difficulty == None or post.difficulty == '':
                    raise
                if post.rushspeed == 0.0:
                    post.rushspeed = 1.0
                song_maxcombo = post.perfect+post.great+post.good+post.bad+post.miss
                if song_maxcombo > get_max_combo(post.song, post.difficulty):
                    update_max_combo(post.song, post.difficulty, song_maxcombo)
                    update_song_list()
                    if current_app.debug:
                        current_app.logger.debug("Updated max combo for song %s, difficulty %s with max combo of %s" % (post.song, post.difficulty, song_maxcombo))
                post.sp = calc_performance(post.song, post.difficulty, post.difficultynum, post.perfect, post.great, post.good, post.bad, post.miss, int_to_judge(post.modifiers), post.rushspeed, post.stagepass == "True")
                add_exp(u, int(request.form['EXP']))
                add_pp(u, int(request.form['PP']))
                if current_app.debug:
                    current_app.logger.debug("EXP and PP added to profile.")
                if high_score(post):
                    if current_app.debug:
                        current_app.logger.debug("High score detected, saving score...")
                    del_high_score(post)
                    db.session.add(post)
                    db.session.commit()
                    if current_app.debug:
                        current_app.logger.debug("Committed score to database.")
                    update_user_sp(u)
                    if current_app.debug:
                        current_app.logger.debug("User SP updated.")
                elif current_app.debug:
                    current_app.logger.debug("High score not detected, not saving score.")
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to submit through PrimeServer: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            if isinstance(e, BadRequestKeyError):
                current_app.logger.error(json.dumps(request.form, indent=4))
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error submitting through PrimeServer: %s' % traceback.format_exc())
    return jsonify(response)

@main.route('/getprofile', methods=['GET'])
def getprofile():
    response = {}
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            u = accesscode_to_user(request.args.get('access_code').lower())
            if u == None:
                current_app.logger.error("Access code does not resolve to a valid user!")
                raise
            return jsonify(user_to_primeprofile(u))
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to get PrimeServer profile: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error getting PrimeServer profile: %s' % traceback.format_exc())
    return jsonify(response)

@main.route('/saveprofile', methods=['POST'])
def saveprofile():
    response = {
        'status': 'success'
    }
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            u = accesscode_to_user(request.form['AccessCode'].lower())
            if u == None:
                current_app.logger.error("Access code does not resolve to a valid user!")
                raise
            update_user_with_primeprofile(u, request.form)
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to save PrimeServer profile: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            if isinstance(e, BadRequestKeyError):
                temp = request.form.copy()
                temp.pop('Scores', None)
                current_app.logger.error(json.dumps(temp, indent=4))
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error saving PrimeServer profile: %s' % traceback.format_exc())
    return jsonify(response)

@main.route('/getworldbest', methods=['GET'])
def getworldbest():
    response = {}
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            return jsonify(get_worldbest(scoretype=request.args.get('scoretype')))
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to retrieve world best: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            if isinstance(e, BadRequestKeyError):
                current_app.logger.error(json.dumps(request.form, indent=4))
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error retrieving world best: %s' % traceback.format_exc())
    return jsonify(response)

@main.route('/getrankmode', methods=['GET'])
def getrankmode():
    response = {}
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            return jsonify(get_rankmode(scoretype=request.args.get('scoretype')))
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to retrieve rank mode: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            if isinstance(e, BadRequestKeyError):
                current_app.logger.error(json.dumps(request.form, indent=4))
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error retrieving rank mode: %s' % traceback.format_exc())
    return jsonify(response)

@main.route('/getapikey', methods=['POST'])
def getapikey():
    response = {
        'status': 'success'
    }
    try:
        if not apikey_required or (valid_api_key(request.form['api_key']) and (request.environ.get('REMOTE_ADDR') in approved_ips or request.environ.get('HTTP_X_FORWARDED_FOR') in approved_ips)):
            form = APIKeyForm(request.form)
            if form.validate():
                apikey = APIKey(
                    key = generate_unique_key(),
                    name = form.name.data,
                    country = form.country.data
                )
                db.session.add(apikey)
                db.session.commit()
                response['key'] = apikey.key
                response['name'] = apikey.name
                response['country'] = apikey.country
            else:
                response['status'] = 'failure'
                if current_app.debug:
                    response['reason'] = form.errors
                else:
                    response['reason'] = 'invalid request'
        else:
            response['status'] = 'failure'
            if current_app.debug:
                current_app.logger.error('Forbidden IP attempted to create API key: ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else ""))
                response['reason'] = 'forbidden IP ' + (request.environ.get('REMOTE_ADDR') if request.environ.get('REMOTE_ADDR') != None else "") + ' and ' + (request.environ.get('HTTP_X_FORWARDED_FOR') if request.environ.get('HTTP_X_FORWARDED_FOR') != None else "")
            else:
                response['reason'] = 'forbidden'
    except Exception as e:
        response['status'] = 'failure'
        #response['reason'] = type(e).__name__
        if current_app.debug:
            if isinstance(e, BadRequestKeyError):
                current_app.logger.error(json.dumps(request.form, indent=4))
            response['reason'] = traceback.format_exc()
        else:
            response['reason'] = 'internal error'
        current_app.logger.error('Error creating API key: %s' % traceback.format_exc())
    return jsonify(response)

'''@main.route('/validatetid', methods=['POST'])
def validatetid():
    response = {}
    try:
        if request.form.validate() and valid_api_key(request.form['api_key']): # and if request.remote_addr in approved_ips
            if get_tournament(request.form['tid']) == None: 
                response['status'] = 'false'
            else:
                response['status'] = 'true' if get_tournament(request.form['tid']).active else 'false'
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
    return jsonify(response)'''

@main.route('/chart_search', methods=['GET', 'POST']) # The methods 'GET' and 'POST' tell this route that
def search():                                   # we can both request and send data to/from the page.
    form = ChartSearchForm(request.form)
    if request.method == "POST" and form.validate():
        session['search_song'] = form.song.data
        session['search_difficulty'] = request.form.get('diffDrop')
        session['search_filters'] = form.filters.data
        return redirect(url_for('main.search_results'))
    return render_template("chartsearch.html", form=form, songdata=raw_songdata, int_to_mods=int_to_mods, modlist_to_modstr=modlist_to_modstr, int_to_noteskin=int_to_noteskin)

@main.route('/search', methods=['GET', 'POST']) # The methods 'GET' and 'POST' tell this route that
def chartsearch():                                   # we can both request and send data to/from the page.
    form = SearchForm(request.form)
    if request.method == "POST" and form.validate():
        session['search_song'] = form.song.data
        session['search_filters'] = form.filters.data
        session['search_scoremodifier'] = form.scoremodifier.data
        session['search_score'] = form.score.data
        session['search_exscoremodifier'] = form.exscoremodifier.data
        session['search_exscore'] = form.score.data
        session['search_stagepass'] = form.stagepass.data
        session['search_platform'] = form.platform.data
        session['search_perfect'] = form.perfect.data
        session['search_great'] = form.great.data
        session['search_good'] = form.good.data
        session['search_bad'] = form.bad.data
        session['search_miss'] = form.miss.data
        session['search_maxcombo'] = form.maxcombo.data
        #scrollspeed
        #autovelocity
        session['noteskin'] = form.noteskin.data
        #gamemix
        #gameversion
        session['ranked'] = form.ranked.data
        session['judgement'] = form.judgement.data
        #tournamentid
        return redirect(url_for('main.search_results'))
    return render_template("search.html", form=form, songdata=raw_songdata, int_to_mods=int_to_mods, modlist_to_modstr=modlist_to_modstr, int_to_noteskin=int_to_noteskin)

@main.route('/search_results/')
def search_results():
    results = Post.query

    results = results.filter(Post.approved == 1)  # Only get approved posts

    if session.get('search_song') != None and session['search_song'] != '':
        results = results.filter(Post.song == session['search_song'])

    if session.get('search_difficulty') != None and session['search_difficulty'] != '':
        results = results.filter(Post.difficulty == session['search_difficulty'])

    if session.get('search_filters') != None and session['search_filters'] == 'verified': # fix for array
        results = results.filter(Post.platform == 'pad')
    elif session.get('search_filters') != None and session['search_filters'] == 'prime-verified':
        results = results.filter(Post.platform == 'pad', Post.acsubmit == "True")
    elif session.get('search_filters') != None and session['search_filters'] == 'unverified':
        results = results.filter(or_(Post.platform == 'keyboard', Post.platform == 'sf2-pad'))

    if session.get('search_score') != None and session['search_score'] != '':
        if session.get('search_scoremodifier') != None and session['search_scoremodifier'] != '':
            if session['search_scoremodifier'] == '==':
                results = results.filter(Post.score == int(session['search_score']))
            elif session['search_scoremodifier'] == '!=':
                results = results.filter(Post.score != int(session['search_score']))
            elif session['search_scoremodifier'] == '<':
                results = results.filter(Post.score < int(session['search_score']))
            elif session['search_scoremodifier'] == '>':
                results = results.filter(Post.score > int(session['search_score']))
            elif session['search_scoremodifier'] == '<=':
                results = results.filter(Post.score <= int(session['search_score']))
            elif session['search_scoremodifier'] == '>=':
                results = results.filter(Post.score >= int(session['search_score']))

    if session.get('search_exscore') != None and session['search_exscore'] != '':
        if session.get('search_exscoremodifier') != None and session['search_exscoremodifier'] != '':
            if session['search_exscoremodifier'] == '==':
                results = results.filter(Post.exscore == int(session['search_exscore']))
            elif session['search_exscoremodifier'] == '!=':
                results = results.filter(Post.exscore != int(session['search_exscore']))
            elif session['search_exscoremodifier'] == '<':
                results = results.filter(Post.exscore < int(session['search_exscore']))
            elif session['search_exscoremodifier'] == '>':
                results = results.filter(Post.exscore > int(session['search_exscore']))
            elif session['search_exscoremodifier'] == '<=':
                results = results.filter(Post.exscore <= int(session['search_exscore']))
            elif session['search_exscoremodifier'] == '>=':
                results = results.filter(Post.exscore >= int(session['search_exscore']))

    if session.get('search_stagepass') != None and session['search_stagepass'] != '' and session['search_stagepass'] != 'Any':
        results = results.filter(Post.stagepass == session['search_stagepass'])

    if session.get('search_platform') != None and session['search_platform'] != '' and session['search_platform'] != 'Any':
        q = [Post.platform == x for x in session['search_platform']]
        results = results.filter(or_(*q))

    if session.get('search_perfect') != None and session['search_perfect'] != '' and session['search_perfect'] != 'Any':
        results = results.filter(Post.perfect == int(session['search_perfect']))
    if session.get('search_great') != None and session['search_great'] != '' and session['search_great'] != 'Any':
        results = results.filter(Post.great == int(session['search_great']))
    if session.get('search_good') != None and session['search_good'] != '' and session['search_good'] != 'Any':
        results = results.filter(Post.good == int(session['search_good']))
    if session.get('search_bad') != None and session['search_bad'] != '' and session['search_bad'] != 'Any':
        results = results.filter(Post.bad == int(session['search_bad']))
    if session.get('search_miss') != None and session['search_miss'] != '' and session['search_miss'] != 'Any':
        results = results.filter(Post.miss == int(session['search_miss']))

    if session.get('search_maxcombo') != None and session['search_maxcombo'] != '' and session['search_maxcombo'] != 'Any':
        results = results.filter(Post.miss == int(session['search_maxcombo']))

    if session.get('search_noteskin') != None and session['search_noteskin'] != '' and session['search_noteskin'] != 'Any':
        q = [Post.noteskin == x for x in session['search_noteskin']]
        results = results.filter(or_(*q))

    if session.get('search_ranked') != None and session['search_ranked'] != '' and session['search_ranked'] != 'Any':
        results = results.filter(Post.ranked == session['search_ranked'])

    if session.get('search_judgement') != None and session['search_judgement'] != '' and session['search_judgement'] != 'Any':
        q = [Post.noteskin == x for x in session['search_judgement']]
        results = results.filter(or_(*q))

    return render_template("search_results.html", results=results, songdata=raw_songdata, int_to_mods=int_to_mods, modlist_to_modstr=modlist_to_modstr, int_to_noteskin=int_to_noteskin)

@main.route('/wiki/<wikipage>')
def wiki(wikipage):
    current_app.logger.debug(wikipage)
    if re.match(r'^\w+$', wikipage):
        dest = os.path.join(current_app.root_path, 'templates/wiki/', wikipage+'.md')
        if os.path.isfile(dest):
            with open(dest) as f:
                txt = f.read()
            return render_template("wiki.html", mdname=wikipage.replace('_', ' '), mdpage=txt)
    abort(404)

@main.route('/changelog')
def changelog():
    return render_template("changelog.html", changelog=GetChangelog())

@main.route('/resources')
def resources():
    return render_template("resources.html", changelog=GetChangelog())

@main.route('/howto')
def howto():
    return render_template("howto.html", changelog=GetChangelog())