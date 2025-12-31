#!/usr/bin/env bash
set -euo pipefail

# Change to repository root
cd "$(dirname "$0")"

# Stop running containers
if docker compose ps --status running | grep -q .; then
  echo "Stopping running containers..."
  docker compose down
else
  echo "No running containers to stop; ensuring stack is down."
  docker compose down || true
fi

# Remove the database volume
volume_name="${COMPOSE_PROJECT_NAME:-tarobot}_pgdata"
if docker volume inspect "$volume_name" >/dev/null 2>&1; then
  echo "Removing database volume: $volume_name"
  docker volume rm "$volume_name"
else
  echo "Database volume $volume_name not found; skipping removal."
fi

# Update repository
echo "Pulling latest changes..."
git pull --rebase

# Build updated containers
echo "Building containers..."
docker compose build --pull

# Start stack
echo "Starting docker compose stack..."
docker compose up -d

echo "Update complete."
