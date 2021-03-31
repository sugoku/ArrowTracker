from flask import render_template, url_for, flash, redirect, request, Blueprint, send_file, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt, raw_songdata
from app.models import *
from app.users.forms import (RegisterForm, LoginForm, UpdateAccountForm, UpdateAccountPrimeServerForm,
                             RequestResetForm, ResetPasswordForm, MessageForm)
from app.users.utils import send_reset_email, get_user_rank
from app.scores.utils import *
from app.main.utils import *
from sqlalchemy import or_
import json
import binascii
import io
from datetime import datetime

users = Blueprint('users', __name__)

@users.context_processor
def add_songdata():
    return dict(songdata=raw_songdata)

@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data.lower(), password=hashed_password, accesscode=generate_unique_accesscode(), ign=re.sub(r'[^a-zA-Z0-9]', '', form.username.data).upper()[:12]) # ign needs to be fixed ASAP it's a major flaw
        db.session.add(user)
        db.session.commit()
        flash(f'Hello, {form.username.data}! You may now log in!', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)

@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        user = User.query.filter_by(email=email).first()
        if user == None:
            flash('User not found!', 'danger')
        #user.email = user.email.lower()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Login successful! Welcome, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful!', 'danger')
    return render_template('login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route('/dashboard/updatepfp', methods=["POST"])
@login_required
def update_pfp():
    if request.method == 'POST':
        current_user.image_file = request.form['submit_button']
        db.session.commit()
        flash('Profile image updated!', 'success')
    return redirect(url_for('users.dashboard'))

@users.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    if current_user.has_role('PrimeServer'):
        form = UpdateAccountPrimeServerForm()
    else:
        form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'profile')
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data.lower()
        current_user.bio = form.bio.data
        current_user.favsong = form.favsong.data
        if current_user.has_role('PrimeServer'):
            current_user.ign = form.ign.data
            current_user.noteskin = form.noteskin.data
            current_user.scrollspeed = round(0.5 * round(float(form.scrollspeed.data) / 0.5), 1)
            current_user.modifiers = current_user.modifiers | mods_to_int([], form.judgement.data)
            current_user.psupdate = "True" if not form.psupdate.data else "False"
        db.session.commit()
        flash('Account details updated!', 'success')
        return redirect(url_for('users.dashboard'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.favsong.data = current_user.favsong
        if current_user.has_role('PrimeServer'):
            form.ign.data = current_user.ign
            form.noteskin.data = current_user.noteskin
            form.scrollspeed.data = current_user.scrollspeed
            form.judgement.data = int_to_judge(current_user.modifiers)
            form.psupdate.data = current_user.psupdate == "False"
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template("dashboard.html", title="Dashboard", image_file=image_file, form=form, current_user=current_user)

@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    scores = Post.query.filter_by(author=user, status=POST_APPROVED)\
        .order_by(Post.date_posted.desc())\
        .paginate(per_page=5, page=page)
    difficulty = None
    for score in scores.items:
        difficulty = str(score.difficulty)
    return render_template("user_posts.html", scores=scores, difficulty=difficulty, user=user, songdata=raw_songdata)

@users.route("/userpage/<string:username>")
def user_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    topscores = Post.query.filter_by(author=user, status=POST_APPROVED).filter(or_(Post.image_file != "None", Post.acsubmit == "True")).order_by(Post.sp.desc()).limit(50).all()
    recentscores = Post.query.filter_by(author=user, status=POST_APPROVED).order_by(Post.date_posted.desc()).limit(3).all()

    firstscores = []
    allscores = Post.query.filter_by(author=user, status=POST_APPROVED).all()
    for score in allscores:
        if score == Post.query.filter_by(song_id=score.song_id, difficulty=score.difficulty).filter(or_(Post.image_file != "None", Post.acsubmit == "True")).first():
            firstscores.append(score)
    
    return render_template("user_profile.html", topscores=topscores, recentscores=recentscores, user=user, int_to_mods=int_to_mods, modlist_to_modstr=modlist_to_modstr, int_to_noteskin=int_to_noteskin, get_user_rank=get_user_rank, firstscores=firstscores)

@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect_for(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('A reset email has been reset with instructions! Make sure you check your spam folder!', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect_for(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That token is invalid or expired!', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'You password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@users.route("/members")
def members():
    users = User.query.filter_by(status=USER_CONFIRMED).all()
    total = db.engine.execute('select count(*) from User').scalar()
    return render_template('users.html', users=users, total=total)

@users.route("/members/supporters")
def supporters():
    with open('supporters.json', 'r') as f:
        supporters = json.load(f)
    total = len(supporters)
    return render_template('supporters.html', supporters=supporters, total=total)

@users.route("/getprimebin", methods=["GET"])
def getprimebin():
    if current_user.is_authenticated:
        current_app.logger.info(current_user.accesscode)
        return send_file(
            io.BytesIO(binascii.unhexlify(current_user.accesscode)), 
            as_attachment=True,
            attachment_filename='prime.bin',
            mimetype='application/octet-stream'
        )
    else:
        return redirect_for(url_for('main.home'))

@users.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('users.user_page', username=recipient))
    return render_template('new_message.html', form=form, recipient=recipient)

@users.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('users.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('users.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

# @users.route('/export_posts')
# @login_required
# def export_posts():
#     if current_user.get_task_in_progress('export_posts'):
#         flash('An export task is currently in progress')
#     else:
#         current_user.launch_task('export_posts', 'Exporting posts...')
#         db.session.commit()
#     return redirect(url_for('main.user', username=current_user.username))


@users.route('/notifications')
def notifications():
    if current_user.is_authenticated:
        since = request.args.get('since', 0.0, type=float)
        notifications = current_user.notifications.filter(
            Notification.timestamp > since).order_by(Notification.timestamp.asc())
        return jsonify([{
            'name': n.name,
            'data': n.get_data(),
            'timestamp': n.timestamp
        } for n in notifications])
    else:
        return redirect_for(url_for('main.home'))