CREATE TABLE IF NOT EXISTS request (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  port INTEGER NOT NULL,
  referrer TEXT,
  request_date TEXT NOT NULL,
  request_data,
  form TEXT,
  url TEXT NOT NULL,
  access_route,
  headers TEXT NOT NULL
);
