-- verifica que cuando se inserte un registro en config se actualize la tabla de auditoria
BEGIN;
DO $$
DECLARE
  _config_id INTEGER;
BEGIN
  SELECT
    id INTO _config_id
  FROM
    create_test_user ();
  INSERT INTO config (name, value)
    VALUES ('max_string_distance_to_match', '3')
  RETURNING
    id INTO _config_id;
  IF NOT EXISTS (
    SELECT
      *
    FROM
      audit_log
    WHERE
      table_name = 'config'
      AND record_id = _config_id
      AND operation_type = 'INSERT'
      AND changed_at = CURRENT_TIMESTAMP) THEN
  RAISE EXCEPTION 'Registro en audit_log no encontrado';
END IF;
  UPDATE
    config
  SET
    value = '4'
  WHERE
    id = _config_id;
  IF NOT EXISTS (
    SELECT
      *
    FROM
      audit_log
    WHERE
      table_name = 'config'
      AND record_id = _config_id
      AND operation_type = 'UPDATE'
      AND changed_at = CURRENT_TIMESTAMP
      AND changed_data ->> 'value' = '4') THEN
  RAISE EXCEPTION 'Registro en audit_log no encontrado';
END IF;
END;
$$;
ROLLBACK;
