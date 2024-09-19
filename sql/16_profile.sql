-- Person Profiles Definition
CREATE TABLE IF NOT EXISTS profile_type (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  accept_natural_person BOOLEAN DEFAULT FALSE,
  accept_legal_person BOOLEAN DEFAULT FALSE
);

-- Person Profiles Attributes
CREATE TABLE IF NOT EXISTS profile_attribute (
  id SERIAL PRIMARY KEY,
  profile_type_id INTEGER NOT NULL REFERENCES profile_type (id) ON DELETE CASCADE,
  attribute VARCHAR(255) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL CHECK (type IN ('number', 'boolean', 'categorical')),
  is_transactional BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_profile_attribute ON profile_attribute (profile_type_id);

CREATE TABLE IF NOT EXISTS profile_attribute_categorical_values (
  id SERIAL PRIMARY KEY,
  attribute_id INTEGER NOT NULL REFERENCES profile_attribute (id) ON DELETE CASCADE,
  accepted_value VARCHAR(255) NOT NULL,
  UNIQUE (attribute_id, accepted_value)
);

CREATE INDEX IF NOT EXISTS idx_profile_attrs_categorical_values ON profile_attribute_categorical_values (attribute_id);

-- Person Profile
CREATE TABLE IF NOT EXISTS profile (
  id SERIAL PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES person (id) ON DELETE CASCADE,
  profile_type_id INTEGER NOT NULL REFERENCES profile_type (id)
);

CREATE INDEX IF NOT EXISTS idx_person_profile ON profile (person_id);

-- Profile Data
CREATE TABLE IF NOT EXISTS profile_data (
  id SERIAL PRIMARY KEY,
  profile_id INTEGER NOT NULL REFERENCES profile (id) ON DELETE CASCADE,
  attribute_id INTEGER NOT NULL REFERENCES profile_attribute (id) ON DELETE CASCADE,
  value TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL
  -- TODO: check the consistency of the profile -> profily_type and attribute -> profile_type -> profile_type
);

CREATE INDEX IF NOT EXISTS idx_profile_data ON profile_data (profile_id, attribute_id);
