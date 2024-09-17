#!/bin/bash

# set -ex

# -----------------------------------------
# Script: setup_database.sh
# Description: Executes SQL files in the 'sql' directory in order.
# Usage: ./setup_database.sh [--host HOST] [--port PORT] [--user USER] [--password PASSWORD] [--database DATABASE]
# Defaults:
#   host: (local socket connection)
#   port: 5432
#   user: postgres
#   password: ""
#   database: holocron
# -----------------------------------------

# Function to display usage instructions
usage() {
echo "Usage: $0 [--host HOST] [--port PORT] [--user USER] [--password PASSWORD] [--database DATABASE]"
  echo
  echo "Parameters:"
  echo "  --host       - Database host (default: local socket connection)"
  echo "  --port       - Database port (default: 5432)"
  echo "  --user       - Database user (default: postgres)"
  echo "  --password   - Database password (default: empty)"
  echo "  --database   - Database name (default: holocron)"
  echo
  echo "Example:"
  echo "  $0 --host localhost --port 5432 --user postgres --password mypassword --database mydatabase"
  exit 1
}

# --- Parameter Parsing ---

# Default values
HOST=""
PORT="5432"
USER="postgres"
PASSWORD=""
DATABASE="holocron"

# Function to parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --host)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    HOST="$2"
                    shift 2
                else
                    echo "Error: --host requires a value."
                    usage
                fi
                ;;
            --host=*)
                HOST="${1#*=}"
                shift 1
                ;;
            --port)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    PORT="$2"
                    shift 2
                else
                    echo "Error: --port requires a value."
                    usage
                fi
                ;;
            --port=*)
                PORT="${1#*=}"
                shift 1
                ;;
            --user)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    USER="$2"
                    shift 2
                else
                    echo "Error: --user requires a value."
                    usage
                fi
                ;;
            --user=*)
                USER="${1#*=}"
                shift 1
                ;;
            --password)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    PASSWORD="$2"
                    shift 2
                else
                    echo "Error: --password requires a value."
                    usage
                fi
                ;;
            --password=*)
                PASSWORD="${1#*=}"
                shift 1
                ;;
            --database)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    DATABASE="$2"
                    shift 2
                else
                    echo "Error: --database requires a value."
                    usage
                fi
                ;;
            --database=*)
                DATABASE="${1#*=}"
                shift 1
                ;;
            --help|-h)
                usage
                ;;
            *)
                echo "Error: Unknown option: $1"
                usage
                ;;
        esac
    done
}

# Parse the arguments
parse_args "$@"

# --- Set PGPASSWORD Environment Variable ---
export PGPASSWORD="$PASSWORD"

# --- Connection Check ---

echo "Attempting to connect to the database '$DATABASE'..."
PSQL_CMD=(psql -U "$USER" -d "$DATABASE" -c '\q' -q)

if [[ -n "$HOST" ]]; then
    PSQL_CMD+=(-h "$HOST")
fi

if [[ -n "$PORT" ]]; then
    PSQL_CMD+=(-p "$PORT")
fi

# Execute the connection command and capture any errors
if ! "${PSQL_CMD[@]}"; then
    echo "Error: Unable to connect to the database '$DATABASE' with the provided parameters."
    # Cleanup before exiting
    unset PGPASSWORD
    exit 1
else
    echo "Connection successful."
fi

# --- SQL File Execution ---

# Define the directory containing SQL files
SQL_DIR="sql"

# Check if the SQL directory exists
if [ ! -d "$SQL_DIR" ]; then
    echo "Error: SQL directory '$SQL_DIR' does not exist."
    # Cleanup before exiting
    unset PGPASSWORD
    exit 1
fi

# Find all .sql files in the directory, sorted alphabetically
SQL_FILES=$(find "$SQL_DIR" -type f -name "*.sql" | sort)

# Check if any SQL files are found
if [ -z "$SQL_FILES" ]; then
    echo "No SQL files found in '$SQL_DIR'. Nothing to execute."
    # Cleanup before exiting
    unset PGPASSWORD
    exit 0
fi

# Execute each SQL file
for sql_file in $SQL_FILES; do
    echo "Executing '$sql_file'..."
    EXEC_CMD=(psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DATABASE" -f "$sql_file" -q)

    if [[ -n "$HOST" ]]; then
        EXEC_CMD+=(-h "$HOST")
    fi

    if [[ -n "$PORT" ]]; then
        EXEC_CMD+=(-p "$PORT")
    fi

    # Execute the SQL file and capture any errors
    if ! "${EXEC_CMD[@]}"; then
        echo "Error: Failed to execute '$sql_file'. Aborting."
        # Cleanup before exiting
        unset PGPASSWORD
        exit 1
    else
        echo "Successfully executed '$sql_file'."
    fi
done

echo "All SQL scripts executed successfully."

# --- Cleanup ---

# Unset PGPASSWORD for security reasons
unset PGPASSWORD

exit 0
