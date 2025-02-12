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


CREATE OR REPLACE FUNCTION fuzzy_match_score(token1 TEXT, token2 TEXT)
RETURNS DOUBLE PRECISION AS
$$
DECLARE
    lev_distance  INT;
    max_len       INT;
    lev_ratio     DOUBLE PRECISION;
    phonetic_score DOUBLE PRECISION;
BEGIN
    -- If the tokens match exactly, return 1.0.
    IF token1 = token2 THEN
       RETURN 1.0;
    END IF;

    -- Abbreviation rule:
    -- If one token is very short (length <= 2) and its first character
    -- equals the first character of the other token, return 0.95.
    IF (char_length(token1) <= 2 AND substring(token2,1,1) = substring(token1,1,1))
       OR (char_length(token2) <= 2 AND substring(token1,1,1) = substring(token2,1,1)) THEN
       RETURN 0.95;
    END IF;

    -- Phonetic check using dmetaphone (provided by fuzzystrmatch)
    IF dmetaphone(token1) = dmetaphone(token2) THEN
       phonetic_score := 0.95;
    ELSE
       phonetic_score := 0.0;
    END IF;

    -- Compute Levenshtein similarity ratio.
    max_len := GREATEST(char_length(token1), char_length(token2));
    IF max_len = 0 THEN
       lev_ratio := 1.0;
    ELSE
       lev_distance := levenshtein(token1, token2);
       lev_ratio := (max_len - lev_distance)::DOUBLE PRECISION / max_len;
    END IF;

    RETURN GREATEST(lev_ratio, phonetic_score);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION compute_match_score(
    query_given_names    TEXT,
    query_first_surname  TEXT,
    query_second_surname TEXT,
    blacklist_name       TEXT
) RETURNS INTEGER
AS
$$
DECLARE
    -- Normalized strings (using unaccent, lower, and removing punctuation)
    norm_query_given_names    TEXT := regexp_replace(unaccent(lower(query_given_names)), '[[:punct:]]', '', 'g');
    norm_query_first_surname  TEXT := regexp_replace(unaccent(lower(query_first_surname)), '[[:punct:]]', '', 'g');
    norm_query_second_surname TEXT := regexp_replace(unaccent(lower(query_second_surname)), '[[:punct:]]', '', 'g');
    norm_blacklist            TEXT := regexp_replace(unaccent(lower(blacklist_name)), '[[:punct:]]', '', 'g');

    -- Token arrays
    query_given_tokens TEXT[] := string_to_array(norm_query_given_names, ' ');
    query_surname_tokens TEXT[] := ARRAY[]::TEXT[];
    blacklist_tokens   TEXT[] := string_to_array(norm_blacklist, ' ');

    token_count        INT := COALESCE(array_length(blacklist_tokens,1), 0);
    used_indices       BOOLEAN[];  -- An array of booleans to mark which blacklist tokens have been "used"

    i INT;
    j INT;
    best_score DOUBLE PRECISION;
    best_index INT;
    current_score DOUBLE PRECISION;
    surname_scores DOUBLE PRECISION[] := '{}';
    surname_score DOUBLE PRECISION;

    -- Variables for given names matching:
    best_given_score DOUBLE PRECISION := 0;
    best_given_name_position INT := NULL;
    penalty DOUBLE PRECISION := 0;

    overall_score DOUBLE PRECISION;
    names_matched_count INT := 0;
BEGIN
    -- Build query surname tokens array (ignore empty strings)
    IF length(trim(norm_query_first_surname)) > 0 THEN
       query_surname_tokens := query_surname_tokens || norm_query_first_surname;
    END IF;
    IF length(trim(norm_query_second_surname)) > 0 THEN
       query_surname_tokens := query_surname_tokens || norm_query_second_surname;
    END IF;

    -- Initialize the used_indices array with FALSE for each blacklist token.
    IF token_count > 0 THEN
        used_indices := ARRAY(SELECT false FROM generate_series(1, token_count));
    ELSE
        used_indices := ARRAY[]::BOOLEAN[];
    END IF;

    -----------------------------
    -- STEP 1: Surname Matching
    -----------------------------
    -- For each query surname token, find the best matching blacklist token (not already used).
    FOR i IN 1 .. COALESCE(array_length(query_surname_tokens,1),0) LOOP
         best_score := 0;
         best_index := NULL;
         FOR j IN 1 .. token_count LOOP
             IF used_indices[j] = false THEN
                current_score := fuzzy_match_score(query_surname_tokens[i], blacklist_tokens[j]);
                IF current_score > best_score THEN
                   best_score := current_score;
                   best_index := j;
                END IF;
             END IF;
         END LOOP;
         surname_scores := surname_scores || best_score;
         IF best_index IS NOT NULL THEN
             used_indices[best_index] := true;
         END IF;
    END LOOP;

    -- Special rule: If there are two query surnames but fewer than two tokens matched,
    -- then we require that the first surname (paternal) is matched strongly.
    IF COALESCE(array_length(query_surname_tokens,1),0) = 2 THEN
         IF array_length(surname_scores,1) = 2 THEN
             IF surname_scores[1] >= 0.9 THEN
                surname_score := 1.0;
             ELSE
                surname_score := (surname_scores[1] + surname_scores[2]) / 2.0;
             END IF;
         ELSE
             surname_score := 0.0;
         END IF;
    ELSIF COALESCE(array_length(query_surname_tokens,1),0) > 0 THEN
         -- Otherwise, average the scores for the surnames.
         surname_score := 0;
         FOR i IN 1 .. array_length(surname_scores,1) LOOP
             surname_score := surname_score + surname_scores[i];
         END LOOP;
         surname_score := surname_score / array_length(surname_scores,1);
    ELSE
         surname_score := 1.0;
    END IF;

    -----------------------------
    -- STEP 2: Given Names Matching
    -----------------------------
    -- Use any remaining blacklist tokens (those not used for surname matching).
    FOR i IN 1 .. COALESCE(array_length(query_given_tokens,1),0) LOOP
         FOR j IN 1 .. token_count LOOP
             IF used_indices[j] = false THEN
                current_score := fuzzy_match_score(query_given_tokens[i], blacklist_tokens[j]);

                -- for short given names, we allow a lower score to match
                if current_score >= 0.75 and current_score < 0.9 and length(query_given_tokens[i]) < 5 then
                    current_score := 0.9;
                end if;

                if current_score >= 0.8 then
                    names_matched_count := names_matched_count + 1;
                end if;
                IF current_score > best_given_score THEN
                   best_given_score := current_score;
                   best_given_name_position := i;  -- save the position (1 = primary given name)
                END IF;
             END IF;
         END LOOP;
    END LOOP;

    -- If the best given–name match did not come from the first (primary) token, apply a penalty.
    IF best_given_name_position IS NOT NULL AND best_given_name_position > 1 THEN
         penalty := 0.1;
    ELSE
         penalty := 0;
    END IF;
    best_given_score := GREATEST(0, best_given_score - penalty);

    -- If not all given names matched, reduce the score.
    if names_matched_count < COALESCE(array_length(query_given_tokens,1),0) then
        best_given_score := best_given_score * 0.9;
    end if;

    -----------------------------
    -- STEP 3: Combine Scores
    -----------------------------
    -- We weight the given–name match as 70% and the surname match as 30%.
    overall_score := 0.5 * best_given_score + 0.5 * surname_score;

    -- Scale to a 0-100 range and round.
    RETURN round(overall_score * 100);
END;
$$ LANGUAGE plpgsql;


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
    person_full_name := unaccent(person_full_name);

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
    blacklist_full_name := unaccent(blacklist_full_name);

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
