CREATE TABLE IF NOT EXISTS request (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  port INTEGER NOT NULL,
  referrer TEXT NOT NULL,
  request_date TEXT NOT NULL,
  request_data TEXT NOT NULL,
  form TEXT NOT NULL,
  url TEXT NOT NULL,
  access_route TEXT NOT NULL,
  headers TEXT NOT NULL
);
