CREATE TABLE IF NOT EXISTS person (
    id SERIAL PRIMARY KEY,
    type person_type NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);

DROP TRIGGER IF EXISTS prevent_person_deletion ON person;
CREATE TRIGGER prevent_person_deletion
BEFORE DELETE ON person FOR EACH ROW EXECUTE PROCEDURE prevent_deletion();


CREATE TABLE IF NOT EXISTS natural_person_details (
    person_id INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    curp VARCHAR(18) CHECK (LENGTH(curp) = 18),
    rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
    name TEXT NOT NULL,
    first_last_name TEXT NOT NULL,
    second_last_name TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (person_id)
);

DROP TRIGGER IF EXISTS prevent_natural_person_updates ON natural_person_details;
CREATE TRIGGER prevent_natural_person_updates
BEFORE UPDATE ON natural_person_details
FOR EACH ROW EXECUTE FUNCTION prevent_updates();

CREATE INDEX IF NOT EXISTS idx_curp_natural_details ON natural_person_details (curp);
CREATE INDEX IF NOT EXISTS idx_rfc_natural_details ON natural_person_details (rfc);


CREATE TABLE IF NOT EXISTS juridical_person_details (
    person_id INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 12 AND 13),
    legal_name TEXT NOT NULL,
    incorporation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (person_id)
);

DROP TRIGGER IF EXISTS prevent_juridical_person_updates ON juridical_person_details;
CREATE TRIGGER prevent_juridical_person_updates
BEFORE UPDATE ON juridical_person_details
FOR EACH ROW EXECUTE FUNCTION prevent_updates();

CREATE INDEX IF NOT EXISTS idx_rfc_juridical_details ON juridical_person_details (rfc);
