from loadsongs import load_song_lists
from app import db, current_app
from sqlalchemy.sql.expression import func
import datetime
import random
import json
import app
import os
import send_webhook

songpairs, songtypes = load_song_lists()

def get_current_weekly():
    with open('weekly.json', 'r') as f:
        weeklylist = json.load(f)
    return weeklylist['chart_id']

def create_json(post):
    scoredict = {
        post.id: {
            'chart_id': post.chart_id,
            'post_id': post.id,
            'date_posted': str(post.date_posted)
        }
    }
    rootdir = os.path.join(current_app.root_path, f'static/archived_weekly')
    datedir = os.path.join(current_app.root_path, f'static/archived_weekly', datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    if not os.path.exists(datedir):
        os.makedirs(datedir)
    jsonfile = os.path.join(rootdir, datedir, f'{post.id}.json')
    with open(jsonfile, 'w+') as f:
        json.dump(scoredict, f, indent=2)

def randomize_weekly(app):
    Chart = app.pump_models.Chart
    with open('weekly.json', 'r') as f:
        weeklyjson = json.load(f)
    chart = Chart.query.filter_by(in_latest_kpump=True).order_by(func.random()).first()
    weeklyjson['chart_id'] = chart.id
    with open('weekly.json', 'w') as f:
        json.dump(weeklyjson, f, indent=2)
    send_webhook.notify(chart.id)
