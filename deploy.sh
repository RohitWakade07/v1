#!/bin/bash
# Deploy script for EC2
# Run this from any machine that can SSH to the EC2 (not behind a proxy)
# Usage: bash deploy.sh

KEY_PATH="$HOME/Downloads/eep.pem"
EC2_HOST="ubuntu@51.20.55.161"

echo "==> Connecting to EC2 and deploying..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $EC2_HOST << 'REMOTE'
  set -e
  echo "==> Pulling latest code..."
  cd ~/grading-platform
  git pull origin v1-backend

  echo "==> Rebuilding and restarting backend..."
  cd ~/grading-platform/backend
  docker compose down
  
  echo "==> Cleaning up old Docker images and builder cache to free space..."
  docker system prune -a --volumes -f
  docker builder prune -a -f
  sudo apt-get clean || true
  
  docker compose build --no-cache
  docker compose up -d

  echo "==> Waiting for containers to be healthy..."
  sleep 10
  docker compose ps

  echo "==> Done! Deployment complete."
REMOTE

echo "==> Deploy finished."
