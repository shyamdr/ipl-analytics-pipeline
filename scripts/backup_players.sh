#!/bin/bash
# A script to back up the Players table to a custom-format archive.

# --- Configuration ---
DB_NAME="postgres"
DB_USER="postgres"
TABLE_NAME="players"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${TABLE_NAME}_backup_${TIMESTAMP}.dump"

# --- Logic ---
echo "Creating backup directory if it doesn't exist..."
mkdir -p $BACKUP_DIR

echo "Backing up the '${TABLE_NAME}' table from database '${DB_NAME}'..."

# Use pg_dump with custom format (-Fc) for a robust, compressed backup
# It will prompt for your database password.
pg_dump --username=$DB_USER --host=localhost --dbname=$DB_NAME --table=$TABLE_NAME --format=c --file=$BACKUP_FILE

echo "-------------------------------------"
if [ $? -eq 0 ]; then
    echo "✅ Backup successful!"
    echo "File created at: ${BACKUP_FILE}"
else
    echo "❌ Backup failed."
fi