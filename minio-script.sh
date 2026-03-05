#!/bin/sh
set -e
echo "Waiting for MinIO to be ready..."
while ! mc ready local; do 
  sleep 1
done

echo "Checking 'medforce' bucket..."
if ! mc ls local/medforce >/dev/null 2>&1; then
  echo "Creating 'medforce' bucket..."
  mc mb local/medforce
fi

echo "Setting public access for 'medforce' bucket..."
mc anonymous set public local/medforce/

echo "Initialization completed successfully"