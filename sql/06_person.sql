CREATE TABLE IF NOT EXISTS person (
  id SERIAL PRIMARY KEY,
  type person_type NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  deleted_at TIMESTAMPTZ
);

DROP TRIGGER IF EXISTS prevent_person_deletion ON person;

CREATE TRIGGER prevent_person_deletion
  BEFORE DELETE ON person
  FOR EACH ROW
  EXECUTE PROCEDURE prevent_deletion ();

CREATE TABLE IF NOT EXISTS natural_person_details (
  person_id INTEGER NOT NULL REFERENCES person (id) ON DELETE CASCADE,
  curp VARCHAR(18) CHECK (LENGTH(curp) = 18),
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  name TEXT NOT NULL,
  first_last_name TEXT NOT NULL,
  second_last_name TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (person_id)
);

DROP TRIGGER IF EXISTS prevent_natural_person_updates ON natural_person_details;

CREATE TRIGGER prevent_natural_person_updates
  BEFORE UPDATE ON natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

CREATE INDEX IF NOT EXISTS idx_curp_natural_details ON natural_person_details (curp);

CREATE INDEX IF NOT EXISTS idx_rfc_natural_details ON natural_person_details (rfc);

CREATE OR REPLACE FUNCTION natural_person_details_tgr_fn ()
  RETURNS TRIGGER
  AS $$
DECLARE
  full_name TEXT;
  _row_count INTEGER;
  min_distance INTEGER;
BEGIN
  min_distance := (SELECT value::INTEGER FROM config WHERE name = 'max_string_distance_to_match');

  full_name := upper(trim(replace(format('%s %s %s', NEW.name, NEW.first_last_name, NEW.second_last_name),
    '  ', ' ')));
  INSERT INTO blacklist_search (person_id, blacklist_person_id, MATCH, match_score, search_date)
  SELECT
    NEW.person_id,
    bl_npd.id,
    TRUE,
    1,
    CURRENT_DATE
  FROM
    blacklist_natural_person_details bl_npd
  WHERE
    upper(trim(replace(format('%s %s %s', bl_npd.name, bl_npd.first_last_name, bl_npd.second_last_name),
      '  ', ' '))) = full_name
    OR bl_npd.curp = NEW.curp
    OR bl_npd.rfc = NEW.rfc;

  GET DIAGNOSTICS _row_count := ROW_COUNT;

  IF _row_count = 0 THEN
    INSERT INTO blacklist_search (person_id, blacklist_person_id, MATCH, match_score, search_date)
    SELECT
      NEW.person_id,
      bl_npd.id,
      TRUE,
      1.0 * (length(full_name) - levenshtein (upper(trim(replace(format('%s %s %s', bl_npd.name,
	bl_npd.first_last_name, bl_npd.second_last_name), '  ', ' '))), full_name)) /
	length(full_name),
      CURRENT_DATE
    FROM
      blacklist_natural_person_details bl_npd
    WHERE
      levenshtein (upper(trim(replace(format('%s %s %s', bl_npd.name, bl_npd.first_last_name,
	bl_npd.second_last_name), '  ', ' '))), full_name) < min_distance;
  END IF;

  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS natural_person_details_tgr ON natural_person_details;

CREATE TRIGGER natural_person_details_tgr
  AFTER INSERT ON natural_person_details
  FOR EACH ROW
  EXECUTE FUNCTION natural_person_details_tgr_fn ();

CREATE TABLE IF NOT EXISTS juridical_person_details (
  person_id INTEGER NOT NULL REFERENCES person (id) ON DELETE CASCADE,
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
  legal_name TEXT NOT NULL,
  incorporation_date DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (person_id)
);

DROP TRIGGER IF EXISTS prevent_juridical_person_updates ON juridical_person_details;

CREATE TRIGGER prevent_juridical_person_updates
  BEFORE UPDATE ON juridical_person_details
  FOR EACH ROW
  EXECUTE FUNCTION prevent_updates ();

CREATE INDEX IF NOT EXISTS idx_rfc_juridical_details ON juridical_person_details (rfc);
