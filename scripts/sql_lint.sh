#!/bin/bash

SQL_DIRS=("sql" "sql/tests")
CONFIG_FILE="pg_format.conf"

for dir in "${SQL_DIRS[@]}"; do
    find "$dir" -type f -name "*.sql" | while read -r file; do
        echo "Formatting $file..."
        pg_format -c "$CONFIG_FILE" -i "$file"
    done
done

echo "Formatting complete."
