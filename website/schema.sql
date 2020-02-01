CREATE TABLE IF NOT EXISTS requests (
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
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS users (
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
  FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  lyrics TEXT,
  time_added int,
  owner_id INTEGER NOT NULL,
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS song_artists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artist_id INTEGER NOT NULL,
  song_id INTEGER NOT NULL,
  FOREIGN KEY (artist_id) REFERENCES artists (id),
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE IF NOT EXISTS album_songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  FOREIGN KEY (album_id) REFERENCES albums (id),
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE IF NOT EXISTS single_songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE IF NOT EXISTS user_static_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  time_added int,
  file_name TEXT NOT NULL,
  original_file_name TEXT,
  owner_comment TEXT,
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS song_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  user_static_file_id INTEGER NOT NULL,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (user_static_file_id) REFERENCES user_static_files (id)
);

CREATE TABLE IF NOT EXISTS song_image_edits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  old_song_image_id INTEGER NOT NULL,
  new_song_image_id INTEGER,
  FOREIGN KEY (new_song_image_id) REFERENCES song_image (id),
  FOREIGN KEY (old_song_image_id) REFERENCES song_image (id)
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
  old_song_audio_id INTEGER NOT NULL,
  new_song_audio_id INTEGER,
  FOREIGN KEY (old_song_audio_id) REFERENCES song_audio (id),
  FOREIGN KEY (new_song_audio_id) REFERENCES song_audio (id)
);

CREATE TABLE IF NOT EXISTS albums (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  artist_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (artist_id) REFERENCES artists (id),
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS album_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_static_file_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  FOREIGN KEY (user_static_file_id) REFERENCES user_static_files (id),
  FOREIGN KEY (album_id) REFERENCES albums (id)
);

CREATE TABLE IF NOT EXISTS artists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  time_added int
);
