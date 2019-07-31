import os
import logging
from flask import render_template, request, Blueprint, current_app, session, redirect, url_for, flash, Markup, jsonify
from flask_login import current_user, login_required
from app.main.forms import SearchForm, TournamentForm, TournamentEditForm
from app.scores.forms import ScoreForm
from app.users.forms import APIKeyForm
from app.models import Post, Tournament, APIKey
from app import songlist_pairs, difficulties, db, raw_songdata
from sqlalchemy import desc, or_
from app.config import GetChangelog
from app.main.utils import save_picture, allowed_file, valid_api_key, generate_unique_key
from app.users.utils import accesscode_to_user, user_to_primeprofile, update_user_with_primeprofile
from app.scores.utils import id_to_songname, prime_grade, prime_charttype, prime_songcategory

# We can define all of the "@main" decorators below as a "blueprint" that
# allows us to easily call or redirect the user to any of them from anywhere.
main = Blueprint('main', __name__)

# The route for the main homepage.
@main.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    scores = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=15, page=page)
    total = db.engine.execute('select count(*) from Post').scalar()
    return render_template("home.html", scores=scores, total=total, songdata=raw_songdata)

@main.route('/about')
def about():
    return render_template("about.html")

@main.route('/submit', methods=['POST'])
def submit():
    response = {
        'status': 'success'
    }
    try:
        if request.form.validate() and valid_api_key(request.form['api_key']): # and if request.remote_addr in approved_ips
            u = accesscode_to_user(request.form.accesscode.data)
            post = Post(
                song = id_to_songname(hex(int(request.form['SongID']))),
                song_id = int(request.form['SongID']),
                score = int(request.form['Score']),
                exscore = calc_exscore(int(request.form['Perfect']), int(request.form['Great']), int(request.form['Good']), int(request.form['Bad']), int(request.form['Miss'])),
                lettergrade = prime_grade[int(request.form['Grade'])],
                type = prime_charttype[int(request.form['Type'])],
                difficulty = int(request.form['ChartLevel']),
                platform = 'pad',
                stagepass = 'True' if request.form['Flag'] == '128' else 'False',
                perfect = int(request.form['Perfect']),
                great = int(request.form['Great']),
                good = int(request.form['Good']),
                bad = int(request.form['Bad']),
                miss = int(request.form['Miss']),
                maxcombo = int(request.form['MaxCombo']),
                pp = int(request.form['PP']),
                runningstep = int(request.form['RunningStep']),
                kcal = float(request.form['Kcal']),
                scrollspeed = int(request.form['NoteSkinSpeed']) % 0x100,
                noteskin = int(request.form['NoteSkinSpeed']) / 0x10000,
                modifiers = int(request.form['Modifiers']),
                #gamemix = request.form['Gamemix'],
                gameversion = request.form['GameVersion'],
                ranked = 'True' if request.form['Flag'] == '128' else 'False',
                length = prime_songcategory[int(request.form['SongCategory'])],
                accesscode = request.form['AccessCode'],
                acsubmit = 'True',
                user_id = u.id
            )
            db.session.add(post)
            add_exp(u, request.form['EXP'])
            db.session.commit()
            
            return jsonify(response)
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
            return jsonify(response)
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
        return jsonify(response)

@main.route('/getprofile', methods=['GET'])
def getprofile():
    response = {}
    try:
        if request.form.validate() and valid_api_key(request.args.get('api_key')): # and if request.remote_addr in approved_ips
            u = accesscode_to_user(request.args.get('access_code'))
            return jsonify(user_to_primeprofile(u))
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
            return jsonify(response)
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
        return jsonify(response)

@main.route('/saveprofile', methods=['POST'])
def saveprofile():
    response = {
        'status': 'success'
    }
    try:
        if request.form.validate() and valid_api_key(request.form['api_key']): # and if request.remote_addr in approved_ips
            u = accesscode_to_user(request.form['access_code'])
            update_user_with_primeprofile(u, request.form)
            db.session.commit()
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
    return jsonify(response)

@main.route('/getworldbest', methods=['GET'])
def getworldbest():
    response = {}
    try:
        if request.form.validate() and valid_api_key(request.args.get('api_key')): # and if request.remote_addr in approved_ips
            return jsonify(get_worldbest(scoretype=request.args.get('scoretype')))
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
    return jsonify(response)

