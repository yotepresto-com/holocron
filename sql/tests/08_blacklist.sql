-- verifica que cuando se inserte un registro en blacklist_person_details se busque personas que hagan match
BEGIN;
DO $$
DECLARE
  _blacklist_person_id INTEGER;
  _blacklist_id INTEGER;
  _user_id INTEGER;
  _person_id INTEGER;
BEGIN
  SELECT
    id INTO _user_id
  FROM
    create_test_user ();
  -- mismo nombre y diferente RFC y CURP
  SELECT
    id INTO _person_id
  FROM
    create_test_person (_curp := 'VARD123456AAAAAA11', _rfc := 'AAAA123456AAB');
  SELECT
    id INTO _blacklist_id
  FROM
    create_test_blacklist ();
  SELECT
    id INTO _blacklist_person_id
  FROM
    create_test_blacklist_person (_blacklist_id);
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH
      AND match_score = 1) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por nombre';
END IF;
  -- mismo CURP y diferente nombre y RFC
  SELECT
    id INTO _blacklist_person_id
  FROM
    create_test_blacklist_person (_blacklist_id, _curp := 'VARD123456AAAAAA11', _rfc := 'AAAA123456AAC', _name := 'Otro');
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por CURP';
END IF;
  -- mismo RFC y diferente nombre y CURP
  SELECT
    id INTO _blacklist_person_id
  FROM
    create_test_blacklist_person (_blacklist_id, _curp := 'VARD123456AAAAAA24', _rfc := 'AAAA123456AAB', _name := 'Otro');
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por RFC';
END IF;
END;
$$;
ROLLBACK;

-- verifica que cuando se inserte un registro en natural_person_details se busquen coincidencias en listas negras
BEGIN;
DO $$
DECLARE
  _blacklist_person_id INTEGER;
  _blacklist_id INTEGER;
  _user_id INTEGER;
  _person_id INTEGER;
BEGIN
  SELECT
    id INTO _user_id
  FROM
    create_test_user ();
  SELECT
    id INTO _blacklist_id
  FROM
    create_test_blacklist ();
  -- mismo nombre y diferente rfc y curp
  SELECT
    id INTO _blacklist_person_id
  FROM
    create_test_blacklist_person (_blacklist_id, _curp := 'VARD123456AAAAAA11', _rfc := 'AAAA123456AAB');
  SELECT
    id INTO _person_id
  FROM
    create_test_person ();
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH
      AND match_score = 1) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por nombre';
END IF;
  -- mismo CURP y diferente nombre y RFC
  SELECT
    id INTO _person_id
  FROM
    create_test_person (_curp := 'VARD123456AAAAAA11', _rfc := 'AAAA123456AAC', _name := 'Otro');
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por CURP';
END IF;
  -- mismo RFC y diferente nombre y CURP
  SELECT
    id INTO _person_id
  FROM
    create_test_person (_curp := 'VARD123456AEEEEA11', _rfc := 'AAAA123456AAB', _name := 'Otro');
  IF NOT EXISTS (
    SELECT
      *
    FROM
      blacklist_search
    WHERE
      person_id = _person_id
      AND blacklist_person_id = _blacklist_person_id
      AND MATCH) THEN
  RAISE EXCEPTION 'Registro en blacklist_search no encontrado por RFC';
END IF;
END;
$$;
ROLLBACK;
