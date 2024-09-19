
CREATE TABLE IF NOT EXISTS unusual_operations (
  id SERIAL PRIMARY KEY,
  operation_date DATE NOT NULL,
  customer_id INTEGER NOT NULL REFERENCES profile (id),
  amount DECIMAL(15, 2) NOT NULL,
  description TEXT,
  alert_level VARCHAR(20),
  reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relevant_operations (
  id SERIAL PRIMARY KEY,
  operation_date DATE NOT NULL,
  customer_id INTEGER NOT NULL REFERENCES profile (id),
  amount DECIMAL(15, 2) NOT NULL,
  operation_type VARCHAR(50),
  details TEXT,
  reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
