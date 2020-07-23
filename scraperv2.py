# Generate a complete.json using the new Pump Out database, also parse max combos and artists for songs

from sqlalchemy import create_engine, MetaData, Table, select
import json
import csv
import os
from pathlib import Path

db_uri = 'sqlite:///resources/pumpout.db'
engine = create_engine(db_uri)
conn = engine.connect()

meta = MetaData(engine)
meta.reflect()

def get_all_items(table):
    select_st = select([table])
    return conn.execute(select_st)

typeabbrev = {
    'S': 'S',
    'D': 'D',
    'SP': 'SP',
    'DP': 'DP',
    'C': 'Co-Op',
    'R': 'Routine',
    'HDB': 'HD'
}

smtype_to_stdtype = {
    'StepsType_Pump_Single': 'S',
    'StepsType_Pump_Halfdouble': 'HD',
    'StepsType_Pump_Double': 'D'
}  # this should be a fallback only because SP, DP, Co-Op charts aren't accounted for

# operation = meta.tables['operation']
# operations = {r[0]: r[1] for r in get_all_items(operation)}
# print(operations)
operations = {
    1: "ADD",
    2: "REMOVE",
    3: "UPDATE",
    4: "EXISTS",
    5: "REVIVE",
    6: "CROSS"
}

artist = meta.tables['artist']          # artistId, internalTitle
category = meta.tables['category']      # categoryId, internalTitle, sortOrder
cut = meta.tables['cut']                # cutId, internalTitle, sortOrder
label = meta.tables['label']            # labelId, internalTitle, sortOrder, description
language = meta.tables['language']      # languageId, code, internalTitle
mix = meta.tables['mix']                # mixId, gameId, internalTitle, parentMixId, sortOrder
mode = meta.tables['mode']              # modeId, internalTitle, internalAbbreviation, internalHexColor, sortOrder, padsUsed, routine, coOp, performance
stepmaker = meta.tables['stepmaker']    # stepmakerId, internalTitle
version = meta.tables['version']        # versionId, mixId, internalTitle, parentVersionId, sortOrder

print('Getting initial lists from database...')
artists = {r[0]: r[1] for r in get_all_items(artist)}
categories = {r[0]: r[1] for r in get_all_items(category)}
cuts = {r[0]: r[1] for r in get_all_items(cut)}                
labels = {r[0]: r[1] for r in get_all_items(label)}
languages = {r[0]: r[1] for r in get_all_items(language)}
mixes = {r[0]: r[2] for r in get_all_items(mix)}
modes = {r[0]: r[2] for r in get_all_items(mode)}
stepmakers = {r[0]: r[1] for r in get_all_items(stepmaker)}
versions = {r[0]: (mixes[r[1]], r[2]) if r[2] != 'default' else (mixes[r[1]],) for r in get_all_items(version)}

print('Loading Flask app for game mix list...')
from app import gamemix_pairs
mixes_to_pairindices = {gamemix_pairs[i][1]: i for i in range(len(gamemix_pairs))}
versions_to_mixes = {r[0]: r[1] for r in get_all_items(version)}

song = meta.tables['song']                                              # songId, cutId, internalTitle
songArtist = meta.tables['songArtist']                                  # songId, artistId, sortOrder, prefix
songBpm = meta.tables['songBpm']                                        # songBpmId, songId, bpmMin, bpmMax
songBpmVersion = meta.tables['songBpmVersion']                          # songBpmId, songId, versionId
songCard = meta.tables['songCard']                                      # songCardId, songId, path, sortOrder
songCardVersion = meta.tables['songCardVersion']                        # songCardId, versionId, operationId, internalDescription (NULL)
songCategory = meta.tables['songCategory']                              # songCategoryId, songId, categoryId
songCategoryVersion = meta.tables['songCategoryVersion']                # songCategoryId, songId, versionId
songGameIdentifier = meta.tables['songGameIdentifier']                  # songGameIdentifierId, songId, gameIdentifier
songGameIdentifierVersion = meta.tables['songGameIdentifierVersion']    # songGameIdentifierId, versionId, operationId, internalDescription (NULL)
# songLabel = meta.tables['songLabel']  # these two are currently empty right now
# songLabelVersion = meta.tables['songLabel'] 
songTitle = meta.tables['songTitle']                                    # songTitleId, songId, languageId, title                 
songTitleVersion = meta.tables['songTitleVersion']                      # songTitleId, songId, languageId, versionId
songVersion = meta.tables['songVersion']                                # songId, versionId, operationId, internalDescription (usually NULL)

