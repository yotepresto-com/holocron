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
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 9 AND 13),
  name TEXT,
  first_last_name TEXT,
  second_last_name TEXT,
  full_name TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  calculated_full_name TEXT generated always as (replace(upper(coalesce(full_name, name || ' ' || first_last_name || coalesce(' ' || second_last_name, ''))), '  ', ' ') ) stored,
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
  id SERIAL PRIMARY KEY,
  blacklist_person_id INTEGER NOT NULL REFERENCES blacklist_person (id) ON DELETE CASCADE,
  rfc VARCHAR(13) CHECK (LENGTH(rfc) BETWEEN 9 AND 13),
  legal_name TEXT NOT NULL,
  incorporation_date DATE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
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
BEGIN
    -- If the tokens match exactly, return 1.0.
    IF token1 = token2 THEN
       RETURN 1.0;
    END IF;

    -- Abbreviation rule: Jesús, José y María
    if token1 in ('MA', 'M') and token2 in ('MARIA', 'MARIO') then
        return 0.95;
    end if;

    if token2 in ('MA', 'M') and token1 in ('MARIA', 'MARIO') then
        return 0.95;
    end if;

    if token1 = 'J' and token2 in ('JESUS', 'JOSE') then
        return 0.95;
    end if;

    if token2 = 'J' and token1 in ('JESUS', 'JOSE') then
        return 0.95;
    end if;

    if token1 = 'JE' and token2 = 'JESUS' then
        return 0.95;
    end if;

    if token2 = 'JE' and token1 = 'JESUS' then
        return 0.95;
    end if;

    if token1 = 'JO' and token2 = 'JOSE' then
        return 0.95;
    end if;

    if token2 = 'JO' and token1 = 'JOSE' then
        return 0.95;
    end if;

    -- Compute Levenshtein similarity ratio.
    max_len := GREATEST(char_length(token1), char_length(token2));
    IF max_len = 0 THEN
       lev_ratio := 0;
    ELSE
       lev_distance := levenshtein(token1, token2);
       lev_ratio := (max_len - lev_distance)::DOUBLE PRECISION / max_len;
    END IF;

    RETURN lev_ratio;
END;
$$ LANGUAGE plpgsql;


create or replace function compute_match_score(
    first_name text,
    last_name text,
    second_last_name text,
    bl_full_name text
) returns float
as $$
declare
    i int;
    j int;
    match_names bool := false;
    match_name1 bool := false;
    match_name2 bool := false;
    match_last_names bool := false;
    match_last_name1 bool := false;
    match_last_name2 bool := false;
    bl_full_name_tokens text[];
    bl_mached_tokens bool[];
    first_name_tokens text[];
    match_first_name1_idx int;
    match_first_name2_idx int;
    match_last_name1_idx int;
    match_last_name2_idx int;
    distance2 int;
    distance int;
    distance_result float;
    full_name text;
    max_len int;
