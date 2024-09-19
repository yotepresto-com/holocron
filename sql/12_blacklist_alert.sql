DO $$
BEGIN
  IF NOT EXISTS (
    SELECT
      1
    FROM
      pg_type
    WHERE
      typname = 'alert_state') THEN
  CREATE TYPE alert_state AS ENUM (
    'pending',
    'suppressed',
    'discarded',
    'closed',
    'reported'
);
END IF;
END
$$;

CREATE TABLE IF NOT EXISTS blacklist_alert (
  id SERIAL PRIMARY KEY,
  blacklist_search_id INTEGER NOT NULL REFERENCES blacklist_search (id),
  state alert_state NOT NULL,
  date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_blacklist_alert_search ON blacklist_alert (blacklist_search_id);
