-- Person Type Enum
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT
      1
    FROM
      pg_type
    WHERE
      typname = 'person_type') THEN
  CREATE TYPE person_type AS ENUM (
    'natural',
    'juridical'
);
END IF;
END
$$;

-- Trigger to prevent updates
CREATE OR REPLACE FUNCTION prevent_updates ()
  RETURNS TRIGGER
  AS $$
BEGIN
  RAISE EXCEPTION 'Updates are not allowed on this table';
END;
$$
LANGUAGE plpgsql;

-- Trigger to prevent deletions
CREATE OR REPLACE FUNCTION prevent_deletion ()
  RETURNS TRIGGER
  AS $$
BEGIN
  RAISE EXCEPTION 'Delitions are not allowed on this table';
END;
$$
LANGUAGE plpgsql;

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
