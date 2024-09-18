-- Create the operation_type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'operation_type_enum') THEN
        CREATE TYPE operation_type_enum AS ENUM ('INSERT', 'UPDATE', 'DELETE');
    END IF;
END
$$;

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation_type operation_type_enum NOT NULL,
    record_id INTEGER NOT NULL,
    changed_data JSONB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE SET NULL
);

-- Indexes to improve query performance on audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation_type ON audit_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_record_id ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at);

-- Trigger Function for Auditing INSERT operations and setting timestamps
CREATE OR REPLACE FUNCTION audit_insert() RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at := COALESCE(NEW.created_at, CURRENT_TIMESTAMP);

    -- verifica que la tabla tenga la columna updated_at
    if (to_jsonb(NEW)) ? 'updated_at' then
        NEW.updated_at := CURRENT_TIMESTAMP;
    end if;

    -- Insert audit log
    INSERT INTO audit_log (
        table_name, 
        operation_type, 
        record_id, 
        changed_data, 
        changed_by
    ) VALUES (
        TG_TABLE_NAME, 
        'INSERT', 
        NEW.id, 
        to_jsonb(NEW), 
        current_setting('app.current_user_id')::INTEGER
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger Function for Auditing UPDATE operations and setting timestamps
CREATE OR REPLACE FUNCTION audit_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;

    -- Insert audit log
    INSERT INTO audit_log (
        table_name, 
        operation_type, 
        record_id, 
        changed_data, 
        changed_by
    ) VALUES (
        TG_TABLE_NAME, 
        'UPDATE', 
        NEW.id, 
        to_jsonb(NEW), 
        current_setting('app.current_user_id')::INTEGER
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger Function for Auditing DELETE operations
CREATE OR REPLACE FUNCTION audit_delete() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name, 
        operation_type, 
        record_id, 
        changed_data, 
        changed_by
    ) VALUES (
        TG_TABLE_NAME, 
        'DELETE', 
        OLD.id, 
        to_jsonb(OLD), 
        current_setting('app.current_user_id')::INTEGER
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Function to Set Current User ID for Audit Logging
-- This should be called at the beginning of each session or transaction
CREATE OR REPLACE FUNCTION set_current_user_id(_user_id INTEGER) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', _user_id::TEXT, true);
END;
$$ LANGUAGE plpgsql;


-- Create or replace the add_audit_triggers function
CREATE OR REPLACE FUNCTION add_audit_triggers(tables TEXT[])
RETURNS VOID AS $$
DECLARE
    tbl TEXT;
    trigger_name TEXT;
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        -- ***** INSERT Trigger *****
        trigger_name := 'audit_insert_' || tbl;
        
        -- Check if the INSERT trigger already exists
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger
            WHERE tgname = trigger_name
              AND tgrelid = tbl::regclass
        ) THEN
            -- Create the INSERT trigger
            EXECUTE format('
                CREATE TRIGGER %I
                AFTER INSERT ON %I
                FOR EACH ROW
                EXECUTE FUNCTION audit_insert();
            ', trigger_name, tbl);
        END IF;

        -- ***** UPDATE Trigger *****
        trigger_name := 'audit_update_' || tbl;
        
        -- Check if the UPDATE trigger already exists
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger
            WHERE tgname = trigger_name
              AND tgrelid = tbl::regclass
        ) THEN
            -- Create the UPDATE trigger
            EXECUTE format('
                CREATE TRIGGER %I
                AFTER UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION audit_update();
            ', trigger_name, tbl);
        END IF;

        -- ***** DELETE Trigger *****
        trigger_name := 'audit_delete_' || tbl;
        
        -- Check if the DELETE trigger already exists
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger
            WHERE tgname = trigger_name
              AND tgrelid = tbl::regclass
        ) THEN
            -- Create the DELETE trigger
            EXECUTE format('
                CREATE TRIGGER %I
                AFTER DELETE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION audit_delete();
            ', trigger_name, tbl);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
