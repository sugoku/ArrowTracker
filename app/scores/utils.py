import logging
from PIL import Image
import os
import secrets
import json
import sys
from flask import current_app
from flask_login import current_user
from app import db, logging, raw_songdata, scheduler
from app.models import Post, User

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/score_screenshots', picture_fn)
    i = Image.open(form_picture)
    i.save(picture_path)
    return picture_fn

def return_completion(user, difficulty):
    user = user = User.query.filter_by(username=user).first_or_404()
    allscores = Post.query.filter_by(author=user).all()
    data = {}
    passinggrades = ['a','s','ss','sss']
    completed = 0
    if difficulty == "singles":
        data['singles'] = {}
        for i in range(25):
            diff = i+1
            for score in allscores:
                if score.difficulty == diff and score.lettergrade in passinggrades:
                    completed += 1
            data['singles'][diff] = completed
    return(data)

@scheduler.task('interval', id='update_scores', minutes=1)
def update_scores_task():
    with scheduler.app.app_context():
        current_app.logger.info("Updating PrimeServer leaderboards...")
        rankings = ['worldbest', 'rankmode']
        scoretypes = ['default', 'exscore']
        for rnk in rankings:
            for st in scoretypes:
                with open(os.getcwd()+'/leaderboards/'+rnk+'_'+st+'.json', 'w') as f:
                    json.dump(create_ranking(rnk, st), f)
        current_app.logger.info("Updated leaderboards.")

def create_ranking(ranking='worldbest', scoretype='default'):
    if ranking == 'worldbest':
        worldbest = {
            'WorldScores': []
        }
        song_ids = []
        # get all song IDs and charts
        # then get top score for each song ID and append to array
        for i in song_ids:
            if scoretype == 'default':
                score = Post.query.filter_by(song_id=i).order_by(Post.score.desc()).all()
            elif scoretype == 'exscore':
                score = Post.query.filter_by(song_id=i).order_by(Post.exscore.desc()).all()
            else:
                break
            worldbest['WorldScores'].append(
                {
                    'SongID': i,
                    'ChartLevel': score.difficulty,
                    'ChartMode': cmode[score.type],
                    'Score': score.score,
                    'Nickname': id_to_user(score.user_id).ign
                }
            )
        worldbest['WorldScores'] = worldbest['WorldScores'][:4095] # 0-4094
        return worldbest
    elif ranking == 'rankmode':
        rankmode = {
            'Ranks': []
        }
        song_ids = []
        # get all song IDs
        # then calculate cumulative score per user on song id and get top 3
        # ideally that is what we would do but nah let's put a watermark cause that will be hard when people submit more scores
        for i in song_ids:
            #if scoretype == 'default':
            #    score = Post.query.filter_by(song_id=i).order_by(Post.score.desc()).all()
            #elif scoretype == 'exscore':
            #    score = Post.query.filter_by(song_id=i).order_by(Post.exscore.desc()).all()
            #else:
            #    break
            rankmode['Ranks'].append(
                {
                    'SongID': i,
                    'First': 'PRIME',
                    'Second': 'SERVER',
                    'Third': '2019'
                }
            )
        rankmode['Ranks'] = rankmode['Ranks'][:4095] # 0-4094
        return rankmode #0-399
    return []

def get_worldbest(scoretype='default'):
    re.sub(r'\W+', '', scoretype)
    with open(os.getcwd()+'/leaderboards/'+'worldbest_'+scoretype+'.json') as f:
        return json.load(f)

def get_rankmode(scoretype='default'):
    re.sub(r'\W+', '', scoretype)
    with open(os.getcwd()+'/leaderboards/'+'rankmode_'+scoretype+'.json') as f:
        return json.load(f)
    # plan to use APScheduler to update database