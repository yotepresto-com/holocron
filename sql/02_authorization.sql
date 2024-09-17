-- System Permission Enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'system_permission') THEN
        CREATE TYPE system_permission AS ENUM (
            'create_user',
            'read_user',
            'update_user',
            'delete_user',
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
            'delete_risk_matrix',
            'view_reports',
            'manage_blacklist',
            'manage_roles'
        );
    END IF;
END
$$;

-- System Users
CREATE TABLE IF NOT EXISTS system_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Role
CREATE TABLE IF NOT EXISTS role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Role Permission Assignment
CREATE TABLE IF NOT EXISTS role_permission (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    permission system_permission NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (role_id, permission)
);

-- Role Assignment
CREATE TABLE IF NOT EXISTS user_role (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES system_user(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permission_role ON role_permission(role_id);
CREATE INDEX IF NOT EXISTS idx_user_role_user ON user_role(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_role ON user_role(role_id);

-- Permission check
CREATE OR REPLACE FUNCTION has_permission(
    _user_id INTEGER,
    _permission system_permission
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM system_user su
        JOIN user_role ur ON su.id = ur.user_id
        JOIN role_permission rp ON ur.role_id = rp.role_id
        WHERE su.id = _user_id
          AND su.is_active = TRUE
          AND rp.permission = _permission
    );
END;
$$ LANGUAGE plpgsql;

-- -- Add Audit Triggers
-- SELECT add_audit_triggers(
--     ARRAY[
--         'system_user',
--         'role',
--         'role_permission',
--         'user_role'
--     ]
-- );
