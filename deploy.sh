#!/bin/bash
# Barekat Deployment Script
# Run on the server as root: bash deploy.sh

set -e

SERVER_IP="107.150.20.134"
REPO_URL="https://github.com/Hosseinasgari1/barekat.git"
PROJECT_DIR="/root/barekat"

echo "=========================================="
echo "  Barekat Deployment Script"
echo "  Server: $SERVER_IP"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Step 1: Install Docker and dependencies
echo ""
echo "[1/7] Installing Docker and dependencies..."
apt-get update -y
apt-get install -y docker.io docker-compose-v2 ufw git curl

systemctl enable docker
systemctl start docker

echo "Docker installed and started."

# Step 2: Configure firewall
echo ""
echo "[2/7] Configuring firewall..."
ufw --force reset
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 8000/tcp
ufw --force enable
echo "Firewall configured: ports 22, 80, 8000 open"

# Step 3: Clone or update repository
echo ""
echo "[3/7] Cloning repository..."
if [ -d "$PROJECT_DIR" ]; then
  echo "Directory exists, pulling latest..."
  cd $PROJECT_DIR
  git pull origin main
else
  git clone $REPO_URL $PROJECT_DIR
  cd $PROJECT_DIR
fi

echo "Repository ready at $PROJECT_DIR"

# Step 4: Set up environment file
echo ""
echo "[4/7] Setting up environment file..."
if [ -f ".env" ]; then
  echo ".env already exists, backing up..."
  cp .env .env.backup.$(date +%Y%m%d%H%M%S)
fi
cp .env.prod .env
echo "Environment file created from .env.prod"

# Step 5: Build and start containers
echo ""
echo "[5/7] Building and starting containers..."
docker compose -f docker-compose.prod.yml down || true
docker compose -f docker-compose.prod.yml up -d --build

echo "Containers started. Waiting for them to be ready..."
sleep 15

# Step 6: Run migrations and collect static
echo ""
echo "[6/7] Running migrations and collecting static files..."
docker exec barekat_backend python manage.py migrate --noinput
docker exec barekat_backend python manage.py collectstatic --noinput

echo "Migrations and static files done."

# Step 7: Show status
echo ""
echo "[7/7] Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "  Frontend:  http://$SERVER_IP"
echo "  Backend:   http://$SERVER_IP:8000/api/"
echo "  Admin:     http://$SERVER_IP:8000/admin/"
echo ""
echo "  To seed test data:"
echo "    docker exec barekat_backend python manage.py seed_data"
echo ""
echo "  To create a superuser:"
echo "    docker exec -it barekat_backend python manage.py createsuperuser"
echo ""
echo "  To view logs:"
echo "    docker compose -f docker-compose.prod.yml logs -f"
echo ""
