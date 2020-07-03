from sqlalchemy import and_
from app.models import *

def song_passed(u, song, difficulty):
    return Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED, \
        Post.song == song, \
        Post.difficulty == difficulty, \
        Post.stagepass == 'True')).first() != None

def song_passed_grade(u, song, difficulty, lettergrades):
    return Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED, \
        Post.song == song, \
        Post.difficulty == difficulty, \
        Post.stagepass == 'True', \
        Post.lettergrade.in_(lettergrades))).first() != None

def score_exists(u, song=None, difficulty=None, stagepass=None, lettergrades=None, perfect=None, great=None, good=None, bad=None, miss=None, score=None):
    q = Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED))
    if song != None:
        q = q.filter(Post.song == song)
    if difficulty != None:
        q = q.filter(Post.difficulty == difficulty)
    if stagepass != None:
        q = q.filter(Post.stagepass == str(stagepass))
    if lettergrades != None:
        q = q.filter(Post.lettergrade.in_(lettergrades))
    if perfect != None:
        q = q.filter(Post.perfect == perfect)
    if great != None:
        q = q.filter(Post.great == great)
    if good != None:
        q = q.filter(Post.good == good)
    if bad != None:
        q = q.filter(Post.bad == bad)
    if miss != None:
        q = q.filter(Post.miss == miss)
    if score != None:
        q = q.filter(Post.score == score)
    return q.first() != None

def has_unique_clears(u, count, diffbounds, co_op=False, lettergrades=None):
    if count <= 0: return True
    q = Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED, \
        Post.stagepass == 'True'))
    if not co_op:
        q = q.filter(diffbounds[0] <= Post.difficultynum <= diffbounds[1])
    if co_op:
        q = q.filter(Post.difficulty.contains('Co-Op'))
    if lettergrades != None:
        q = q.filter(Post.lettergrade.in_(lettergrades))
    q = q.all()
    clears = 0
    songs = set()
    for post in q:
        if post.song not in songs:
            songs.add(post.song)
            clears += 1
        if clears >= count:
            return True
    return False

def last_n_scores_match(u, n, lettergrades=None):
    q = Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED))
    q = q.limit(n).all()
    if len(q) != n:
        return False
    for post in q:
        if post.stagepass == 'False' or post.lettergrade not in lettergrades:
            return False
    return True

def judge_count(u, judge, stagepass=True):
    q = Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED))
    if stagepass:
        q.filter(Post.stagepass == 'True')
    i = 0
    for post in q.all():
        if judge == 'perfect':
            i += post.perfect
        elif judge == 'great':
            i += post.great
        elif judge == 'good':
            i += post.good
        elif judge == 'bad':
            i += post.bad
        elif judge == 'miss':
            i += post.miss
    return i

def post_count(u, stagepass=False):
    q = Post.query.filter(and_(Post.user_id == u.id, \
        Post.status == POST_APPROVED))
    if stagepass:
        q.filter(Post.stagepass == 'True')
    return len(q.all())

def has_titles(u, titles):
    for title in titles:
        if not u.has_role(title):
            return False
    return True

xx = '[XX]'

half = 'Half'
gimmick = 'Gimmick'
drill = 'Drill'
twist = 'Twist'
run = 'Run'

level = 'Lv.'
expert = 'EXPERT'
specialist = 'Specialist'

tier_intermediate = 'Intermediate'
tier_advanced = 'Advanced'
tier_expert = 'Expert'
tier_master = 'The Master'

co_op = 'Co-Op'
co_op_lv1 = 'Beginner'
co_op_lv2 = 'Intermediate'
co_op_lv3 = 'Advanced'
co_op_lv4 = 'Expert'
co_op_max = 'Lovers'

xx_title_grades = ['ss', 'sss']
s_grades = ['s', 'ss', 'sss']
ss_grades = s_grades[1:]
sss_grades = ss_grades[1:]

grade_sss = '[SSS]'
grade_ss = '[SS]'
grade_s = '[S]'
grade_a = '[A]'
grade_b = '[B]'
grade_c = '[C]'
grade_d = '[D]'
grade_f = '[F]'

judge_great = '[Great]'
judge_good = '[Good]'
judge_bad = '[Bad]'

prime2vip = 'Prime 2 VIP'
prime2specialist = 'Prime 2 Specialist'

gold = 'Gold'
platinum = 'Platinum'
diamond = 'Diamond'
vip = 'VIP'

scrooge = 'Scrooge'
cheater = 'Cheater'
macnom = 'Macnom'
pump_is_a_sense = 'Pump Is A Sense'
no_skill_no_pump = 'No Skill No Pump'
goinmul = '고인물'
king_gregory = 'King Gregory'

