
-- Blacklists
CREATE TABLE IF NOT EXISTS blacklist (
  id SERIAL PRIMARY KEY,
  short_name VARCHAR(10) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Perstons in blacklist
CREATE TABLE IF NOT EXISTS blacklist_person (
  id SERIAL PRIMARY KEY,
  blacklist_id INTEGER NOT NULL REFERENCES blacklist (id),
  type person_type NOT NULL,
  official_registration_number TEXT NOT NULL, -- requerido
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  deleted_at TIMESTAMPTZ,
  official_deletion_number TEXT,
  CONSTRAINT check_deletion_consistency CHECK ((deleted_at IS NULL AND official_deletion_number IS NULL) OR
    (deleted_at IS NOT NULL AND official_deletion_number IS NOT NULL))
);

DROP TRIGGER IF EXISTS prevent_blacklist_person_deletion ON blacklist_person;

CREATE TRIGGER prevent_blacklist_person_deletion
  BEFORE DELETE ON blacklist_person
  FOR EACH ROW
  EXECUTE PROCEDURE prevent_deletion ();

CREATE TABLE IF NOT EXISTS blacklist_person_attribute (
  id SERIAL PRIMARY KEY,
  attribute_name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS blacklist_person_attribute_value (
  id SERIAL PRIMARY KEY,
  blacklist_person_id INTEGER NOT NULL REFERENCES blacklist_person (id) ON DELETE CASCADE,
  attribute_id INTEGER NOT NULL REFERENCES blacklist_person_attribute (id) ON DELETE CASCADE,
  value TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  UNIQUE (blacklist_person_id, attribute_id)
);

CREATE INDEX IF NOT EXISTS idx_person_attribute_values ON blacklist_person_attribute_value
  (blacklist_person_id, attribute_id);

-- Natural Person Blacklist
CREATE TABLE IF NOT EXISTS blacklist_natural_person_details (
  id INTEGER NOT NULL REFERENCES blacklist_person (id) ON DELETE CASCADE,
  curp VARCHAR(18) CHECK (LENGTH(curp) = 18),
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  name TEXT NOT NULL,
  first_last_name TEXT NOT NULL,
  second_last_name TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (id)
);

DROP TRIGGER IF EXISTS prevent_blacklist_natural_person_updates ON blacklist_natural_person_details;

CREATE TRIGGER prevent_blacklist_natural_person_updates
  BEFORE UPDATE ON blacklist_natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

CREATE OR REPLACE FUNCTION blacklist_natural_person_details_tgr_fn ()
  RETURNS TRIGGER
  AS $$
DECLARE
  full_name TEXT;
BEGIN
  full_name := upper(trim(replace(format('%s %s %s', NEW.name, NEW.first_last_name, NEW.second_last_name),
    '  ', ' ')));
  INSERT INTO blacklist_search (person_id, blacklist_person_id, MATCH, match_score, search_date)
  SELECT
    npd.person_id,
    NEW.id,
    TRUE,
    1,
    CURRENT_DATE
  FROM
    natural_person_details npd
  WHERE
    upper(trim(replace(format('%s %s %s', npd.name, npd.first_last_name, npd.second_last_name),
      '  ', ' '))) = full_name
    OR npd.curp = NEW.curp
    OR npd.rfc = NEW.rfc;
  -- TODO: fuzzy search
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS blacklist_natural_person_details_tgr ON blacklist_natural_person_details;

CREATE TRIGGER blacklist_natural_person_details_tgr
  AFTER INSERT ON blacklist_natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION blacklist_natural_person_details_tgr_fn ();

-- Juridical Person Blacklist
CREATE TABLE IF NOT EXISTS blacklist_juridical_person_details (
  blacklist_person_id INTEGER NOT NULL REFERENCES blacklist_person (id) ON DELETE CASCADE,
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  legal_name TEXT NOT NULL,
  incorporation_date DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (blacklist_person_id)
);

DROP TRIGGER IF EXISTS prevent_blacklist_juridical_person_updates ON blacklist_juridical_person_details;

CREATE TRIGGER prevent_blacklist_juridical_person_updates
  BEFORE UPDATE ON blacklist_juridical_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

-- Add Audit Triggers
SELECT
  add_audit_triggers (ARRAY['blacklist', 'blacklist_person', 'blacklist_person_attribute', 'blacklist_person_attribute_value', 'blacklist_natural_person_details',
    'blacklist_juridical_person_details']);
