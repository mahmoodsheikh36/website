import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    send_from_directory
)

from website.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('', methods=['GET'])
def index():
    return render_template('index.html')

@bp.route('index', methods=['GET'])
def index_page():
    return index()

@bp.route('greeting', methods=['GET', 'POST'])
def greeting_page():
    return 'greetings, friend!'

@bp.route('about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')
