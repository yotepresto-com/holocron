CREATE TABLE IF NOT EXISTS product_type (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_type_name ON product_type (name);

CREATE TABLE IF NOT EXISTS product (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  person_id INTEGER REFERENCES person (id),
  product_type_id INTEGER NOT NULL REFERENCES product_type (id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_person ON product (person_id);

CREATE INDEX IF NOT EXISTS idx_product_product_type ON product (product_type_id);

CREATE TABLE IF NOT EXISTS product_attribute (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  data_type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_attribute_name ON product_attribute (name);

CREATE TABLE IF NOT EXISTS product_attribute_value (
  id SERIAL PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES product (id),
  attribute_id INTEGER NOT NULL REFERENCES product_attribute (id),
  value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_attribute_value_product ON product_attribute_value (product_id);

CREATE INDEX IF NOT EXISTS idx_product_attribute_value_attribute ON product_attribute_value (attribute_id);
