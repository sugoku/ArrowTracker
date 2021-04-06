import csv, json, math
from app.scores.utils import abbrev_charttype, calc_exscore

def calc_performance(chart, perfect, great, good, bad, miss, judgement, rush, stagepass):
    '''
        Given a Chart object, counts for perfects/greats/goods/bads/misses, 
        a judgement value, rush speed and a boolean representing a stage pass, 
        return the Skill Points (SP) for a song.
        
        If a song is unranked it will return -1.0
    '''
    if chart.max_combo is None or chart.weight == 0.0 or chart.mode.name in ('Co-Op', 'Routine'):
        return -1.0
    
    global_multiplier = chart.weight

    difficulty_weight = 2.0
    exscore_weight = 2.0
    miss_weight = 5.0

    judgement_multiplier = 1
    if judgement == 'hj':
        judgement_multiplier = 1.075
    elif judgement == 'vj':
        judgement_multiplier = 1.15

    rush_weight = 0.4

    fail_multiplier = 1.0 if stagepass else 0.75

    max_combo = chart.max_combo
    ex = calc_exscore(perfect, great, good, bad, miss)
    max_ex = calc_exscore(max_combo, 0, 0, 0, 0)
    return max(((math.pow(difficulty, math.pow(difficulty_weight, math.pow(rush, rush_weight))) * math.pow(ex / max_ex, exscore_weight) * (1.0 - (miss / max_combo * miss_weight)) * global_multiplier * judgement_multiplier * fail_multiplier), 0))

def get_diffstr(difftype, diffnum):
    return {val: key for key, val in abbrev_charttype.items()}[difftype] + str(diffnum)

# def rerate_generator():
#     rerates = {}
#     with open('rerated.csv', newline='', encoding='utf-8') as f:
#         data = csv.reader(f)
#         for row in data:
#             songname = row[3]
#             if row[2] == 'Full Song' or row[2] == 'Short Cut':
#                 songname += ' [' + row[2] + ']'
#             rerates[','.join((songname.strip(), get_diffstr(row[4].strip().replace(' (H)', ''), row[5]), row[4].strip().replace(' (H)', ''), row[5]))] = (songname.strip(), get_diffstr(row[4].strip().replace(' (H)', ''), int(row[5])), row[4].strip().replace(' (H)', ''), int(row[6]))
#     with open("rerates.json", "w", encoding='utf-8') as wf:
#         json.dump(rerates, wf, indent=4)

# def prime_to_xx_diff(post):
#     with open('rerates.json', 'r') as rerates:
#         reratedict = json.load(rerates)
#     newvalues = reratedict[','.join((post.song.strip(), post.difficulty, post.type, post.difficultynum))] # song name, difficulty string, chart type, difficulty number

#     #post.song = newvalues[0]
#     post.difficulty = newvalues[1]
#     post.type = newvalues[2]
#     post.difficultynum = newvalues[3]

# if __name__ == '__main__':
#     rerate_generator()