@main.route('/getrankmode', methods=['GET'])
def getrankmode():
    response = {}
    try:
        if request.form.validate() and valid_api_key(request.args.get('api_key')): # and if request.remote_addr in approved_ips
            return jsonify(get_rankmode(scoretype=request.args.get('scoretype')))
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
    return jsonify(response)

@main.route('/getapikey', methods=['POST'])
@login_required
def getapikey():
    response = {
        'status': 'success'
    }
    try:
        if request.form.validate() and current_user.is_authenticated: # and if request.remote_addr in approved_ips
            form = APIKeyForm(request.form)
            if form.validate():
                apikey = APIKey(
                    key = generate_unique_key(),
                    name = form.name.data,
                    country = form.country.data
                )
                db.session.add(apikey)
                db.session.commit()
        else:
            response['status'] = 'failure'
            response['reason'] = 'invalid request'
    except Exception as e:
        response['status'] = 'failure'
        response['reason'] = type(e).__name__
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

@main.route('/search', methods=['GET', 'POST']) # The methods 'GET' and 'POST' tell this route that
def search():                                   # we can both request and send data to/from the page.
    form = SearchForm(request.form)
    if request.method == "POST" and form.validate():
        session['song_search'] = form.song.data
        session['filters'] = form.filters.data
        session['length'] = form.length.data
        return redirect(url_for('main.search_results'))
    return render_template("search.html", form=form)

@main.route('/search_results/')
def search_results():
    if session['filters'] == 'old':
        results = Post.query.filter(Post.song.like('%' + session['song_search'] + '%'), Post.length == None)
    if session['filters'] == 'all':
        results = Post.query.filter(Post.song.like('%' + session['song_search'] + '%'), Post.length == session['length'])
    elif session['filters'] == 'verified':
        results = Post.query.filter(Post.song.like('%' + session['song_search'] + '%'), Post.length == session['length'], Post.platform == 'pad', )
    elif session['filters'] == 'unverified':
        results = Post.query.filter(Post.song.like('%' + session['song_search'] + '%'), Post.length == session['length'], or_(Post.platform == 'keyboard', Post.platform == 'sf2-pad'))
    return render_template("search_results.html", results=results)

@main.route('/changelog')
def changelog():
    return render_template("changelog.html", changelog=GetChangelog())

@main.route('/resources')
def resources():
    return render_template("resources.html", changelog=GetChangelog())

@main.route('/howto')
def howto():
    return render_template("howto.html", changelog=GetChangelog())

@main.route("/tournaments/view")
@login_required
def tournaments():
    page = request.args.get('page', 1, type=int)
    tournaments = Tournament.query.order_by(Tournament.date_posted.desc()).paginate(per_page=16, page=page)
    return render_template("tournaments.html", tournaments=tournaments)

@main.route("/tournaments/create", methods=["GET", "POST"])
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
                picture_file = save_picture(file)
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                flash('You can\'t upload that!', 'error')
        tournament = Tournament(name = form.name.data, skill_lvl = form.skill_lvl.data, description = form.description.data, bracketlink = form.bracketlink.data, image_file = picture_file, contactinfo = form.contactinfo.data, user_id = current_user.id)
        db.session.add(tournament)
        db.session.commit()
        flash('Tournament created!', 'success')
        return redirect(url_for('main.tournaments'))
    return render_template("create_tournament.html", form=form)

@main.route("/tournaments/<int:tournament_id>/edit", methods=["GET", "POST"])
@login_required
def edit_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    form = TournamentEditForm()
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
                picture_file = save_picture(file)
                flash('File uploaded successfully!', 'success')
            elif file and not allowed_file(file.filename):
                picture_file = "None"
                flash('You can\'t upload that!', 'error')
        tournament.image_file = picture_file
        tournament.name = form.name.data
        tournament.description = form.description.data
        tournament.skill_lvl = form.skill_lvl.data
        tournament.bracketlink = form.bracketlink.data
        tournament.contactingo = form.contactinfo.data
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

@main.route('/tournament/<int:tournament_id>')
def tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    return render_template('tournament.html', tournament=tournament)

@main.route('/tournament/<int:tournament_id>/delete', methods=["POST"])
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if tournament.user_id != current_user.id:
        abort(403)
    if tournament.image_file != "None":
        os.remove(os.path.join(current_app.root_path, 'static/tournament_pics', tournament.image_file))
    db.session.delete(tournament)
    db.session.commit()
    flash('Your tournament has been deleted!', 'success')
    return redirect(url_for('main.tournaments'))
