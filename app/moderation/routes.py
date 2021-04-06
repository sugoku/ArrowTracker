import os
import logging
import traceback
import json
from flask import render_template, request, Blueprint, current_app, session, redirect, url_for, flash, Markup, jsonify
from flask_login import current_user, login_required
from app.main.forms import SearchForm, ChartSearchForm
from app.scores.forms import ScoreForm
from app.users.forms import APIKeyForm
from app.models import Post, Tournament, APIKey
from app import songlist_pairs, db, approved_ips, apikey_required, roles_required
from sqlalchemy import desc, or_
from app.config import GetChangelog
from app.main.utils import save_picture, allowed_file, valid_api_key, generate_unique_key
from app.users.utils import accesscode_to_user, user_to_primeprofile, update_user_with_primeprofile, update_user_sp, add_exp, add_pp
from app.scores.utils import *
from calc_performance import calc_performance
from werkzeug.exceptions import BadRequestKeyError

moderation = Blueprint('moderation', __name__)

@roles_required(['Moderator', 'Admin'])
@moderation.route('/mod')
def mod_page():
    return render_template('moderator.html')