CREATE TABLE IF NOT EXISTS request (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  referrer TEXT,
  request_date TEXT NOT NULL,
  request_data,
  form TEXT,
  url TEXT NOT NULL,
  access_route,
  headers TEXT NOT NULL,
  user_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  email TEXT NOT NULL,
  register_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_admin INTEGER
);

CREATE TABLE IF NOT EXISTS post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  admin_only INTEGER,
  FOREIGN KEY (author_id) REFERENCES user (id)
);


CREATE TABLE IF NOT EXISTS songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER,
  name TEXT NOT NULL,
  artist TEXT NOT NULL,
  album TEXT NOT NULL,
  lyrics TEXT
);

CREATE TABLE IF NOT EXISTS user_static_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  add_timestamp int,
  file_path TEXT NOT NULL,
  original_file_name TEXT,
  owner_comment TEXT
);

CREATE TABLE IF NOT EXISTS song_audio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  user_static_file_id INTEGER NOT NULL,
  duration int,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (user_static_file_id) REFERENCES user_static_files (id)
);

CREATE TABLE IF NOT EXISTS song_audio_edits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  old_song_audio_addition_id INTEGER NOT NULL,
  new_song_audio_addition_id INTEGER,
  FOREIGN KEY (old_song_audio_addition_id) REFERENCES song_audio_additions (id),
  FOREIGN KEY (new_song_audio_addition_id) REFERENCES song_audio_additions (id)
);
