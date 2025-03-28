CREATE TABLE IF NOT EXISTS pep_search (
  id BIGSERIAL PRIMARY KEY,
  person_id INTEGER REFERENCES person (id),
  pep_person_id INTEGER REFERENCES pep_person (id),
  match BOOLEAN,
  match_score NUMERIC(5, 4), -- 0.0000 to 1.0000 four decimal places
  search_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  match_details JSONB
);

CREATE INDEX IF NOT EXISTS idx_pep_search_person_id ON pep_search (person_id);

CREATE INDEX IF NOT EXISTS idx_pep_search_pep_person_id ON pep_search (pep_person_id);

CREATE INDEX IF NOT EXISTS idx_pep_search_match ON pep_search (MATCH);


create or replace function pep_search_match_tgr_fn()
returns trigger
as $$
begin
    -- TODO: change the hardcoded 0.9 to a config
    if new.match_score >= 0.9 then
        insert into pep_alert (pep_search_id, date, state)
        values (new.id, new.search_date, 'pending');
    end if;

    return new;
end;
$$ language plpgsql;

drop trigger if exists pep_search_match_tgr on pep_search;
create trigger pep_search_match_tgr
    after insert on pep_search
    for each row
    execute function pep_search_match_tgr_fn();
