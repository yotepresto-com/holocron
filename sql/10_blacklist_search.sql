CREATE TABLE IF NOT EXISTS blacklist_search (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES person(id),
    blacklist_person_id INTEGER REFERENCES blacklist_person(id),
    match BOOLEAN,
    match_score NUMERIC(5, 4), -- 0.0000 to 1.0000 four decimal places
    search_date date NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_blacklist_search_person_id ON blacklist_search (person_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_search_blacklist_person_id ON blacklist_search (blacklist_person_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_search_match ON blacklist_search (match);