begin
    bl_full_name := regexp_replace(unaccent(upper(bl_full_name)), '[[:punct:]]', '', 'g');
    first_name := regexp_replace(unaccent(upper(first_name)), '[[:punct:]]', '', 'g');
    last_name := regexp_replace(unaccent(upper(last_name)), '[[:punct:]]', '', 'g');
    second_last_name := regexp_replace(unaccent(upper(second_last_name)), '[[:punct:]]', '', 'g');

    bl_full_name_tokens := string_to_array(bl_full_name, ' ');
    first_name_tokens := string_to_array(first_name, ' ');

    bl_mached_tokens :=  (select array_agg(f) from (select false as f from unnest(bl_full_name_tokens)));
    full_name := trim(first_name || ' ' || last_name || ' ' || coalesce(second_last_name, ''));

    if bl_full_name = full_name then
        return 1.0;
    end if;

    max_len := GREATEST(length(full_name), length(bl_full_name));

    IF max_len = 0 THEN
        RETURN 0.0;
    END IF;

    distance := levenshtein(full_name, bl_full_name);
    distance_result := (1.0 * (max_len - distance)) / max_len;

    -- TODO: cambiar el 0.9 por una configuración
    if distance_result >= 0.9 then
        return distance_result;
    end if;

    -- primero apellidos y luego nombres
    distance2 := levenshtein(trim(last_name || coalesce(' ' || second_last_name, '') || ' ' || first_name), bl_full_name);
    distance_result := greatest(distance_result, 1.0 * (max_len - distance2) / max_len);

    -- TODO: cambiar el 0.9 por una configuración
    if distance_result >= 0.9 then
        return distance_result;
    end if;

    -- first name
    for i in 1 .. coalesce(array_length(first_name_tokens, 1), 0) loop
        for j in 1 .. coalesce(array_length(bl_full_name_tokens, 1), 0) loop
            if bl_mached_tokens[j] then
                continue;
            end if;

            --if bl_full_name_tokens[j] = first_name_tokens[i] then
            if fuzzy_match_score(bl_full_name_tokens[j], first_name_tokens[i]) >= 0.9 then

                bl_mached_tokens[j] := true;
                if i = 1 then
                    match_first_name1_idx := j;
                    match_name1 := true;
                else
                    match_first_name2_idx := j;
                    match_name2 := true;
                end if;

                exit;
            end if;
        end loop;
    end loop;

    if array_length(first_name_tokens, 1) = 1 then
        match_names := match_name1;
    else
        match_names := match_name1 OR match_name2;
    end if;

    -- last name1
    for j in 1 .. coalesce(array_length(bl_full_name_tokens, 1), 0) loop
        if bl_mached_tokens[j] then
            continue;
        end if;

        --if bl_full_name_tokens[j] = last_name then
        if fuzzy_match_score(bl_full_name_tokens[j], last_name) >= 0.9 then
            match_last_name1 := true;
            bl_mached_tokens[j] := true;
            match_last_name1_idx := j;
            exit;
        end if;
    end loop;

    if match_names then
        -- coincide el primer nombre con el primero de la lista negra pero el segundo no y el apellido va después del nombre
        if match_first_name1_idx > 1 and bl_mached_tokens[match_first_name1_idx - 1] is false and match_last_name1 and match_last_name1_idx > match_first_name1_idx then
            match_names := false;
        end if;

        -- coincide el primer nombre con el primero de la lista negra pero el segundo no y el apellido va antes del nombre
        if match_last_name1 and match_last_name1_idx < match_first_name1_idx and match_name2 is false and array_length(bl_mached_tokens, 1) > match_first_name1_idx and bl_mached_tokens[match_first_name1_idx + 1] is false then
            match_names := false;
        end if;

        -- coincide el segundo nombre con el segundo de la lista negra pero el primero no
        if match_name2 and not match_name1 and match_first_name2_idx < match_last_name1_idx and match_first_name2_idx > 1 and bl_mached_tokens[match_first_name2_idx - 1] is false then
            match_names := false;
        end if;

        -- el segundo nombre coincide con el primero y hay un segundo nombre en la lista negra que no coincide
        if match_name1 is false and match_name2 and match_first_name2_idx = 1 and match_last_name1 and match_last_name1_idx > 2 then
            match_names := false;
        end if;
    end if;

    -- last name2
    if second_last_name = '' or second_last_name is null then
        match_last_name2 := true;
        match_last_name2_idx := match_last_name1_idx + 999; -- to make it bigger than the first last name index
    else
        for j in 1 .. coalesce(array_length(bl_full_name_tokens, 1), 0) loop
            if bl_mached_tokens[j] then
                continue;
            end if;

            --if bl_full_name_tokens[j] = second_last_name then
            if fuzzy_match_score(bl_full_name_tokens[j], second_last_name) >= 0.9 then
                match_last_name2 := true;
                bl_mached_tokens[j] := true;
                match_last_name2_idx := j;
                exit;
            end if;
        end loop;
    end if;

    if match_last_name1 and match_last_name2 and match_last_name2_idx > match_last_name1_idx then
        match_last_names := true;
    end if;

    /*
    raise notice 'match_names: %', match_names; --DELETE
    raise notice 'match_name1: %', match_name1; --DELETE
    raise notice 'match_name2: %', match_name2; --DELETE
    raise notice 'match_first_name1_idx: %', match_first_name1_idx; --DELETE
    raise notice 'match_first_name2_idx: %', match_first_name2_idx; --DELETE
    raise notice 'match_last_name1: %', match_last_name1; --DELETE
    raise notice 'match_last_name2: %', match_last_name2; --DELETE
    raise notice 'match_last_name1_idx: %', match_last_name1_idx; --DELETE
    raise notice 'match_last_name2_idx: %', match_last_name2_idx; --DELETE
    raise notice 'l: %', array_length(bl_full_name_tokens, 1); --DELETE
    */

    if match_names and match_last_names then
        if match_last_name1_idx < coalesce(match_first_name1_idx, match_first_name2_idx) and match_last_name1_idx > 1 then
            return distance_result;
        end if;

        -- tiene un apellido y hace match con el segundo apellido de la lista negra
        if (second_last_name = '' or second_last_name is null) and match_last_name1_idx = 4 then
            return distance_result;
        end if;

        if match_last_name1_idx - match_first_name1_idx > 1 then
            for i in match_first_name1_idx + 1 .. match_last_name1_idx - 1 loop
                if bl_mached_tokens[i] is false then
                    return distance_result;
                end if;
            end loop;
        end if;

        -- coincide el segundo nombre con el segundo de la lista negra pero el primero no y los apellidos van antes de los nombres
        if match_name2 and match_name1 is false and match_first_name2_idx - match_last_name2_idx > 1 then
            return distance_result;
        end if;

        -- el segundo nombre coincide con el primero y hay un segundo nombre en la lista negra que no coincide y los apellidos van antes de los nombres
        if match_name1 is false and match_name2 and match_last_name1_idx = 1 and match_first_name2_idx < array_length(bl_full_name_tokens, 1) then
            return distance_result;
        end if;

        return 0.9;
    else
        return distance_result;
    end if;
