# scraper-v3
# Generate a pump.db using the new Pump Out database, also parse max combos and artists for songs

from sqlalchemy import create_engine, MetaData, Table, select
import json
import csv
import os
from pathlib import Path
from app import db, create_app
from app.pump_models import *
from tqdm import tqdm

db_uri = 'sqlite:///resources/pumpout.db'
engine = create_engine(db_uri)
conn = engine.connect()

CLEAR_DB = True
CLEAR_PUMP_DB = True

app = create_app()
app.app_context().push()

if CLEAR_DB:
    print("CLEAR_DB enabled, dropping existing app.db tables...")
    db.drop_all(bind=None)
if CLEAR_PUMP_DB:
    print("CLEAR_PUMP_DB enabled, dropping existing pump.db tables...")
    db.drop_all(bind='pump')
print("Generating app.db if it doesn't exist...")
db.create_all(bind=None)
print("Generating pump.db if it doesn't exist...")
db.create_all(bind='pump')

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
    'StepsType_Pump_Halfdouble': 'HDB',
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
difficulty = meta.tables['difficulty']  # difficultyId, value, sortOrder, internalTitle, danger
cut = meta.tables['cut']                # cutId, internalTitle, sortOrder
label = meta.tables['label']            # labelId, internalTitle, sortOrder, description
language = meta.tables['language']      # languageId, code, internalTitle
mix = meta.tables['mix']                # mixId, gameId, internalTitle, parentMixId, sortOrder
mode = meta.tables['mode']              # modeId, internalTitle, internalAbbreviation, internalHexColor, sortOrder, padsUsed, routine, coOp, performance
stepmaker = meta.tables['stepmaker']    # stepmakerId, internalTitle
version = meta.tables['version']        # versionId, mixId, internalTitle, parentVersionId, sortOrder

print('Getting initial lists from database...')
artists = {artistId: Artist(id=artistId, name=internalTitle) for artistId, internalTitle in get_all_items(artist)}
categories ={categoryId: Category(id=categoryId, name=internalTitle, sort_order=sortOrder) for categoryId, internalTitle, sortOrder in get_all_items(category)}
cuts = {cutId: Length(id=cutId, name=internalTitle, sort_order=sortOrder) for cutId, internalTitle, sortOrder in get_all_items(cut)}
labels = {labelId: Label(id=labelId, name=internalTitle, sort_order=sortOrder) for labelId, internalTitle, sortOrder, description in get_all_items(label)}
languages = {languageId: Language(id=languageId, code=code, name=internalTitle) for languageId, code, internalTitle in get_all_items(language)}
mixes = {mixId: GameMix(id=mixId, name=internalTitle, short_name=internalTitle, parent_mix_id=parentMixId, sort_order=sortOrder) for mixId, gameId, internalTitle, parentMixId, sortOrder in get_all_items(mix)}
modes = {modeId: Mode(id=modeId, name=internalTitle, abbrev=internalAbbreviation, pads_used=padsUsed, panels_used=(5*padsUsed if internalAbbreviation != 'HDB' else 6), coop=bool(coOp), performance=bool(performance)) for modeId, internalTitle, internalAbbreviation, internalHexColor, sortOrder, padsUsed, routine, coOp, performance in get_all_items(mode)}
stepmakers = {stepmakerId: Stepmaker(id=stepmakerId, name=internalTitle) for stepmakerId, internalTitle in get_all_items(stepmaker)}
versions = {versionId: Version(id=versionId, gamemix=mixes[mixId], name=internalTitle, parent_version_id=parentVersionId, sort_order=sortOrder) for versionId, mixId, internalTitle, parentVersionId, sortOrder in get_all_items(version)}

mix_short_name = {
    "NX Absolute": "NXA",
    "NX2 / Next Xenesis": "NX2",
    "NX / New Xenesis": "NX",
    "The Prex 3": "Prex 3",
    "The Premiere 3": "Premiere 3",
    "The Prex 2": "Prex 2",
    "The Premiere 2": "Premiere 2",
    "The Rebirth": "Rebirth",
    "The Prex": "Prex",
    "The Premiere": "Premiere",
    "The Perfect Collection": "Perfect",
    "The Collection": "Collection",
    "The O.B.G / Season Evolution": "O.B.G SE",
    "2nd Ultimate Remix": "2nd",
    "The 1st Dance Floor": "1st"
}

