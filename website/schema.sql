PRAGMA foreign_keys = OFF;

CREATE TABLE requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  referrer TEXT,
  time_added int,
  request_data TEXT,
  form TEXT,
  url TEXT NOT NULL,
  access_route TEXT,
  headers TEXT NOT NULL,
  user_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  email TEXT NOT NULL,
  time_added int,
  is_admin int
);

CREATE TABLE songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_added int,
  name TEXT NOT NULL,
  audio_file_id INTEGER NOT NULL,
  duration REAL,
  bitrate int,
  codec TEXT NOT NULL,
  FOREIGN KEY (audio_file_id) REFERENCES files (id)
);

CREATE TABLE song_artists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artist_id INTEGER NOT NULL,
  song_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (artist_id) REFERENCES artists (id),
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE album_artists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artist_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (album_id) REFERENCES albums (id),
  FOREIGN KEY (artist_id) REFERENCES artists (id)
);

CREATE TABLE album_songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  index_in_album int,
  time_added int,
  FOREIGN KEY (album_id) REFERENCES albums (id),
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE single_songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  image_file_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  year INTEGER,
  time_added int,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (image_file_id) REFERENCES files (id),
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_added int,
  original_name TEXT,
  mimetype TEXT NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE static_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  FOREIGN KEY (file_id) REFERENCES files (id),
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE albums (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  year INTEGER,
  owner_id INTEGER NOT NULL,
  time_added int,
  image_file_id INTEGER NOT NULL,
  FOREIGN KEY (owner_id) REFERENCES users (id),
  FOREIGN KEY (image_file_id) REFERENCES files (id)
);

CREATE TABLE artists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  time_added int
);

CREATE TABLE artist_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_file_id INTEGER NOT NULL,
  artist_id INTEGER NOT NULL,
  FOREIGN KEY (artist_id) REFERENCES artists (id),
  FOREIGN KEY (image_file_id) REFERENCES image_file_id (id)
);

CREATE TABLE playlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  time_added int,
  owner_id INTEGER NOT NULL,
  image_file_id INTEGER NOT NULL,
  FOREIGN KEY (owner_id) REFERENCES users (id),
  FOREIGN KEY (image_file_id) REFERENCES image_file_id (id)
);

CREATE TABLE playlist_song_additions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  playlist_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (playlist_id) REFERENCES playlists (id)
);

CREATE TABLE playlist_song_removals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  playlist_id INTEGER NOT NULL,
  song_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (playlist_id) REFERENCES playlists (id)
);

CREATE TABLE liked_songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE liked_song_removals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  time_added int,
  owner_id INTEGER NOT NULL,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE collages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_added int,
  owner_id INTEGER NOT NULL,
  name TEXT,
  FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE collage_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_added int,
  file_id INTEGER NOT NULL,
  collage_id INTEGER NOT NULL,
  FOREIGN KEY (file_id) REFERENCES files (id),
  FOREIGN KEY (collage_id) REFERENCES collages (id)
);

-- audit tables --

CREATE TABLE song_name_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  time_added int,
  old_name TEXT NOT NULL,
  new_name TEXT NOT NULL,
  FOREIGN KEY (song_id) REFERENCES songs (id)
);

CREATE TABLE album_name_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  album_id INTEGER NOT NULL,
  time_added int,
  old_name TEXT NOT NULL,
  new_name TEXT NOT NULL,
  FOREIGN KEY (album_id) REFERENCES albums (id)
);

CREATE TABLE album_artist_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  album_id INTEGER NOT NULL,
  time_added int,
  old_artist_id INTEGER NOT NULL,
  new_artist_id INTEGER NOT NULL,
  FOREIGN KEY (album_id) REFERENCES albums (id),
  FOREIGN KEY (old_artist_id) REFERENCES artists (id),
  FOREIGN KEY (new_artist_id) REFERENCES artists (id)
);

CREATE TABLE song_artist_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id INTEGER NOT NULL,
  time_added int,
  old_artist_id INTEGER NOT NULL,
  new_artist_id INTEGER NOT NULL,
  FOREIGN KEY (song_id) REFERENCES songs (id),
  FOREIGN KEY (old_artist_id) REFERENCES artists (id),
  FOREIGN KEY (new_artist_id) REFERENCES artists (id)
);

CREATE TABLE album_year_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  album_id INTEGER NOT NULL,
  time_added int,
  old_year INTEGER,
  new_year INTEGER NOT NULL,
  FOREIGN KEY (album_id) REFERENCES albums (id)
);

CREATE TABLE deleted_albums (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (album_id) REFERENCES albums (id),
  FOREIGN KEY (owner_id) REFERENCES albums (id)
);

CREATE TABLE deleted_singles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  single_song_id INTEGER NOT NULL,
  time_added int,
  FOREIGN KEY (single_song_id) REFERENCES single_songs (id)
);

-- playback data collection tables

--CREATE TABLE playbacks (
--  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  owner_id INTEGER NOT NULL,
--  song_id INTEGER NOT NULL,
--  start_time int,
--  end_time int,
--  FOREIGN KEY (song_id) REFERENCES songs (id),
--  FOREIGN KEY (owner_id) REFERENCES users (id)
--);
--
--CREATE TABLE pauses (
--  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  playback_id INTEGER NOT NULL,
--  time int,
--  FOREIGN KEY (song_id) REFERENCES songs (id),
--);
--
--CREATE TABLE resumes (
--);
--
--CREATE TABLE seeks (
--);
