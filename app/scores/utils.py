import logging
from PIL import Image
import os
import secrets
import json
import sys
import re
from flask import current_app
from flask_login import current_user
from app import db, logging, raw_songdata, scheduler, judgement_pairs
from app.models import *
from app.users.utils import update_user_sp, update_user_titles

def id_to_user(uid):
    u = User.query.filter_by(id=uid).first()
    return u if u != None else None

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/score_screenshots', picture_fn)
    output_size = (1200, 1200)
    i = Image.open(form_picture)
    if i.size[0] > 1200 or i.size[1] > 1200:
        i.thumbnail(output_size)
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
    0x3: "Easy",
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
    0x1d: "Basic (Infinity)",
    0x1e: "Fiesta",
    0x1f: "Fiesta 2",
}
other_noteskin = {
    0x20: "Prime 2",
    0x21: "XX",
    -1: "Unknown"
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

def update_song_list():
    current_app.logger.info("Updating song list database...")
    with open(os.getcwd()+'/app/static/gamelists/complete.json', 'w') as f:
        json.dump(raw_songdata, f)
    current_app.logger.info("Updated song list database.")

def get_max_combo(song, difficulty):
    return raw_songdata[song]['difficulties'][difficulty][0]

def update_max_combo(song, difficulty, maxcombo):
    raw_songdata[song]['difficulties'][difficulty][0] = maxcombo

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
                                    'ChartLevel': score.difficultynum,
                                    'ChartMode': get_primediff(score.type),
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
                                    'ChartLevel': score.difficultynum,
                                    'ChartMode': get_primediff(score.type),
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

def check_post(post):
    """Evaluates a post and returns the status which it should be assigned.
    
    If there is something impossible which would prevent the post from being submitted, return None"""
    # return status a given post should be by looking at the post itself, returns None is something is impossible

    # if SS or SSS, check if full combo or 0 miss
    if post.grade in ('ss', 'sss') and post.miss > 0:
        return None
    
    # make a score unranked if...
    # - song doesn't have a max combo
    # - platform != 'pad'

    # # check picture using fastai
    # # use this to initialize the learner: score_learner = load_learner(path)
    # current_app.logger.debug("Predicting image.")
    # im = Image.open(post.image_file)
    # if im != None:
    #     result = score_learner.predict(im)
    # mix = int_to_gamelabel(result[1])
    # if mix not in pump_mixes:  # or mix not the specified gamemix
    #     return POST_PENDING
    # # also consider checking if a song or chart is not playable in the recognized mix (but also check this above if possible)

    return POST_APPROVED


def approve_post(post):
    '''Given a post, set it to an approved state and update the user's SP and titles.'''
    post.status = POST_APPROVED
    db.session.commit()
    u = User.query.get(post.user_id)
    update_user_sp(u)
    update_user_titles(u)

def queue_post(post):
    '''Given a post, add it to the moderator queue.'''
    post.status = POST_PENDING
    db.session.commit()

# def id_to_songdiff(sid, diff):
#     '''Given an official song ID and a difficulty, return the difficulty of the song (???)'''
#     pass

def id_to_songname(sid):
    '''Given an official song ID, return the song it is associated with.'''
    for song in raw_songdata:
        if raw_songdata[song]['song_id'] == sid:
            return song
    return None

def songname_to_id(songname):
    '''Given the name of a song, return its official song ID.'''
    if raw_songdata.get(songname) != None:
        return raw_songdata[songname]['song_id']
    return None

def posts_to_uscore(posts, scoretype='default'):
    '''Given a list of posts, return a PrimeServer UScore packet.'''
    uscore = []
    for post in posts:
        if scoretype == 'default':
            uscore.append(
                {
                    'SongID': post.song_id,
                    'ChartLevel': post.difficultynum,
                    'GameDataFlag': get_primediff(post.type),
                    'Score': post.score,
                    'RealScore': post.score
                }
            )
        elif scoretype == 'exscore':
            uscore.append(
                {
                    'SongID': post.song_id,
                    'ChartLevel': post.difficultynum,
                    'GameDataFlag': get_primediff(post.type),
                    'Score': post.exscore,
                    'RealScore': post.exscore
                }
            )
    return uscore[:4384]

def calc_exscore(perfect, great, good, bad, miss):
    '''Calculate the EX Score of a chart given the amounts of perfects, greats, goods, bads, and misses.'''
    PERFECT_WEIGHT = 3
    GREAT_WEIGHT = 2
    GOOD_WEIGHT = 1
    BAD_WEIGHT = 0
    MISS_WEIGHT = 0
    return PERFECT_WEIGHT * perfect + GREAT_WEIGHT * great + GOOD_WEIGHT * good + BAD_WEIGHT * bad + MISS_WEIGHT * miss

def mods_to_int(modlist, judgement):
    '''Given a list of modifiers, return a representative integer.'''
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

def int_to_mods(num, separate_judge=False):
    '''Given an integer, return the list of modifiers that it represents.'''
    mods_rev = {val: key for key, val in mods.items()}
    mods_vals = sorted(mods.values(), reverse=True)
    
    modlist = []

    for mod in mods_vals:
        if num - mod >= 0:
            modlist.append(mods_rev[mod])
            num -= mod
            if num == 0:
                break
    
    if separate_judge:
        judgement = 'nj'
        for judge in judgement_pairs:
            if judge[0] in modlist:
                modlist.remove(judge[0])  # error catching might be a good idea here
                judgement = judge[0]
        return modlist, judgement

    return modlist

def int_to_judge(num):
    '''Given an integer representing a list of modifiers, return its judgement modifier.'''
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
    '''Given a list of modifiers, format it as a readable comma-separated string.'''
    s = ""
    i = 0
    while i < len(modlist)-1:
        s += str(modlist[i].upper()) + ', '
        i += 1
    if len(modlist) > 0:
        s += str(modlist[i].upper())
    return s if s != "" else "None"

def get_diffnum(diffstr):
    '''Given a difficulty string, return its difficulty value.'''
    return int(''.join(x for x in diffstr if x.isdigit()))

def get_difftype(diffstr):
    '''Given a difficulty string, return the full name of the chart type it is associate with.'''
    return abbrev_charttype.get(''.join(x for x in diffstr if not x.isdigit()))

def get_diffstr(difftype, diffnum):
    '''Given two integers representing the chart type and the difficulty value, return the representative difficulty string.'''
    return {val: key for key, val in {x:abbrev_charttype[x] for x in abbrev_charttype if x != 'HD'}.items()}[difftype] + str(diffnum)

def get_primediff(difftype):
    '''Given an integer, return the associated chart type's full name.'''
    return {val: key for key, val in {x:prime_charttype[x] for x in prime_charttype if x != 'HD'}.items()}[difftype]

def int_to_noteskin(num):
    '''Given an integer key, return the associated noteskin's name.'''
    return {**prime_noteskin, **other_noteskin}.get(int(num))

def high_score(post):
    """Check if a score is a user's highest score (in points, not in SP).

    For highest SP score, use `post.is_personal_best`."""
    top = Post.query.filter_by(song_id=post.song_id, difficulty=post.difficulty, user_id=post.user_id).order_by(Post.score.desc()).first()
    if top != None:
        if top.score > post.score:
            return False
    return True

def del_high_score(post):
    """Delete a user's highest score given a Post with the song ID, difficulty, and user ID.

    This function is deprecated since all scores are saved now and thus it should not be used."""
    top = Post.query.filter_by(song_id=post.song_id, difficulty=post.difficulty, user_id=post.user_id).order_by(Post.score.desc()).first()
    if top != None:
        db.session.delete(top)
        db.session.commit()
    

def rerate_diff(post):
    '''Given a post, update the difficulty to match the latest difficulty name.'''
    # todo: do this using the new database
    with open('rerates.json', 'r') as rerates:
        reratedict = json.load(rerates)
    newvalues = reratedict.get(','.join((post.song.strip(), post.difficulty, post.type, str(post.difficultynum)))) # song name, difficulty string, chart type, difficulty number

    if newvalues == None:
        return
    #post.song = newvalues[0]
    post.difficulty = newvalues[1]
    post.type = newvalues[2]
    post.difficultynum = newvalues[3]

def calc_level(exp):
    i = 0
    while True:
        #if exp < int(100+(100*(0.01*(1.02110074343**i)))):\
        if exp < int((5.5816187294199637E-01*(i**5.0936826990568707E-01))-5.4169035580629679):
            return i
        i += 1