for mixId in mixes:
    sn = mix_short_name.get(mixes[mixId].name)
    if sn is not None:
        mixes[mixId].short_name = sn

class Difficulty:
    def __init__(self, difficultyId, value, sortOrder, internalTitle, danger):
        self.difficultyId = difficultyId
        self.value = value
        self.sortOrder = sortOrder
        self.internalTitle = internalTitle
        self.danger = danger

difficulties = {difficultyId: Difficulty(difficultyId, value, sortOrder, internalTitle, danger) for difficultyId, value, sortOrder, internalTitle, danger in get_all_items(difficulty)}

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
    # complete[songId] = {
    #     'id': songId,
    #     'song_id': '',
    #     'length': cuts[cutId],
    #     'internalTitle': internalTitle,
    #     'authors': [],
    #     'bpm': (),
    #     'cards': [],
    #     'difficulties': {},
    #     'titles': {},
    #     'versions': []
    # }
    complete[songId] = Song(
        id=songId,
        length=cuts[cutId],
        internal_title=internalTitle
    )

for songId in complete:
    if complete[songId].length.name in ('Full Song', 'Short Cut'):
        complete[songId].internal_title += f" [{complete[songId].length.name}]"

artist_titles = {}
for songId, artistId, sortOrder, prefix in get_all_items(songArtist):
    if artist_titles.get(songId) is None:
        artist_titles[songId] = []
        artist_titles[songId].append((artistId, sortOrder, prefix))
    complete[songId].artists.append(artists[artistId])
for songId in complete:
    artist_titles[songId].sort(key=lambda x: x[1])
    s = ""
    for artistId, sortOrder, prefix in artist_titles[songId]:
        if len(s) > 0:
            s += f" {prefix}" if prefix != '' else ' &'
        s += f" {artists[artistId].name}"
    # print(s)
    complete[songId].artist = s

for songBpmId, songId, bpmMin, bpmMax in get_all_items(songBpm):
    complete[songId].bpm_min = bpmMin
    complete[songId].bpm_max = bpmMax

for songCardId, songId, path, sortOrder in get_all_items(songCard):
    if sortOrder == 0:
        complete[songId].card = path

for songCategoryId, songId, categoryId in get_all_items(songCategory):
    complete[songId].category = categories[categoryId]

for songGameIdentifierId, songId, gameIdentifier in get_all_items(songGameIdentifier):
    complete[songId].song_id = gameIdentifier

for songTitleId, songId, languageId, title in get_all_items(songTitle):
    complete[songId].titles.append(SongTitle(id=songTitleId, name=title, song=complete[songId], language=languages[languageId]))

for songId, versionId, operationId, internalDescription in get_all_items(songVersion):
    complete[songId].versions.append(versions[versionId])

print('Getting charts from database...')
# charts = {chartId: {
#     'id': songId,
#     'labels': [],
#     'difficulties': [],
#     'reratename': '',
#     'stepmakers': []
# } for chartId, songId in get_all_items(chart)}
charts = {chartId: Chart(
    id=chartId,
    song_id=songId
 ) for chartId, songId in get_all_items(chart)}

for chartLabelId, chartId, labelId in get_all_items(chartLabel):
    charts[chartId].labels.append(labels[labelId])

for chartId, stepmakerId, sortOrder, prefix in get_all_items(chartStepmaker):
    charts[chartId].stepmakers.append(stepmakers[stepmakerId])

print('Getting chart difficulties from database...')
for chartRatingId, chartId, modeId, difficultyId in get_all_items(chartRating):
    version = versions[conn.execute(
        select([chartRatingVersion]) \
            .where(chartRatingVersion.c.chartRatingId == chartRatingId)) \
            .fetchone()[2]]
    charts[chartId].difficulties.append(
        ChartDifficulty(
            id=chartRatingId,
            chart=charts[chartId],
            mode=modes[modeId],
            mode_id=modeId,
            name=f"{modes[modeId].abbrev}{difficulties[difficultyId].internalTitle}",
            rating=difficulties[difficultyId].value,
            version=version
        )
    )

