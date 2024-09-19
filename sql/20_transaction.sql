CREATE TABLE IF NOT EXISTS transaction_type (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  product_type_id INTEGER REFERENCES product_type (id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transaction_type_product_type ON transaction_type (product_type_id);

CREATE INDEX IF NOT EXISTS idx_transaction_type_name ON transaction_type (name);

CREATE TABLE IF NOT EXISTS TRANSACTION (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES product (id),
  transaction_type_id INTEGER NOT NULL REFERENCES transaction_type (id),
  counterpart VARCHAR(255) NOT NULL,
  amount NUMERIC(10, 2) NOT NULL,
  effective_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
  -- TODO: check product_type match with transaction type.
);

CREATE INDEX IF NOT EXISTS idx_transaction_product ON TRANSACTION (product_id);

CREATE INDEX IF NOT EXISTS idx_transaction_type ON TRANSACTION (transaction_type_id);

CREATE INDEX IF NOT EXISTS idx_transaction_counterpart ON TRANSACTION (counterpart);

CREATE INDEX IF NOT EXISTS idx_transaction_effective_date ON TRANSACTION (effective_date);
