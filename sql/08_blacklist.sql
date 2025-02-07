-- Blacklists
CREATE TABLE IF NOT EXISTS blacklist (
  id SERIAL PRIMARY KEY,
  name VARCHAR(10) UNIQUE NOT NULL,
  description TEXT,
  attributes_schema jsonb NOT NULL DEFAULT '{}',
  import_configuration jsonb NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Blacklisted Persons
CREATE TABLE IF NOT EXISTS blacklist_person (
  id SERIAL PRIMARY KEY,
  blacklist_id INTEGER NOT NULL REFERENCES blacklist (id),
  type person_type NOT NULL,
  official_registration_number TEXT NOT NULL, -- requerido
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  deleted_at TIMESTAMPTZ,
  official_deletion_number TEXT,
  attributes jsonb NOT NULL DEFAULT '{}',
  CONSTRAINT check_deletion_consistency CHECK ((deleted_at IS NULL AND official_deletion_number IS NULL) OR
    (deleted_at IS NOT NULL AND official_deletion_number IS NOT NULL))
);

DROP TRIGGER IF EXISTS prevent_blacklist_person_deletion ON blacklist_person;

CREATE TRIGGER prevent_blacklist_person_deletion
  BEFORE DELETE ON blacklist_person
  FOR EACH ROW
  EXECUTE PROCEDURE prevent_deletion ();

-- Natural Person Blacklist
CREATE TABLE IF NOT EXISTS blacklist_natural_person_details (
  id SERIAL PRIMARY KEY,
  blacklist_person_id INTEGER NOT NULL UNIQUE REFERENCES blacklist_person (id) ON DELETE CASCADE,
  curp VARCHAR(18) CHECK (LENGTH(curp) = 18),
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  name TEXT,
  first_last_name TEXT,
  second_last_name TEXT,
  full_name TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  calculated_full_name TEXT generated always as (upper(coalesce(full_name, name || ' ' || first_last_name || coalesce(' ' || second_last_name, '')))) stored,
  CONSTRAINT check_fullname_either_or
    CHECK (
      (full_name IS NOT NULL AND name IS NULL AND first_last_name IS NULL and second_last_name IS NULL)
      OR
      (full_name IS NULL AND name IS NOT NULL AND first_last_name IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_curp_blacklist_natural_details ON blacklist_natural_person_details USING HASH (curp);
CREATE INDEX IF NOT EXISTS idx_rfc_blacklist_natural_details ON blacklist_natural_person_details USING HASH (rfc);
CREATE INDEX IF NOT EXISTS idx_full_name_blacklist_natural_details ON blacklist_natural_person_details USING HASH (full_name);
CREATE INDEX IF NOT EXISTS idx_full_name_trgm_blacklist_natural_details ON blacklist_natural_person_details USING GIN (full_name gin_trgm_ops);

-- Juridical Person Blacklist
CREATE TABLE IF NOT EXISTS blacklist_juridical_person_details (
  blacklist_person_id INTEGER NOT NULL REFERENCES blacklist_person (id) ON DELETE CASCADE,
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  legal_name TEXT NOT NULL,
  incorporation_date DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (blacklist_person_id)
);

-- Natural Person TRIGGERS
DROP TRIGGER IF EXISTS prevent_blacklist_natural_person_updates ON blacklist_natural_person_details;

CREATE TRIGGER prevent_blacklist_natural_person_updates
  BEFORE UPDATE ON blacklist_natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

CREATE OR REPLACE FUNCTION blacklist_natural_person_match_fn(
    _person_name            TEXT,
    _person_first_last_name TEXT,
    _person_second_last_name TEXT,
    _blacklist_name         TEXT,
    _blacklist_last_name    TEXT,
    _blacklist_full_name    TEXT
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
AS $$
DECLARE
    -- Combined name for the 'person' side
    person_full_name    TEXT;
    -- Combined name for the 'blacklist' side
    blacklist_full_name TEXT;
    distance            INTEGER;
    max_len             INTEGER;
BEGIN
    /*
      1) Combine person's parts:
         - If _person_name is not null, use it.
         - Then add first last name (if present).
         - Then add second last name (if present).
         - This effectively is "first_name + ' ' + first_last_name + ' ' + second_last_name"
         - We trim extra spaces at the end just in case.
    */
    person_full_name := COALESCE(_person_name, '')
                       || CASE WHEN _person_first_last_name IS NOT NULL THEN ' ' || _person_first_last_name ELSE '' END
                       || CASE WHEN _person_second_last_name IS NOT NULL THEN ' ' || _person_second_last_name ELSE '' END;

    person_full_name := btrim(person_full_name);

    /*
      2) Combine blacklist parts:
         - Use _blacklist_full_name if present,
           otherwise "blacklist_name + ' ' + blacklist_last_name"
         - Also trim extraneous spaces.
    */
blacklist_full_name := COALESCE(
        btrim(_blacklist_full_name),
        btrim(_blacklist_name || ' ' || COALESCE(_blacklist_last_name, ''))
    );

    -- 3) Check if they match exactly:
    IF person_full_name = blacklist_full_name THEN
        RETURN 1.0;
    END IF;

    -- 4) If not exact, compute Levenshtein-based similarity:
    distance := levenshtein(person_full_name, blacklist_full_name);
    max_len  := GREATEST(length(person_full_name), length(blacklist_full_name));

    -- Avoid division by zero; if both strings are empty, similarity is 0.
    IF max_len = 0 THEN
        RETURN 0.0;
    END IF;

    RETURN (1.0 * (max_len - distance)) / max_len;
END;
$$;



CREATE OR REPLACE FUNCTION blacklist_natural_person_details_tgr_fn ()
  RETURNS TRIGGER
  AS $$
DECLARE
  _row_count INTEGER;
  min_distance INTEGER;
BEGIN
  min_distance := (SELECT value::INTEGER FROM config WHERE name = 'max_string_distance_to_match');

    INSERT INTO blacklist_search (person_id, blacklist_person_id, MATCH, match_score, search_date)
    SELECT
      npd.person_id,
      NEW.blacklist_person_id,
      TRUE,
      blacklist_natural_person_match_fn(
              npd.name,
              npd.first_last_name,
              npd.second_last_name,
              NEW.name,
              NEW.first_last_name || coalesce(' ' || NEW.second_last_name, ''),
              NEW.full_name),
      CURRENT_DATE
    FROM
      natural_person_details npd;
--     WHERE
--       levenshtein (npd.full_name, NEW.full_name) < min_distance; TODO: Add a config flag to toggle this on/off
   RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS blacklist_natural_person_details_tgr ON blacklist_natural_person_details;

CREATE TRIGGER blacklist_natural_person_details_tgr
  AFTER INSERT ON blacklist_natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION blacklist_natural_person_details_tgr_fn ();


-- Juridical person TRIGGERS
DROP TRIGGER IF EXISTS prevent_blacklist_juridical_person_updates ON blacklist_juridical_person_details;

CREATE TRIGGER prevent_blacklist_juridical_person_updates
  BEFORE UPDATE ON blacklist_juridical_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

-- Add Audit TRIGGERS
SELECT
  add_audit_triggers (ARRAY['blacklist', 'blacklist_person', 'blacklist_natural_person_details',
      'blacklist_juridical_person_details']);
