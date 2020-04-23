CREATE TABLE requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  referrer TEXT,
  time int,
  data TEXT,
  form TEXT,
  url TEXT NOT NULL,
  access_route TEXT,
  headers TEXT NOT NULL
);
