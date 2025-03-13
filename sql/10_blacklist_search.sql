CREATE TABLE IF NOT EXISTS blacklist_search (
  id BIGSERIAL PRIMARY KEY,
  person_id INTEGER REFERENCES person (id),
  blacklist_person_id INTEGER REFERENCES blacklist_person (id),
  match BOOLEAN,
  match_score NUMERIC(5, 4), -- 0.0000 to 1.0000 four decimal places
  search_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  match_details JSONB
);

CREATE INDEX IF NOT EXISTS idx_blacklist_search_person_id ON blacklist_search (person_id);

CREATE INDEX IF NOT EXISTS idx_blacklist_search_blacklist_person_id ON blacklist_search (blacklist_person_id);

CREATE INDEX IF NOT EXISTS idx_blacklist_search_match ON blacklist_search (MATCH);


create or replace function  blacklist_search_match_tgr_fn()
returns trigger
as $$
begin
    -- TODO: change the hardcoded 0.9 to a config
    if new.match_score >= 0.9 then
        insert into blacklist_alert (blacklist_search_id, date, state)
        values (new.id, new.search_date, 'pending');
    end if;

    return new;
end;
$$ language plpgsql;

drop trigger if exists blacklist_search_match_tgr on blacklist_search;
create trigger blacklist_search_match_tgr
    after insert on blacklist_search
    for each row
    execute function blacklist_search_match_tgr_fn();
