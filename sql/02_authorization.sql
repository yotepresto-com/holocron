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

create or replace function check_permission()
returns trigger
as $$
declare
    _user_id integer;
    _permission_type permission_type;
begin
    _user_id := current_setting('app.current_user_id')::integer;
    _permission_type := TG_ARGV[0]::permission_type;

    -- TODO: check if the user is superuser
    if not has_permission(_user_id, _permission_type) then
        raise exception 'User % does not have permission %', _user_id, _permission_type;
    end if;

    if TG_OP = 'DELETE' then
        return old;
    else
        return new;
    end if;

end;
$$ language plpgsql;


create trigger check_permission_create_user
before insert on auth_user
for each row
when (new.is_superuser is false)
execute function check_permission('create_user');

create trigger check_permission_delete_user
before update on auth_user
for each row
when (new.is_active is false and old.is_active is true)
execute function check_permission('delete_user');

create trigger check_permission_update_user
before update on auth_user
for each row
execute function check_permission('update_user');

create trigger check_permission_create_group
before insert on auth_group
for each row
execute function check_permission('create_role');

create trigger check_permission_update_group
before update on auth_group
for each row
execute function check_permission('update_role');

create trigger check_permission_delete_group
before delete on auth_group
for each row
execute function check_permission('delete_role');

create trigger check_permission_create_role_permission
before insert on role_permission
for each row
execute function check_permission('assign_permission');

create trigger check_permission_delete_role_permission
before delete on role_permission
for each row
execute function check_permission('remove_permission');

create trigger check_permission_create_auth_user_groups
before insert on auth_user_groups
for each row
execute function check_permission('assign_role');

create trigger check_permission_delete_auth_user_groups
before delete on auth_user_groups
for each row
execute function check_permission('remove_role');

create trigger check_permission_create_product
before insert on product
for each row
execute function check_permission('create_product');

-- TODO: add the other permissions

-- -- Add Audit Triggers
-- SELECT add_audit_triggers(
--     ARRAY[
--         'system_user',
--         'role',
--         'role_permission',
--         'user_role'
--     ]
-- );
