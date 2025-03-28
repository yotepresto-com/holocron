CREATE TABLE IF NOT EXISTS pep_alert (
  id SERIAL PRIMARY KEY,
  pep_search_id INTEGER NOT NULL REFERENCES pep_search (id),
  state alert_state NOT NULL,
  date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pep_alert_search ON pep_alert (pep_search_id);
