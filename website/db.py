import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

from website.utils import current_time

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def open_db(path=None):
    if path is None:
        path = current_app.config['DATABASE']
    db = sqlite3.connect(
        path,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = dict_factory
    return db

def get_db():
    if 'db' not in g:
        g.db = open_db()

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def add_request(ip, referrer, data, form, url, access_route, headers):
    db = get_db()
    db.execute("""
    INSERT INTO requests (ip, referrer, time, data, form, url, access_route, headers)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (ip, referrer, current_time(), data, form, url, access_route, headers,))
    db.commit()
