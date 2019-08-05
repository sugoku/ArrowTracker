import logging
from PIL import Image
import os
import secrets
import json
import sys
import re
from flask import current_app
from flask_login import current_user
from app import db, logging, raw_songdata, scheduler
from app.models import Post, User
from app.users.utils import id_to_user

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

global mods, prime_noteskin, other_noteskin

prime_grade = {
    0: "sss",
    1: "ss",
    2: "s",
    3: "a",
    4: "b",
    5: "c",
    6: "d",
    7: "f"
}
prime_charttype = {
    0x0: "Single", # 0
    0x5: "Double Performance", # 5
    0x40: "Single Performance", # 64
    0x80: "Double", # 128
    0xc0: "Co-Op" # 192
}
abbrev_charttype = {
    'S': "Single",
    'SP': "Double Performance",
    'DP': "Single Performance",
    'D': "Double",
    'HD': "Double", # just don't specify for now
    'Co-Op': "Co-Op"
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
    0x1f: "Fiesta 2",
}
other_noteskin = {
    0x20: "Prime 2",
    0x21: "XX"
}
mods = {
    'v': 0x1,
    'ap': 0x2,
    'ns': 0x3,
    'fl': 0x4,
    'fd': 0x8,
    'm': 0x10,
    'rs': 0x20,
    'rn': 0x40, # random noteskin
    'ua': 0x80,
    'jr': 0x100,
    'dc': 0x200,
    'bgaoff': 0x800,
    'x': 0x1000,
    'nx': 0x2000,
    'dr': 0x4000,
    'si': 0x80000,
    'ri': 0x100000,
    'sn': 0x200000,
    'hj': 0x400000,
    'vj': 0x800000
}
judgements = {
    'nj': 0x0,
    'hj': 0x400000,
    'vj': 0x800000
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
    scoretype = re.sub(r'\W+', '', scoretype)
    if ranking == 'worldbest':
        worldbest = {
            'WorldScores': []
        }
        for song in raw_songdata:
            if raw_songdata[song]['song_id'] != "":
                for chart in raw_songdata[song]['difficulties']:
                    if scoretype == 'default':
                        score = Post.query.filter_by(song_id=int(raw_songdata[song]['song_id'], 16), difficulty=chart).order_by(Post.score.desc()).first()
                        if score != None:
                            worldbest['WorldScores'].append(
                                {
                                    'SongID': int(raw_songdata[song]['song_id'], 16),
                                    'ChartLevel': score.difficulty,
                                    'ChartMode': get_fulldiff(score.type),
                                    'Score': score.score,
                                    'Nickname': id_to_user(score.user_id).ign
                                }
                            )
                    elif scoretype == 'exscore':
                        score = Post.query.filter_by(song_id=int(raw_songdata[song]['song_id'], 16), difficulty=chart).order_by(Post.exscore.desc()).first()
                        if score != None:
                            worldbest['WorldScores'].append(
                                {
                                    'SongID': int(raw_songdata[song]['song_id'], 16),
                                    'ChartLevel': score.difficulty,
                                    'ChartMode': get_fulldiff(score.type),
                                    'Score': score.exscore,
                                    'Nickname': id_to_user(score.user_id).ign
                                }
                            )
                    else:
                        break
                    
        worldbest['WorldScores'] = worldbest['WorldScores'][:4095] # 0-4094
        return worldbest
    elif ranking == 'rankmode':
        rankmode = {
            'Ranks': []
        }
        song_ids = []
        for song in raw_songdata:
            if raw_songdata[song]['song_id'] != "":
                song_ids.append(int(raw_songdata[song]['song_id'], 16))
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
    scoretype = re.sub(r'\W+', '', scoretype)
    with open(os.getcwd()+'/leaderboards/'+'worldbest_'+scoretype+'.json') as f:
        return json.load(f)

def get_rankmode(scoretype='default'):
    scoretype = re.sub(r'\W+', '', scoretype)
    with open(os.getcwd()+'/leaderboards/'+'rankmode_'+scoretype+'.json') as f:
        return json.load(f)
    # plan to use APScheduler to update database

def id_to_songdiff(sid, diff):
    pass

def id_to_songname(sid):
    for song in raw_songdata:
        if raw_songdata[song]['song_id'] == sid:
            return song
    return None

def songname_to_id(songname):
    if raw_songdata.get(songname) != None:
        return raw_songdata[songname]['song_id']
    return None

def posts_to_uscore(posts, scoretype='default'):
    uscore = []
    for post in posts:
        if scoretype == 'default':
            uscore.append(
                {
                    'SongID': post.song_id,
                    'ChartLevel': post.difficulty,
                    'GameDataFlag': post.gameflag,
                    'Score': post.score,
                    'RealScore': post.score
                }
            )
        elif scoretype == 'exscore':
            uscore.append(
                {
                    'SongID': post.song_id,
                    'ChartLevel': post.difficulty,
                    'GameDataFlag': post.gameflag,
                    'Score': post.exscore,
                    'RealScore': post.exscore
                }
            )
    return uscore[:4384]

def calc_exscore(perfect, great, good, bad, miss):
    PERFECT_WEIGHT = 3
    GREAT_WEIGHT = 2
    GOOD_WEIGHT = 1
    BAD_WEIGHT = 0
    MISS_WEIGHT = 0
    return PERFECT_WEIGHT * perfect + GREAT_WEIGHT * great + GOOD_WEIGHT * good + BAD_WEIGHT * bad + MISS_WEIGHT * miss

def mods_to_int(modlist, judgement):
    modsum = 0

    if ('V' in modlist and 'AP' in modlist) or ('V' in modlist and 'NS' in modlist) or ('NS' in modlist and 'AP' in modlist):
        if 'V' in modlist:
            modlist.remove('V')
        if 'AP' in modlist:
            modlist.remove('AP')
        if 'NS' not in modlist:
            modlist.append('NS')

    for mod in modlist:
        if mods.get(mod.lower()) != None:
            modsum += mods[mod.lower()]
    if mods.get(judgement.lower()) != None:
        modsum += mods[judgement.lower()]

    return modsum

def int_to_mods(num):
    mods_rev = {val: key for key, val in mods.items()}
    mods_vals = sorted(mods.values(), reverse=True)
    
    modlist = []

    for mod in mods_vals:
        if num - mod >= 0:
            modlist.append(mods_rev[mod])
            num -= mod
            if num == 0:
                break

    return modlist

def int_to_judge(num):
    judge_rev = {val: key for key, val in judgements.items()}
    judge_vals = sorted(judgements.values(), reverse=True)
    
    modlist = []

    for mod in judge_vals:
        if num - mod >= 0:
            modlist.append(judge_rev[mod])
            num -= mod
            if num == 0:
                break

    return modlist[0]

def modlist_to_modstr(modlist):
    s = ""
    i = 0
    while i < len(modlist)-1:
        s += str(modlist[i].upper()) + ', '
        i += 1
    if len(modlist) > 0:
        s += str(modlist[i].upper())
    return s

def get_diffnum(diffstr):
    return int(''.join(x for x in diffstr if x.isdigit()))

def get_difftype(diffstr):
    return abbrev_charttype.get(''.join(x for x in diffstr if not x.isdigit()))

def get_diffstr(difftype, diffnum):
    return {val: key for key, val in {x:abbrev_charttype[x] for x in abbrev_charttype if x != 'HD'}.items()}[difftype] + str(diffnum)

def get_fulldiff(difftype):
    return {val: key for key, val in {x:abbrev_charttype[x] for x in abbrev_charttype if x != 'HD'}.items()}[difftype]

def int_to_noteskin(num):
    return {**prime_noteskin, **other_noteskin}.get(int(num))

def high_score(post):
    top = Post.query.filter_by(song_id=post.song_id, difficulty=post.difficulty, user_id=post.user_id).order_by(Post.score.desc()).first()
    if top != None:
        if top.score > post.score:
            return False
    return True

def prime_to_xx_diff(post):
    with open('rerates.json', 'r') as rerates:
        reratedict = json.load(rerates)
    newvalues = reratedict[','.join((post.song.strip(), post.difficulty, post.type, post.difficultynum))] # song name, difficulty string, chart type, difficulty number

    #post.song = newvalues[0]
    post.difficulty = newvalues[1]
    post.type = newvalues[2]
    post.difficultynum = newvalues[3]
