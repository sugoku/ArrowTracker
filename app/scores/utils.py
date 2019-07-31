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

prime_grade = {
    0: "SSS",
    1: "SS",
    2: "S",
    3: "A",
    4: "B",
    5: "C",
    6: "D",
    7: "F"
}
prime_charttype = {
    0x0: "Single", # 0
    0x5: "Double Performance", # 5
    0x40: "Single Performance", # 64
    0x80: "Double", # 128
    0xc0: "Co-Op" # 192
}
prime_songcategory = {
    0x0: "Arcade",
    0x1: "Random",
    0x7: "Remix",
    0x8: "Short Cut",
    0x9: "Music Train",
    0xa: "Quest",
    0xc: "UCS" # HDD
}
prime_noteskin = {
    0x0: "Prime",
    0x1: "Korean Trump",
    0x2: "Old",
    0x3: "Easy (Infinity)",
    0x4: "Slime",
    0x5: "Music",
    0x6: "Canon",
    0x7: "Poker",
    0x8: "NX",
    0x9: "Lamb",
    0xa: "Horse",
    0xb: "Dog",
    0xc: "Girl",
    0xd: "Fire",
    0xe: "Ice",
    0xf: "Wind",
    0x13: "NXA",
    0x14: "NX2",
    0x15: "Lightning",
    0x16: "Drum",
    0x17: "Missile",
    0x1b: "Football",
    0x1c: "Rebirth",
    0x1d: "Basic",
    0x1e: "Fiesta",
    0x1f: "Fiesta 2"
}

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

def id_to_songdiff(sid, diff):
    pass

def id_to_songname(sid):
    for song in raw_songdata:
        if raw_songdata[song]['id'] == sid:
            return song
    return None

def posts_to_uscore(posts):
    pass