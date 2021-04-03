import logging
import traceback
import random
from flask import current_app
from flask_login import current_user
from app import db, logging, raw_songdata, scheduler, judgement_pairs
from app.models import *

#scheduler.add_job(f, args=[2,3])

# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunk(lst, n):
    '''Yield successive n-sized chunks from a given list.'''
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# https://stackoverflow.com/questions/3989016/how-to-find-all-positions-of-the-maximum-value-in-a-list
def maxes(seq):
    '''Return list of position(s) of the largest element.'''
    max_indices = []
    if seq:
        max_val = seq[0]
        for i,val in ((i,val) for i,val in enumerate(seq) if val >= max_val):
            if val == max_val:
                max_indices.append(i)
            else:
                max_val = val
                max_indices = [i]
    return max_indices


def event_id(ev, t_id, m_id=None, g_id=None):
    s = f"t{t_id}"
    if m_id is not None:
        s += f"m{m_id}"
    if g_id is not None:
        s += f"g{g_id}"
    if ev == 'start':
        s += 's'
    if ev == 'end':
        s += 'e'
    return s

def tournament_start(t_id):
    tournament = Tournament.query.get(t_id)
    tournament.progress = PROGRESS_IN_PROGRESS

    db.session.commit()

def tournament_end(t_id):
    tournament = Tournament.query.get(t_id)
    tournament.progress = PROGRESS_FINISHED

    db.session.commit()

def round_generate_matches(t_id, match_size):
    tournament = Tournament.query.get(t_id)
    participants = tournament.remaining_participants.copy()
    random.shuffle(participants)
    matchups = chunk(participants, match_size)
    for matchup in matchups:
        match = Match(tournament_id=t_id, depth=tournament.depth, participants=matchup)
        db.session.add(match)
    db.session.commit()

def match_start(m_id):
    match = Match.query.get(m_id)
    tournament = match.tournament

    match.progress = PROGRESS_IN_PROGRESS

    db.session.commit()

def match_end(m_id):
    match = Match.query.get(m_id)
    tournament = match.tournament

    # For each game in a match, calculate the winner and tally
    scores = {uid: 0 for uid in match.participants}
    for game in match.games:
        for winner in game_winner(game, tournament.tournament_type, tournament.score_type):
            scores[winner] += 1

    # Get and set the list of winners
    match.winners = maxes(scores)

    match.progress = PROGRESS_FINISHED

    db.session.commit()

def add_participant(o, u):
    '''Given a Tournament or Match object and a user, add them as a participant. Returns 0 if successful and 1 if the user is already there.'''
    participants = o.participants
    uid = u.id
    try:
        participants.index(uid)
        return 1
    except:
        o.participants = uid
    # db.session.merge(o)  # idk if needed
    db.session.commit()
    return 0

def remove_participant(o, u):
    '''Given a Tournament or Match object and a user, remove them as a participant. Returns 0 if successful and 1 if the user is already not there.'''
    participants = o.participants
    uid = u.id
    try:
        participants.remove(uid)
        # db.session.merge(o)  # idk if needed
        db.session.commit()
        return 0
    except:
        return 1

def get_match_scores(match, user_id, score_type=SCORE_DEFAULT):
    '''Given a Match object, a user ID and optionally a score type, return the valid scores for a tournament match.'''
    scores = Post.query.filter_by(user_id=uid).filter(Post.date_posted >= match.start_time,
                                                      Post.date_posted <= match.end_time)
    if score_type == SCORE_DEFAULT:
        return scores.order_by(Post.score.desc()).all()
    elif score_type == SCORE_EXSCORE:
        return scores.order_by(Post.exscore.desc()).all()

def game_winner(game, tournament_type, score_type):
    '''Given a Game object, a tournament type and optionally a score type, return a list of winners in the match.'''
    match = game.match
    # pending posts still count! it is up to the tournament organizer to make the best decision
    best_scores = []
    participants = match.participants

    if tournament_type == TOURNAMENT_STANDARD:
        for uid in participants:
            scores = Post.query.filter_by(user_id=uid).filter(Post.date_posted >= match.start_time,
                                                              Post.date_posted <= match.end_time)
            if score_type == SCORE_DEFAULT:
                best_score = scores.order_by(Post.score.desc()).first()
            elif score_type == SCORE_EXSCORE:
                best_score = scores.order_by(Post.exscore.desc()).first()
            best_scores.append(best_score if best_score is not None else -1)

    elif tournament_type in (TOURNAMENT_TEAM, TOURNAMENT_TEAM_AVG):
        for tid in participants:
            member_scores = []
            team = Team.query.get(tid)
            for uid in team.members:
                scores = Post.query.filter_by(user_id=uid).filter(Post.date_posted >= match.start_time,
                                                              Post.date_posted <= match.end_time)
                if score_type == SCORE_DEFAULT:
                    best_score = scores.order_by(Post.score.desc()).first()
                elif score_type == SCORE_EXSCORE:
                    best_score = scores.order_by(Post.exscore.desc()).first()
                member_scores.append(best_score if best_score is not None else 0)
            if tournament_type == TOURNAMENT_TEAM:
                best_scores.append(sum(member_scores))
            elif tournament_type == TOURNAMENT_TEAM_AVG:
                best_scores.append(sum(member_scores)/len(member_scores))
    
    return [participants[i] for i in maxes(best_scores)]


def restart_match(m_id):
    # how do you restart a match without wiping out the old match history? good question
    pass