DO $$
BEGIN
  IF NOT EXISTS (
    SELECT
      1
    FROM
      pg_type
    WHERE
      typname = 'risk_matrix_status') THEN
  CREATE TYPE risk_matrix_status AS ENUM (
    'development',
    'active',
    'historical'
);
END IF;
END
$$;

-- Tabla para almacenar las matrices de riesgo
CREATE TABLE IF NOT EXISTS risk_matrix (
  id SERIAL PRIMARY KEY,
  profile_type_id INTEGER NOT NULL REFERENCES profile_type (id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  status risk_matrix_status NOT NULL DEFAULT 'development',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para almacenar los valores de riesgo y pesos para cada atributo en una matriz
CREATE TABLE IF NOT EXISTS risk_attribute_value (
  id SERIAL PRIMARY KEY,
  risk_matrix_id INTEGER NOT NULL REFERENCES risk_matrix (id) ON DELETE CASCADE,
  attribute_id INTEGER NOT NULL REFERENCES profile_attribute (id) ON DELETE CASCADE,
  risk_value TEXT NULL,
  weight NUMERIC(5, 2) NOT NULL,
  CONSTRAINT unique_risk_attribute_matrix UNIQUE (risk_matrix_id, attribute_id)
);

CREATE TABLE IF NOT EXISTS risk_attribute_categorical_value (
  id SERIAL PRIMARY KEY,
  profile_attr_categorical_value INTEGER NOT NULL REFERENCES profile_attribute_categorical_values (id) ON DELETE CASCADE,
  risk_value NUMERIC(5, 2) NOT NULL,
  UNIQUE (profile_attr_categorical_value)
);

CREATE TABLE IF NOT EXISTS risk_level (
  id SERIAL PRIMARY KEY,
  level VARCHAR(50) NOT NULL,
  score_cut NUMERIC(5, 2) NOT NULL,
  is_lowest_level BOOLEAN NOT NULL DEFAULT FALSE,
  is_highest_level BOOLEAN NOT NULL DEFAULT FALSE
  -- TODO: constraint unique_lowest_level and unique highest level
);

CREATE TABLE IF NOT EXISTS risk (
  id SERIAL PRIMARY KEY,
  profile_id INTEGER NOT NULL REFERENCES profile (id) ON DELETE CASCADE,
  risk_matrix_id INTEGER NOT NULL REFERENCES risk_matrix (id) ON DELETE CASCADE,
  evaluation_date DATE NOT NULL,
  score NUMERIC(5, 2) NOT NULL,
  risk_level_id INTEGER NOT NULL REFERENCES risk_level (id),
  CONSTRAINT check_score_range CHECK (score >= 0 AND score <= 100)
  -- TODO: constraint check_profile_type_match
);

CREATE INDEX IF NOT EXISTS idx_risk ON risk (profile_id, evaluation_date);
