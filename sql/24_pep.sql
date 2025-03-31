
CREATE TABLE IF NOT EXISTS pep_list (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE IF NOT EXISTS pep_person (
    id SERIAL PRIMARY KEY,
    pep_list_id INTEGER NOT NULL REFERENCES pep_list (id),
    curp VARCHAR(18) CHECK (LENGTH(curp) = 18),
    rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 9 AND 13),
    name TEXT,
    first_last_name TEXT,
    second_last_name TEXT,
    full_name TEXT,
    date_of_birth DATE,
    category TEXT, -- TODO: convert to an enum
    date_not_in_charge_since DATE,
    country TEXT,
    calculated_full_name TEXT generated always as (replace(upper(coalesce(full_name, name || ' ' || first_last_name || coalesce(' ' || second_last_name, ''))), '  ', ' ') ) stored,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,
    attributes jsonb NOT NULL DEFAULT '{}',
    CONSTRAINT check_fullname_either_or
    CHECK (
        (full_name IS NOT NULL AND name IS NULL AND first_last_name IS NULL and second_last_name IS NULL)
        OR
        (full_name IS NULL AND name IS NOT NULL AND first_last_name IS NOT NULL)
    )
);

DROP TRIGGER IF EXISTS prevent_pep_person_deletion ON pep_person;

CREATE TRIGGER prevent_pep_person_deletion
  BEFORE DELETE ON pep_person
  FOR EACH ROW
  EXECUTE PROCEDURE prevent_deletion ();


CREATE INDEX IF NOT EXISTS idx_curp_pep_person ON pep_person USING HASH (curp);
CREATE INDEX IF NOT EXISTS idx_rfc_pep_person ON pep_person USING HASH (rfc);
CREATE INDEX IF NOT EXISTS idx_full_name_pep_person ON pep_person USING HASH (full_name);
CREATE INDEX IF NOT EXISTS idx_full_name_trgm_pep_person ON pep_person USING GIN (full_name gin_trgm_ops);


CREATE OR REPLACE FUNCTION pep_person_insert_tgr_fn ()
    RETURNS TRIGGER
    AS $$
DECLARE
    min_distance INTEGER;
BEGIN
    -- only check the recent ones
    if NEW.date_not_in_charge_since is not null and now() - NEW.date_not_in_charge_since > '2 years'::interval then
        return new;
    end if;

    min_distance := (SELECT value::INTEGER FROM config WHERE name = 'max_string_distance_to_match');

    INSERT INTO pep_search (person_id, pep_person_id, match, match_score, search_date)
    SELECT
      npd.person_id,
      NEW.id,
      compute_match_score(npd.name, npd.first_last_name, npd.second_last_name, NEW.calculated_full_name) > 0.9, -- TODO: change the hardcoded 0.9 to a config
      compute_match_score(npd.name, npd.first_last_name, npd.second_last_name, NEW.calculated_full_name),
      CURRENT_DATE
    FROM natural_person_details npd
        inner join person p on p.id = npd.person_id
    where p.deleted_at is null
        -- TODO: change the hardcoded 0.9 to a config
        and compute_match_score(npd.name, npd.first_last_name, npd.second_last_name, NEW.calculated_full_name) >= 0.9
    ;
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS pep_person_details_tgr ON pep_person;

CREATE TRIGGER pep_person_insert_tgr
  AFTER INSERT ON pep_person
  FOR EACH ROW
  EXECUTE FUNCTION pep_person_insert_tgr_fn ();


SELECT add_audit_triggers (ARRAY['pep_list', 'pep_person']);
