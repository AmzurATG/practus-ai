#!/bin/bash

# Practus AI Deployment Script
# Domain: practus-ai.amzur.com
# IP: 216.48.184.189

set -e  # Exit on error

echo "=========================================="
echo "Practus AI Production Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${NC}ℹ $1${NC}"
}

# Step 1: Stop any running processes on ports 8080 and 3030
echo "Step 1: Stopping existing processes..."
sudo lsof -ti :8080 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti :3030 | xargs sudo kill -9 2>/dev/null || true
sleep 2
print_success "Stopped existing processes"

# Step 2: Install Nginx if not installed
echo ""
echo "Step 2: Checking Nginx installation..."
if ! command -v nginx &> /dev/null; then
    print_warning "Nginx not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y nginx
    print_success "Nginx installed"
else
    print_success "Nginx is already installed"
fi

# Step 3: Install Certbot if not installed (for SSL)
echo ""
echo "Step 3: Checking Certbot installation..."
if ! command -v certbot &> /dev/null; then
    print_warning "Certbot not found. Installing..."
    sudo apt-get install -y certbot python3-certbot-nginx
    print_success "Certbot installed"
else
    print_success "Certbot is already installed"
fi

# Step 4: Copy systemd service files
echo ""
echo "Step 4: Installing systemd service files..."
sudo cp practus-backend.service /etc/systemd/system/
sudo cp practus-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
print_success "Service files installed"

# Step 5: Copy Nginx configuration
echo ""
echo "Step 5: Installing Nginx configuration..."
sudo cp nginx-practus-ai.conf /etc/nginx/sites-available/practus-ai
sudo ln -sf /etc/nginx/sites-available/practus-ai /etc/nginx/sites-enabled/practus-ai
print_success "Nginx configuration installed"

# Step 6: Test Nginx configuration
echo ""
echo "Step 6: Testing Nginx configuration..."
if sudo nginx -t; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Step 7: Enable and start services
echo ""
echo "Step 7: Enabling and starting services..."
sudo systemctl enable practus-backend
sudo systemctl enable practus-frontend
sudo systemctl restart practus-backend
sudo systemctl restart practus-frontend
sleep 5
print_success "Services enabled and started"

# Step 8: Restart Nginx
echo ""
echo "Step 8: Restarting Nginx..."
sudo systemctl restart nginx
print_success "Nginx restarted"

# Step 9: Check service status
echo ""
echo "Step 9: Checking service status..."
echo ""
echo "Backend Service Status:"
sudo systemctl status practus-backend --no-pager | head -n 10

echo ""
echo "Frontend Service Status:"
sudo systemctl status practus-frontend --no-pager | head -n 10

echo ""
echo "Nginx Status:"
sudo systemctl status nginx --no-pager | head -n 10

# Step 10: Verify ports are listening
echo ""
echo "Step 10: Verifying ports..."
if sudo lsof -i :8080 > /dev/null; then
    print_success "Backend is listening on port 8080"
else
    print_error "Backend is NOT listening on port 8080"
fi

if sudo lsof -i :3030 > /dev/null; then
    print_success "Frontend is listening on port 3030"
else
    print_error "Frontend is NOT listening on port 3030"
fi

if sudo lsof -i :80 > /dev/null; then
    print_success "Nginx is listening on port 80"
else
    print_error "Nginx is NOT listening on port 80"
fi

if sudo lsof -i :443 > /dev/null; then
    print_success "Nginx is listening on port 443"
else
    print_warning "Nginx is NOT listening on port 443 (SSL not configured yet)"
fi

# Step 11: Setup SSL (manual step)
echo ""
echo "=========================================="
echo "Step 11: SSL Certificate Setup"
echo "=========================================="
print_info "To enable HTTPS, run the following command:"
echo ""
echo "sudo certbot --nginx -d practus-ai.amzur.com"
echo ""
print_warning "Make sure your DNS is pointing to 216.48.184.189 before running certbot"

# Step 12: Summary
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
print_info "Services installed and running:"
echo "  - Backend: practus-backend.service (port 8080)"
echo "  - Frontend: practus-frontend.service (port 3030)"
echo "  - Nginx: nginx.service (ports 80, 443)"
echo ""
print_info "Access URLs:"
echo "  - HTTP:  http://practus-ai.amzur.com"
echo "  - HTTP:  http://216.48.184.189"
echo "  - HTTPS: https://practus-ai.amzur.com (after SSL setup)"
echo ""
print_info "Useful commands:"
echo "  - Check backend logs:   sudo journalctl -u practus-backend -f"
echo "  - Check frontend logs:  sudo journalctl -u practus-frontend -f"
echo "  - Check nginx logs:     sudo tail -f /var/log/nginx/practus-ai-*.log"
echo "  - Restart backend:      sudo systemctl restart practus-backend"
echo "  - Restart frontend:     sudo systemctl restart practus-frontend"
echo "  - Restart nginx:        sudo systemctl restart nginx"
echo ""
print_success "Deployment complete!"
