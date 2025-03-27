
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


SELECT add_audit_triggers (ARRAY['pep_list', 'pep_person']);