chart = meta.tables['chart']                            # chartId, songId
chartLabel = meta.tables['chartLabel']                  # chartLabelId, chartId, labelId
chartLabelVersion = meta.tables['chartLabelVersion']    # chartLabelId, versionId, operationId, internalDescription
chartRating = meta.tables['chartRating']                # chartRatingId, chartId, modeId, difficultyId
chartRatingVersion = meta.tables['chartRatingVersion']  # chartRatingId, chartId, versionId
chartStepmaker = meta.tables['chartStepmaker']          # chartId, stepmakerId, sortOrder, prefix
chartVersion = meta.tables['chartVersion']              # chartId, versionId, operationId, internalDescription

complete = {}

print('Getting songs from database...')
# at the end of everything, set the key to the song's internal title instead of the ID
for songId, cutId, internalTitle in get_all_items(song):
    complete[songId] = {
        'id': songId,
        'song_id': '',
        'length': cuts[cutId],
        'internalTitle': internalTitle,
        'authors': [],
        'bpm': (),
        'cards': [],
        'difficulties': {},
        'titles': {},
        'versions': []
    }

for songId in complete:
    if complete[songId]['length'] in ('Full Song', 'Short Cut'):
        complete[songId]['internalTitle'] += f" [{complete[songId]['length']}]"

for songId, artistId, sortOrder, prefix in get_all_items(songArtist):
    complete[songId]['authors'].append((artists[artistId], sortOrder, prefix))
for songId in complete:
    complete[songId]['authors'].sort(key=lambda x: x[1])
    complete[songId]['authors'] = [(x[0], x[2]) for x in complete[songId]['authors']]

for songBpmId, songId, bpmMin, bpmMax in get_all_items(songBpm):
    complete[songId]['bpm'] = (bpmMin, bpmMax) if bpmMin != bpmMax else (bpmMin,)

for songCardId, songId, path, sortOrder in get_all_items(songCard):
    complete[songId]['cards'].append((path, sortOrder))
for songId in complete:
    complete[songId]['cards'].sort(key=lambda x: x[1])
    complete[songId]['cards'] = [x[0] for x in complete[songId]['cards']]

for songCategoryId, songId, categoryId in get_all_items(songCategory):
    complete[songId]['genre'] = categories[categoryId]

for songGameIdentifierId, songId, gameIdentifier in get_all_items(songGameIdentifier):
    complete[songId]['song_id'] = gameIdentifier

for songTitleId, songId, languageId, title in get_all_items(songTitle):
    complete[songId]['titles'][languages[languageId]] = title

for songId, versionId, operationId, internalDescription in get_all_items(songVersion):
    complete[songId]['versions'].append(versions[versionId] + (operations[operationId],))

print('Getting charts from database...')
charts = {chartId: {
    'id': songId,
    'labels': [],
    'difficulties': [],
    'reratename': '',
    'stepmakers': []
} for chartId, songId in get_all_items(chart)}

for chartLabelId, chartId, labelId in get_all_items(chartLabel):
    charts[chartId]['labels'].append(labels[labelId])

for chartId, stepmakerId, sortOrder, prefix in get_all_items(chartStepmaker):
    charts[chartId]['stepmakers'].append(stepmakers[stepmakerId])

print('Getting chart difficulties from database...')
for chartRatingId, chartId, modeId, difficultyId in get_all_items(chartRating):
    version = conn.execute(
        select([chartRatingVersion]) \
            .where(chartRatingVersion.c.chartRatingId == chartRatingId)) \
            .fetchone()[2]
    charts[chartId]['difficulties'].append(
        (f"{typeabbrev[modes[modeId]]}{difficultyId}", mixes_to_pairindices[mixes[versions_to_mixes[version]]])
    )

