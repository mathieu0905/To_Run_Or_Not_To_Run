#!/bin/bash

# Backup script: Backup output directory to backup directory

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/output"
BACKUP_DIR="$SCRIPT_DIR/backup"

# Check if output directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: output directory does not exist"
    exit 1
fi

# Create timestamped backup directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="$BACKUP_DIR/output_$TIMESTAMP"

mkdir -p "$TARGET_DIR"
cp -r "$SOURCE_DIR"/* "$TARGET_DIR"/

echo "Backup complete: $TARGET_DIR"