end;
$$ language plpgsql immutable parallel safe;


create or replace function blacklist_juridical_person_match_fn(
    legal_name TEXT,
    blacklist_legal_name TEXT
)
returns double precision
as $$
declare
    max_len int;
    distance int;
begin
    legal_name := regexp_replace(unaccent(upper(legal_name)), '[[:punct:]]', '', 'g');
    blacklist_legal_name := regexp_replace(unaccent(upper(blacklist_legal_name)), '[[:punct:]]', '', 'g');

    legal_name := replace(legal_name, ' SA DE CV', '');
    legal_name := replace(legal_name, ' SR DE RL', '');
    legal_name := replace(legal_name, ' RL DE CV', '');

    blacklist_legal_name := replace(blacklist_legal_name, ' SA DE CV', '');
    blacklist_legal_name := replace(blacklist_legal_name, ' SR DE RL', '');
    blacklist_legal_name := replace(blacklist_legal_name, ' RL DE CV', '');


    if legal_name = blacklist_legal_name then
        return 1.0;
    end if;

    max_len := GREATEST(length(legal_name), length(blacklist_legal_name));

    IF max_len = 0 THEN
        RETURN 0.0;
    END IF;

    distance := levenshtein(legal_name, blacklist_legal_name);
    return (1.0 * (max_len - distance)) / max_len;
end;
$$ language plpgsql immutable parallel safe;


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
      compute_match_score(npd.name, npd.first_last_name, npd.second_last_name, NEW.calculated_full_name),
      CURRENT_DATE
    FROM natural_person_details npd
        inner join person p on p.id = npd.person_id
    where p.deleted_at is null
    -- TODO: change the hardcoded 0.9 to a config
    -- and compute_match_score(npd.name, npd.first_last_name, npd.second_last_name, NEW.calculated_full_name) >= 0.9
    ;
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


CREATE OR REPLACE FUNCTION blacklist_juridical_person_details_tgr_fn ()
  RETURNS TRIGGER
  AS $$
DECLARE
  _row_count INTEGER;
  min_distance INTEGER;
BEGIN
    min_distance := (SELECT value::INTEGER FROM config WHERE name = 'max_string_distance_to_match');

    INSERT INTO blacklist_search (person_id, blacklist_person_id, MATCH, match_score, search_date)
    SELECT
      jpd.person_id,
      NEW.blacklist_person_id,
      TRUE,
      blacklist_juridical_person_match_fn(jpd.legal_name, NEW.legal_name),
      CURRENT_DATE
    FROM juridical_person_details jpd
        inner join person p on p.id = jpd.person_id
    where p.deleted_at is null
    -- TODO: change the hardcoded 0.9 to a config
    --    and blacklist_juridical_person_match_fn(jpd.legal_name, NEW.legal_name) >= 0.9
    ;

  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS blacklist_juridical_person_details_tgr ON blacklist_juridical_person_details;

CREATE TRIGGER blacklist_juridcal_person_details_tgr
  AFTER INSERT ON blacklist_juridical_person_details
  FOR EACH ROW
  EXECUTE FUNCTION blacklist_juridical_person_details_tgr_fn ();

-- Add Audit TRIGGERS
SELECT
  add_audit_triggers (ARRAY['blacklist', 'blacklist_person', 'blacklist_natural_person_details',
      'blacklist_juridical_person_details']);
