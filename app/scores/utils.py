import logging
from PIL import Image
import os
import secrets
import json
import sys
import re
from flask import current_app
from flask_login import current_user
from app import db, logging, scheduler, judgement_pairs
from app.models import *
from app.pump_models import *
from weekly import randomize_weekly, get_current_weekly, create_json
from app.users.utils import update_user_sp, update_user_titles

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def return_completion(user, difficulty):
    user = User.query.filter_by(username=user).first_or_404()
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
    0x0: Mode.query.filter_by(name="Single").first(), # 0
    0x5: Mode.query.filter_by(name="Double Performance").first(), # 5
    0x40: Mode.query.filter_by(name="Single Performance").first(), # 64
    0x80: Mode.query.filter_by(name="Double").first(), # 128
    0xc0: Mode.query.filter_by(name="Co-Op").first() # 192
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
mods_display = {
    'v': 'V (Vanish)',
    'ap': 'AP',
    'ns': 'NS',
    'fl': 'FL',
    'fd': 'FD',
    'm': 'M (Mirror)',
    'rs': 'RS',
    'rn': 'Random Noteskin', # random noteskin
    'ua': 'UA',
    'jr': 'JR (Judge Reverse)',
    'dc': 'DC',
    'bgaoff': 'BGA OFF',
    'x': 'X',
    'nx': 'NX',
    'dr': 'DR',
    'si': 'SI',
    'ri': 'RI',
    'sn': 'SN',
    'hj': 'HJ (Hard Judgement)',
    'vj': 'VJ (Very Hard Judgement)'
}
judgements = {
    'nj': 0x0,
    'hj': 0x400000,
    'vj': 0x800000
}


fastai_classes = ['a20blue','a20gold','ace','chunithm','ddrassorted','fiesta','fiesta2','groovecoaster','infinity','jubeat','none','pium','prime','prime2','pumpassorted','sdvx','simplylove','stepmaniax','xx']

fastai_games = {
    'fiesta': GameMix.query.filter_by(name='Fiesta').first(),
    'fiesta2': GameMix.query.filter_by(name='Fiesta 2').first(),
    'infinity': GameMix.query.filter_by(name='Infinity').first(),
    'prime': GameMix.query.filter_by(name='Prime').first(),
    'prime2': GameMix.query.filter_by(name='Prime 2').first(),
    'pumpassorted': GameMix.query.filter_by(name='The 1st Dance Floor').first()
}

def fastai_int_to_game(i):
    return fastai_games.get(fastai_classes[i])
    

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

@scheduler.task('cron', id='update_weekly', week='*', day_of_week='mon')
def update_weekly_task():
    with scheduler.app.app_context():
        weekly_id = get_current_weekly()
        high_score = Post.query.filter_by(chart_id=weekly_id).filter(Post.date_posted >= match.start_time,
                                                                     Post.date_posted <= match.end_time).order_by(Post.score.desc()).first()
        if high_score is not None:
            create_json(high_score)
            high_score.author.weeklywins += 1
            db.session.commit()
        current_app.logger.info("Updating weekly challenge...")
        randomize_weekly(app)
        current_app.logger.info("Updated weekly challenge.")

def create_ranking(ranking='worldbest', scoretype='default'):
    scoretype = re.sub(r'\W+', '', scoretype)
    if ranking == 'worldbest':
        worldbest = {
            'WorldScores': []
        }
        for song in Song.query.all():
            if song.song_id != "" and song.song_id is not None:
                for chart in song.charts:
                    if chart.prime_rating is None:
                        continue
                    if scoretype == 'default':
                        score = Post.query.filter_by(chart_id=chart.id, status=POST_APPROVED).order_by(Post.score.desc()).first()
                        if score is not None:
                            worldbest['WorldScores'].append(
                                {
                                    'SongID': int(song.song_id, 16),
                                    'ChartLevel': chart.prime_rating,
                                    'ChartMode': get_primediff(chart.mode),
                                    'Score': score.score,
                                    'Nickname': score.author.ign
                                }
                            )
                    elif scoretype == 'exscore':
                        score = Post.query.filter_by(chart_id=chart.id, status=POST_APPROVED).order_by(Post.exscore.desc()).first()
                        if score is not None:
                            worldbest['WorldScores'].append(
                                {
                                    'SongID': int(song.song_id, 16),
                                    'ChartLevel': chart.prime_rating,
                                    'ChartMode': get_primediff(chart.mode),
                                    'Score': score.exscore,
                                    'Nickname': score.author.ign
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
        # song_ids = []
        # for song in raw_songdata:
        #     if raw_songdata[song]['song_id'] != "":
        #         song_ids.append(int(raw_songdata[song]['song_id'], 16))
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

fiesta_sort_order = GameMix.query.filter_by(name='Fiesta').first().sort_order

def check_post(post):
    """Evaluates a post and returns the status which it should be assigned.
    
    If there is something impossible which would prevent the post from being submitted, return None"""
    # return status a given post should be by looking at the post itself, returns None is something is impossible

    # --- SANITY CHECKS
    # if SS or SSS, check if full combo or 0 miss
    if post.grade in ('ss', 'sss') and post.miss > 0:
        return None

    # check if chart exists
    chart = Chart.query.get(post.chart_id)
    if chart is None:
        return None
    if platform == 'pad':
        gamemix = GameMix.query.get(post.gamemix_id)
        if gamemix is None:
            return None
    else:  # non-arcade posts should not have a game mix
        if post.gamemix_id is not None:
            return None

    # --- UNRANKED
    if post.platform != 'pad' or chart.max_combo is None or chart.weight == 0.0 or chart.mode.name in ('Co-Op', 'Routine') or gamemix.sort_order < 140:
        return POST_UNRANKED

    # --- QUEUE
    # check picture using fastai
    if score_learner is not None:
        current_app.logger.debug(f"Predicting image for post submitted by {post.author}...")
        if post.image_file is not None:
            im = Image.open(post.image_file)
            result = current_app.score_learner.predict(im)
            
        ai_gamemix = fastai_int_to_game(result[1])
        if ai_gamemix is None or ai_gamemix.sort_order < fiesta_sort_order:
            return POST_PENDING

        earliest = GameMix.query.get(chart.earliest_version_id)
        if ai_gamemix.sort_order < earliest.sort_order:  # check if chart didn't even exist until after the mix
            return POST_PENDING

        if ai_gamemix != gamemix:
            if (ai_gamemix.name == 'Prime' and gamemix.name != 'Prime JE') or (ai_gamemix.name == 'Fiesta' and gamemix.name != 'Fiesta EX'):  # these games look the same so don't worry about it
                return POST_PENDING

    return POST_APPROVED


def approve_post(post):
    '''Given a post, set it to an approved state and update the user's SP and titles.'''
    post.status = POST_APPROVED
    if Post.query.get(post.id) is None:
        db.session.add(post)
    db.session.commit()
    u = post.author
    update_user_sp(u)
    update_user_titles(u)

def queue_post(post):
    '''Given a post, add it to the moderator queue.'''
    post.status = POST_PENDING
    if Post.query.get(post.id) is None:
        db.session.add(post)
    db.session.commit()

def unrank_post(post):
    '''Given a post, set it to unranked.'''
    post.status = POST_UNRANKED
    if Post.query.get(post.id) is None:
        db.session.add(post)
    db.session.commit()
    u = post.author
    update_user_sp(u)
    update_user_titles(u)

def draft_post(post):
    '''Given a post, save it as a draft.'''
    post.status = POST_DRAFT
    if Post.query.get(post.id) is None:
        db.session.add(post)
    db.session.commit()

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