# put charts from temp dictionary into songs
for chartId in charts:
    try:
        # print(charts[chartId])
        diffs = sorted(charts[chartId].difficulties, key=lambda x: x.version.sort_order)

        diffstrs = [f'{x.name} ({x.version.gamemix.name})' for x in diffs]
        # remove duplicates with python magic
        tmp = set()
        tmp_add = tmp.add
        diffstrs = [x for x in diffstrs if not (x in tmp or tmp_add(x))]
        
        charts[chartId].rerate_name = ' -> '.join(diffstrs)
        charts[chartId].name = diffs[-1].name
        charts[chartId].mode_id = diffs[-1].mode_id
        for diff in diffs:
            if diff.version.sort_order < 540:  # Prime 2 v1.00.0
                charts[chartId].prime_rating = diff.rating
        charts[chartId].earliest_version_id = diffs[0].id
        charts[chartId].latest_version_id = diffs[-1].id
        charts[chartId].rating = diffs[-1].rating
    except:
        print(f"WARNING: Skipping chart with no difficulty: {chartId}")

print("Adding objects to database session...")
for artistId in artists:
    db.session.add(artists[artistId])
for categoryId in categories:
    db.session.add(categories[categoryId])
for cutId in cuts:
    db.session.add(cuts[cutId])
for labelId in labels:
    db.session.add(labels[labelId])
for languageId in languages:
    db.session.add(languages[languageId])
for mixId in mixes:
    db.session.add(mixes[mixId])
for modeId in modes:
    db.session.add(modes[modeId])
for stepmakerId in stepmakers:
    db.session.add(stepmakers[stepmakerId])
for versionId in versions:
    db.session.add(versions[versionId])

for songId in complete:
    db.session.add(complete[songId])
for chartId in charts:
    db.session.add(charts[chartId])

print("Committing to database...")
db.session.commit()
print("Committed.")

'''
    Notice:
    The below code requires files which may not be publicly available or easily reproducible.
    Running the above code should work fine by itself, though.
'''

print("Loading max combos...")
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

    maxcombos = [{
        'title': title,
        'chartname': chartname,
        'description': desc,
        'meter': int(meter),
        'style': style,
        'stepstype': smtype_to_stdtype[stepstype],
        'filename': fn,
        # AutoPlayCPU results here, can be redone by hand or by retrying these specific charts
        'grade': grade,
        'score': score,
        # I messed up accuracy so I'm not going to bother putting it in
        'isfull': isfull,
        'maxcombo': int(maxcombo),
        'fantastic': fantastic,
        'perfect': perfect,
        'great': great,
        'good': good,
        'bad': bad,
        'miss': miss
    } for title, chartname, desc, meter, style, stepstype, fn, grade, score, acc, isfull, maxcombo, fantastic, perfect, great, good, bad, miss, _ in tmp]

song_ids = {complete[songId].song_id for songId in complete}
# for each maxcombo option get the filename and read the artist (mostly artist) so we can have an 'author' key instead of 'authors'
combos_found = 0
for i in tqdm(range(len(maxcombos))):
    ch = maxcombos[i]
    ch['song_id'] = os.path.basename(ch['filename']).split(' - ')[0].split(' ')[0] # extract song ID from filename
    if ch['song_id'] not in song_ids:
        continue
    # print(f"{ch['song_id']}")
    diffstr = f"{ch['stepstype']}{ch['meter']:02}".replace('99', '??')
    # print(diffstr)
    chart = Chart.query.join(Song).filter(Song.song_id == ch['song_id'], Chart.name == diffstr).first()
    if chart is not None:
        chart.max_combo = ch['maxcombo']
        combos_found += 1
        # print(f'Combos found: {combos_found}')
    # with open(sm_dir/maxcombos[title]['filename']) as f:
    #     for line in f.readlines():
    #         tmp = line.strip()
    #         if '#ARTIST:' in tmp:
    #             maxcombos[title]['author'] = tmp.split('#ARTIST:')[1][:-1]  # Remove the ARTIST tag and semicolon/newline etc. at the end
    #             break
print(f"Committing {combos_found} combos to database...")
db.session.commit()
print("Committed.")
# print(maxcombos)

# check for manually blacklisted songs or charts in a text file
# format will be title,difficulty,mixes,remove
# mixes is a list of mixes where this chart is not allowed (Pumptris Quattro S18 in XX is fine but S17 in Prime 2 and before is easy to cheese)
# remove determines if this chart should just not be in the database or if should merely be unranked
blacklist_fn = Path("blacklisted.csv")

# with open('app/static/gamelists/Pump it Up/complete.json', 'w') as f:
print('Exporting max combos to JSON...')
fn = 'maxcombos.json'
with open(fn, 'w') as f:
    json.dump(maxcombos, f, indent=2)
print(f"Dumped to {fn}.")