# put charts from temp dictionary into songs
for chartId in charts:
    try:
        # print(charts[chartId])
        charts[chartId]['reratename'] = ' -> '.join([f'{x[0]} ({gamemix_pairs[x[1]][1]})' for x in sorted(charts[chartId]['difficulties'], key=lambda x: x[1])])
        complete[charts[chartId]['id']]['difficulties'][max(charts[chartId]['difficulties'], key=lambda x: x[1])[0]] = charts[chartId]
    except:
        print(f"WARNING: Skipping chart with no difficulty: {chartId, charts[chartId]}")

# replace song ID keys with names instead
complete = {complete[songId]['internalTitle'].strip(): complete[songId] for songId in complete}
for songName in complete:
    del complete[songName]['internalTitle']

# duplicate checker
# for songId in complete:
#     if len(complete[songId]['titles']) > 0:
#         print(songId)

'''
    Notice:
    The below code requires files which may not be publicly available or easily reproducible
'''

# afterwards, load max combos AND displayed artist names because they are not actually in the database for some reason
maxcombo_fn = Path("resources/maxcombo20200717.csv")
# the place where your stepmania songs folder is located (with all the same simfiles as in the maxcombo.csv)
sm_dir = Path("C:\\Games\\StepMania 5.3 Outfox\\")

# maxcombo.csv structure:
# title, chart name (often empty), description, meter (numerical), chart style (difficulty), steps type, filename, grade, score, accuracy (as an integer cause i'm dumb), is full combo, max combo, perfects, greats, goods, bads, misses
with open(maxcombo_fn, 'r') as f:
    reader = csv.reader(f)
    
    tmp = [row for row in reader if len(row) <= 19]  # for now, silently remove max combos where the titles are screwed up

    # If there are more rows than expected that means the song title has commas in it, so just take the first few columns and merge them
    # for i in range(len(tmp)):
    #     if len(tmp[i]) > 19:
    #         # print(tmp[i])
    #         j = 0
    #         if tmp[i][0] in complete or tmp[i][0] in [complete[x]['titles'].get('en') for x in complete]:
    #             j += 1
    #         print(j)
    #         print(tmp[i])
    #         tmp[i] = [tmp[i][x] for x in range(j)] + [','.join(tmp[i][j : j+len(tmp[i])-19])] + tmp[i][j+len(tmp[i])-19:]
            
    #         print(tmp[i])

    maxcombos = {title: {
        'chartname': chartname,
        'description': desc,
        'meter': int(meter),
        'style': style,
        'stepstype': smtype_to_stdtype[stepstype],  # make this
        'filename': fn,
        # AutoPlayCPU results here, can be redone by hand or by retrying these specific charts
        'grade': grade,
        'score': score,
        # I messed up accuracy so I'm not going to bother putting it in
        'isfull': isfull,
        'maxcombo': maxcombo,
        'fantastic': fantastic,
        'perfect': perfect,
        'great': great,
        'good': good,
        'bad': bad,
        'miss': miss
    } for title, chartname, desc, meter, style, stepstype, fn, grade, score, acc, isfull, maxcombo, fantastic, perfect, great, good, bad, miss, _ in tmp}

# for each maxcombo option get the filename and read the artist (mostly artist) so we can have an 'author' key instead of 'authors'
for title in maxcombos:
    maxcombos[title]['song_id'] = os.path.basename(maxcombos[title]['filename']).split(' - ')[0] # extract song ID from filename
    with open(sm_dir/maxcombos[title]['filename']) as f:
        for line in f.readlines():
            tmp = line.strip()
            if '#ARTIST:' in tmp:
                maxcombos[title]['author'] = tmp.split('#ARTIST:')[1][:-1]  # Remove the ARTIST tag and semicolon/newline etc. at the end
                break
print(maxcombos)

# check for manually blacklisted songs or charts in a text file
# format will be title,difficulty,mixes,remove
# mixes is a list of mixes where this chart is not allowed (Pumptris Quattro S18 in XX is fine but S17 in Prime 2 and before is easy to cheese)
# remove determines if this chart should just not be in the database or if should merely be unranked
blacklist_fn = Path("blacklisted.csv")

# with open('app/static/gamelists/Pump it Up/complete.json', 'w') as f:
print('Exporting to JSON...')
fn = 'completev2.json'
with open(fn, 'w') as f:
    json.dump(complete, f, indent=2)
print(f"Dumped to {fn}.")