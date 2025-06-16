#!/bin/bash
# A script to restore the Players table from a specific backup file.

# --- Configuration ---
DB_NAME="postgres"
DB_USER="postgres"
TABLE_NAME="players"

# Takes the backup file path as the first argument from the command line
BACKUP_FILE=$1

# Check if a backup file was provided
if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Error: Please provide the path to the backup file to restore."
    echo "Usage: ./restore_players.sh backups/players_backup_YYYYMMDD_HHMMSS.dump"
    exit 1
fi

echo "About to restore '${TABLE_NAME}' from file: ${BACKUP_FILE}"
echo "WARNING: This will DROP the existing '${TABLE_NAME}' table before restoring."
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo # Move to a new line

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Use pg_restore. --clean drops the table before recreating it from the backup.
    # It will prompt for your database password.
    pg_restore --username=$DB_USER --host=localhost --dbname=$DB_NAME --clean --if-exists --table=$TABLE_NAME "$BACKUP_FILE"

    echo "-------------------------------------"
    if [ $? -eq 0 ]; then
        echo "✅ Restore successful!"
    else
        echo "❌ Restore failed."
    fi
else
    echo "Restore cancelled by user."
fi