aevilux = "AEVILUX"
applesoda = "APPLESODA"
atas = "ATAS"
bme = "BME"
conrad = "CONRAD"
dm_ashura = "DM ASHURA"
doin = "DOIN"
exc = "EXC"
fefemz = "FEFEMZ"
hyun = "HyuN"
kien = "Kien"
max_ = "MAX"
nato = "NATO"
nimgo = "NIMGO"
osing = "OSING"
quree = "QUREE"
shk = "SHK"
spham = "SPHAM"
sunny = "SUNNY"
windforce = "WINDFORCE"
bpm = "BPM"

titles = {
    f"{xx} {half} {level} 1": lambda u: song_passed_grade(u=u, song="Trashy Innocence", difficulty='D16', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 2": lambda u: song_passed_grade(u=u, song="Butterfly", difficulty='D17', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 3": lambda u: song_passed_grade(u=u, song="Shub Niggurath", difficulty='D18', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 4": lambda u: song_passed_grade(u=u, song="Super Fantasy", difficulty='D18', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 5": lambda u: song_passed_grade(u=u, song="Phantom", difficulty='D19', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 6": lambda u: song_passed_grade(u=u, song="Utsushiyo Kaze", difficulty='D20', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 7": lambda u: song_passed_grade(u=u, song="Witch Doctor #1", difficulty='D21', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 8": lambda u: song_passed_grade(u=u, song="Bad Apple [Full Song]", difficulty='D22', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 9": lambda u: song_passed_grade(u=u, song="Danger Zone Try to B.P.M.", difficulty='D23', lettergrades=xx_title_grades),
    f"{xx} {half} {level} 10": lambda u: song_passed_grade(u=u, song="Imprinting", difficulty='D24', lettergrades=xx_title_grades),
    f"{xx} {half} {expert}": lambda u: has_titles(u=u, titles=[f"{xx} {half} {level} {i}" for i in range(10)]),

    f"{xx} {gimmick} {level} 1": lambda u: song_passed_grade(u=u, song="Yeo Rae A", difficulty='S13', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 2": lambda u: song_passed_grade(u=u, song="Bad Apple", difficulty='S15', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 3": lambda u: song_passed_grade(u=u, song="Love Scenario", difficulty='S17', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 4": lambda u: song_passed_grade(u=u, song="Come to Me", difficulty='S17', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 5": lambda u: song_passed_grade(u=u, song="Rock the House [Short Cut]", difficulty='S18', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 6": lambda u: song_passed_grade(u=u, song="Miss S Story", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 7": lambda u: song_passed_grade(u=u, song="Nakakapagpabagabag", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 8": lambda u: song_passed_grade(u=u, song="Twist of Fate", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 9": lambda u: song_passed_grade(u=u, song="Everybody Got 2 Know", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {level} 10": lambda u: song_passed_grade(u=u, song="86", difficulty='S20', lettergrades=xx_title_grades),
    f"{xx} {gimmick} {expert}": lambda u: has_titles(u=u, titles=[f"{xx} {gimmick} {level} {i}" for i in range(10)]),

    f"{xx} {drill} {level} 1": lambda u: song_passed_grade(u=u, song="Vook", difficulty='S15', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 2": lambda u: song_passed_grade(u=u, song="Solitary 1.5", difficulty='S16', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 3": lambda u: song_passed_grade(u=u, song="GunRock", difficulty='S17', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 4": lambda u: song_passed_grade(u=u, song="Moonlight", difficulty='S18', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 5": lambda u: song_passed_grade(u=u, song="Vacuum", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 6": lambda u: song_passed_grade(u=u, song="Overblow", difficulty='S20', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 7": lambda u: song_passed_grade(u=u, song="Sorceress Elise", difficulty='S21', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 8": lambda u: song_passed_grade(u=u, song="Rock the House", difficulty='D22', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 9": lambda u: song_passed_grade(u=u, song="Witch Doctor", difficulty='D23', lettergrades=xx_title_grades),
    f"{xx} {drill} {level} 10": lambda u: song_passed_grade(u=u, song="Wi-Ex-Doc-Va", difficulty='D24', lettergrades=xx_title_grades),
    f"{xx} {drill} {expert}": lambda u: has_titles(u=u, titles=[f"{xx} {drill} {level} {i}" for i in range(10)]),

    f"{xx} {twist} {level} 1": lambda u: song_passed_grade(u=u, song="Street Showdown", difficulty='S15', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 2": lambda u: song_passed_grade(u=u, song="Final Audition 3 U.F", difficulty='S16', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 3": lambda u: song_passed_grade(u=u, song="U Got Me Rocking", difficulty='S17', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 4": lambda u: song_passed_grade(u=u, song="Final Audition 1", difficulty='D18', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 5": lambda u: song_passed_grade(u=u, song="Super Fantasy", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 6": lambda u: song_passed_grade(u=u, song="Witch Doctor #1", difficulty='D20', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 7": lambda u: song_passed_grade(u=u, song="Love is a Danger Zone", difficulty='D21', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 8": lambda u: song_passed_grade(u=u, song="Love is a Danger Zone 2", difficulty='S22', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 9": lambda u: song_passed_grade(u=u, song="LiaDZ (Cranky Mix)", difficulty='D23', lettergrades=xx_title_grades),
    f"{xx} {twist} {level} 10": lambda u: song_passed_grade(u=u, song="Bee", difficulty='D24', lettergrades=xx_title_grades),
    f"{xx} {twist} {expert}": lambda u: has_titles(u=u, titles=[f"{xx} {twist} {level} {i}" for i in range(10)]),

    f"{xx} {run} {level} 1": lambda u: song_passed_grade(u=u, song="Final Audition 1", difficulty='D15', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 2": lambda u: song_passed_grade(u=u, song="Super Fantasy", difficulty='S16', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 3": lambda u: song_passed_grade(u=u, song="Pavane", difficulty='S17', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 4": lambda u: song_passed_grade(u=u, song="Gothique Resonance", difficulty='S18', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 5": lambda u: song_passed_grade(u=u, song="Napalm", difficulty='S19', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 6": lambda u: song_passed_grade(u=u, song="Bee", difficulty='D20', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 7": lambda u: song_passed_grade(u=u, song="Sarabande D21", difficulty='D21', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 8": lambda u: song_passed_grade(u=u, song="Just Hold On (To All Fighters) D22", difficulty='D22', lettergrades=xx_title_grades),
    f"{xx} {run} {level} 9": lambda u: song_passed_grade(u=u, song="Final Audition Ep. 2-X", difficulty='S23', lettergrades=s_grades),
    f"{xx} {run} {level} 10": lambda u: song_passed_grade(u=u, song="Yog-Sothoth", difficulty='D24', lettergrades=xx_title_grades),
    f"{xx} {run} {expert}": lambda u: has_titles(u=u, titles=[f"{xx} {run} {level} {i}" for i in range(10)]),
    f"{xx} {specialist}": lambda u: has_titles(u=u, titles=[f"{xx} {sk} {expert}" for sk in (half, gimmick, drill, twist, run)]),

    f"{xx} {tier_intermediate} {level} 1": lambda u: has_unique_clears(u=u, count=25, diffbounds=(10, 11)),
    f"{xx} {tier_intermediate} {level} 2": lambda u: has_unique_clears(u=u, count=50, diffbounds=(10, 11)),
    f"{xx} {tier_intermediate} {level} 3": lambda u: has_unique_clears(u=u, count=25, diffbounds=(12, 13)),
    f"{xx} {tier_intermediate} {level} 4": lambda u: has_unique_clears(u=u, count=50, diffbounds=(12, 13)),
    f"{xx} {tier_intermediate} {level} 5": lambda u: has_unique_clears(u=u, count=25, diffbounds=(14, 15)),
    f"{xx} {tier_intermediate} {level} 6": lambda u: has_unique_clears(u=u, count=50, diffbounds=(14, 15)),
    f"{xx} {tier_intermediate} {level} 7": lambda u: has_unique_clears(u=u, count=25, diffbounds=(16, 17)),
    f"{xx} {tier_intermediate} {level} 8": lambda u: has_unique_clears(u=u, count=50, diffbounds=(16, 17)),
    f"{xx} {tier_intermediate} {level} 9": lambda u: has_unique_clears(u=u, count=25, diffbounds=(18, 19)),
    f"{xx} {tier_intermediate} {level} 10": lambda u: has_unique_clears(u=u, count=50, diffbounds=(18, 19)),

    f"{xx} {tier_advanced} {level} 1": lambda u: has_unique_clears(u=u, count=25, diffbounds=(20, 20)),
    f"{xx} {tier_advanced} {level} 2": lambda u: has_unique_clears(u=u, count=50, diffbounds=(20, 20)),
    f"{xx} {tier_advanced} {level} 3": lambda u: has_unique_clears(u=u, count=25, diffbounds=(21, 21)),
    f"{xx} {tier_advanced} {level} 4": lambda u: has_unique_clears(u=u, count=50, diffbounds=(21, 21)),
    f"{xx} {tier_advanced} {level} 5": lambda u: has_unique_clears(u=u, count=20, diffbounds=(22, 22)),
    f"{xx} {tier_advanced} {level} 6": lambda u: has_unique_clears(u=u, count=40, diffbounds=(22, 22)),
    f"{xx} {tier_advanced} {level} 7": lambda u: has_unique_clears(u=u, count=60, diffbounds=(22, 22)),
    f"{xx} {tier_advanced} {level} 8": lambda u: has_unique_clears(u=u, count=20, diffbounds=(23, 23)),
    f"{xx} {tier_advanced} {level} 9": lambda u: has_unique_clears(u=u, count=40, diffbounds=(23, 23)),
    f"{xx} {tier_advanced} {level} 10": lambda u: has_unique_clears(u=u, count=60, diffbounds=(23, 23)),

    f"{xx} {tier_expert} {level} 1": lambda u: has_unique_clears(u=u, count=30, diffbounds=(24, 24)),
    f"{xx} {tier_expert} {level} 2": lambda u: has_unique_clears(u=u, count=15, diffbounds=(25, 25)),
    f"{xx} {tier_expert} {level} 3": lambda u: has_unique_clears(u=u, count=7, diffbounds=(26, 26)),
    f"{xx} {tier_expert} {level} 4": lambda u: has_unique_clears(u=u, count=3, diffbounds=(27, 27)),

    f"{xx} {tier_master}": lambda u: song_passed(u=u, song="PARADOXX", difficulty='D28'),  # this might be D28 in general, not sure
    
    f"{xx} {co_op} {co_op_lv1}": lambda u: has_unique_clears(u=u, count=15, co_op=True),
    f"{xx} {co_op} {co_op_lv2}": lambda u: has_unique_clears(u=u, count=20, co_op=True, lettergrades=s_grades),
    f"{xx} {co_op} {co_op_lv3}": lambda u: has_unique_clears(u=u, count=20, co_op=True, lettergrades=ss_grades),
    f"{xx} {co_op} {co_op_lv4}": lambda u: has_unique_clears(u=u, count=40, co_op=True, lettergrades=sss_grades),
    f"{xx} {co_op_max}": lambda u: has_unique_clears(u=u, count=69, co_op=True),

    f"{xx} {grade_sss}uper Man": lambda u: last_n_scores_match(u=u, n=15, lettergrades=['sss']),
    f"{xx} {grade_ss}uper Man": lambda u: last_n_scores_match(u=u, n=15, lettergrades=['ss']),
    f"{xx} {grade_s}uper Man": lambda u: last_n_scores_match(u=u, n=15, lettergrades=['s']),
    f"{xx} {grade_a}ce Player": lambda u: last_n_scores_match(u=u, n=15, lettergrades=['a']),
    f"{xx} {grade_b}est Player": lambda u: last_n_scores_match(u=u, n=15, lettergrades=['b']),
    f"{xx} {grade_c}apable Player": lambda u: last_n_scores_match(u=u, n=5, lettergrades=['c']) and has_grades(u=u, n=20),
    f"{xx} {grade_d}azzling Player": lambda u: last_n_scores_match(u=u, n=12, lettergrades=['d']),
    f"{xx} {grade_f}antastic Player": lambda u: last_n_scores_match(u=u, n=2, lettergrades=['f']),

    f"{xx} {judge_great} Player": lambda u: judge_count(u=u, judge='great') > 10000,
    f"{xx} {judge_good} Player": lambda u: judge_count(u=u, judge='good') > 10000,
    f"{xx} {judge_bad} Player": lambda u: judge_count(u=u, judge='bad') > 10000,

    f"{xx} {gold} Member": lambda u: post_count(u) > 300,  # 100 play count = ~300 score count
    f"{xx} {platinum} Member": lambda u: post_count(u) > 1500,  # 500 play count = ~1500 score count
    f"{xx} {diamond} Member": lambda u: post_count(u) > 3000,  # 1000 play count = ~3000 score count
    f"{xx} {vip} Member": lambda u: post_count(u) > 6000,  # 2000 play count = ~6000 score count

    f"{xx} {scrooge}": lambda u: u.pp > 200000,
    f"{xx} {cheater}": score_exists(u=u, difficulty='D26', lettergrades=xx_title_grades),  
    # f"{xx} {macnom}": lambda u: judge_count(u=u, judge='bad') > 10000,
    f"{xx} {pump_is_a_sense}": lambda u: song_passed_grade(u=u, song="Love is a Danger Zone", difficulty='D21', lettergrades=xx_title_grades),
    f"{xx} {no_skill_no_pump}": lambda u: song_passed_grade(u=u, song="Moonlight", difficulty='D21', lettergrades=xx_title_grades),  
    # it's SS technically for both of the above titles but i'm assuming SSS counts as well
    # f"{xx} {goinmul}": lambda u: judge_count(u=u, judge='bad') > 10000,
    f"{xx} {king_gregory}": lambda u: u.has_role('Moderator'),

    f"{xx} {bpm}": lambda u: score_exists(u=u, song="Beethoven Virus", difficulty='D18', stagepass=True, great=1, good=0, bad=0, miss=2),  

}

# XX titles based on Kyle's XX Unlock Guide
# https://docs.google.com/spreadsheets/d/1YOUOZogs5I0YlMw-1uBI7HXaMAZKjRg5h0XJ4csJh7Y/edit#gid=1708841500