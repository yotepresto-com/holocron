-- System Permission Enum
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT
      1
    FROM
      pg_type
    WHERE
      typname = 'permission_type') THEN
  CREATE TYPE permission_type AS ENUM (
    'create_user',
    'read_user',
    'update_user',
    'delete_user',
    'create_role',
    'read_role',
    'update_role',
    'delete_role',
    'read_permission',
    'assign_permission',
    'remove_permission',
    'assign_role',
    'remove_role',
    'create_profile',
    'read_profile',
    'update_profile',
    'delete_profile',
    'create_product',
    'read_product',
    'update_product',
    'delete_product',
    'create_risk_matrix',
    'read_risk_matrix',
    'update_risk_matrix',
    'delete_risk_matrix'
);
END IF;
END
$$;


-- Role Permission Assignment
CREATE TABLE IF NOT EXISTS role_permission (
  id SERIAL PRIMARY KEY,
  role_id INTEGER NOT NULL REFERENCES auth_group (id) ON DELETE CASCADE,
  permission permission_type NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  UNIQUE (role_id, permission)
);

CREATE INDEX IF NOT EXISTS idx_role_permission_role ON role_permission (role_id);

-- Permission check
CREATE OR REPLACE FUNCTION has_permission (_user_id INTEGER, _permission permission_type)
  RETURNS BOOLEAN
  AS $$
BEGIN
  RETURN EXISTS (
    SELECT
      1
    FROM
      auth_user u
      JOIN auth_user_groups ur ON u.id = ur.user_id
      JOIN role_permission rp ON ur.group_id = rp.role_id
    WHERE
      u.id = _user_id
      AND u.is_active = TRUE
      AND rp.permission = _permission);
END;
$$
LANGUAGE plpgsql;

-- -- Add Audit Triggers
-- SELECT add_audit_triggers(
--     ARRAY[
--         'system_user',
--         'role',
--         'role_permission',
--         'user_role'
--     ]
-- );
