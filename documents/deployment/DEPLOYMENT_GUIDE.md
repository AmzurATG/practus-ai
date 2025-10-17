# Practus AI Production Deployment Guide

## Overview
This guide will help you deploy Practus AI to run as system services accessible via:
- **Domain**: https://practus-ai.amzur.com
- **IP Address**: http://216.48.184.189
- **Backend Port**: 8080 (proxied via Nginx)
- **Frontend Port**: 3030 (proxied via Nginx)

---

## Prerequisites

1. **Server**: Ubuntu/Debian Linux server with root access
2. **IP Address**: 216.48.184.189 (already mapped)
3. **DNS**: practus-ai.amzur.com pointing to 216.48.184.189
4. **Ports**: 80, 443, 8080, 3030 open in firewall
5. **Software**: Node.js, Python, Git already installed

---

## Quick Start (Automated Deployment)

### Option 1: Run the automated deployment script

```bash
cd /root/GIT_REPOSITORIES/Practus-ai/practus-ai
./deploy.sh
```

This script will:
1. ✓ Stop any existing processes
2. ✓ Install Nginx and Certbot
3. ✓ Install systemd service files
4. ✓ Configure Nginx reverse proxy
5. ✓ Start all services
6. ✓ Verify deployment

---

## Manual Deployment (Step-by-Step)

### Step 1: Stop Existing Processes

```bash
# Stop any processes on ports 8080 and 3030
sudo lsof -ti :8080 | xargs sudo kill -9
sudo lsof -ti :3030 | xargs sudo kill -9
```

### Step 2: Install Nginx

```bash
# Update package list
sudo apt-get update

# Install Nginx
sudo apt-get install -y nginx

# Check installation
nginx -v
```

### Step 3: Install Certbot (for SSL)

```bash
# Install Certbot for Let's Encrypt SSL
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 4: Install Backend Service

```bash
# Copy service file
sudo cp /root/GIT_REPOSITORIES/Practus-ai/practus-ai/practus-backend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable practus-backend

# Start the service
sudo systemctl start practus-backend

# Check status
sudo systemctl status practus-backend
```

### Step 5: Install Frontend Service

```bash
# Copy service file
sudo cp /root/GIT_REPOSITORIES/Practus-ai/practus-ai/practus-frontend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable practus-frontend

# Start the service
sudo systemctl start practus-frontend

# Check status
sudo systemctl status practus-frontend
```

### Step 6: Configure Nginx

```bash
# Copy Nginx configuration
sudo cp /root/GIT_REPOSITORIES/Practus-ai/practus-ai/nginx-practus-ai.conf /etc/nginx/sites-available/practus-ai

# Create symbolic link
sudo ln -sf /etc/nginx/sites-available/practus-ai /etc/nginx/sites-enabled/practus-ai

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: Configure Firewall (if UFW is enabled)

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Step 8: Setup SSL Certificate (HTTPS)

```bash
# Make sure DNS is pointing to your server first!
# Then run Certbot
sudo certbot --nginx -d practus-ai.amzur.com

# Follow the prompts:
# 1. Enter your email
# 2. Agree to terms
# 3. Choose to redirect HTTP to HTTPS (recommended)

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 9: Verify Deployment

```bash
# Check if services are running
sudo systemctl status practus-backend
sudo systemctl status practus-frontend
sudo systemctl status nginx

# Check ports
sudo lsof -i :8080  # Backend
sudo lsof -i :3030  # Frontend
sudo lsof -i :80    # Nginx HTTP
sudo lsof -i :443   # Nginx HTTPS

# Test from command line
curl http://localhost:8080/api/health
curl http://localhost:3030
curl http://216.48.184.189
```

---

## Access Your Application

### Via IP Address
- **HTTP**: http://216.48.184.189
- **API**: http://216.48.184.189/api/

### Via Domain (after SSL setup)
- **HTTPS**: https://practus-ai.amzur.com
- **API**: https://practus-ai.amzur.com/api/

---

## Service Management Commands

### Backend Service
```bash
# Start
sudo systemctl start practus-backend

# Stop
sudo systemctl stop practus-backend

# Restart
sudo systemctl restart practus-backend

# View logs
sudo journalctl -u practus-backend -f

# View last 100 lines
sudo journalctl -u practus-backend -n 100
```

### Frontend Service
```bash
# Start
sudo systemctl start practus-frontend

# Stop
sudo systemctl stop practus-frontend

# Restart
sudo systemctl restart practus-frontend

# View logs
sudo journalctl -u practus-frontend -f

# View last 100 lines
sudo journalctl -u practus-frontend -n 100
```

### Nginx
```bash
# Start
sudo systemctl start nginx

# Stop
sudo systemctl stop nginx

# Restart
sudo systemctl restart nginx

# Reload (without dropping connections)
sudo systemctl reload nginx

# Test configuration
sudo nginx -t

# View access logs
sudo tail -f /var/log/nginx/practus-ai-access.log

# View error logs
sudo tail -f /var/log/nginx/practus-ai-error.log
```

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check logs
sudo journalctl -u practus-backend -n 50
sudo journalctl -u practus-frontend -n 50

# Check if ports are already in use
sudo lsof -i :8080
sudo lsof -i :3030

# Kill processes manually if needed
sudo pkill -f "python main.py"
sudo pkill -f "npm run dev"
```

### Issue: Can't access via domain

```bash
# Check DNS resolution
nslookup practus-ai.amzur.com
dig practus-ai.amzur.com

# Check Nginx is listening
sudo lsof -i :80
sudo lsof -i :443

# Check Nginx configuration
sudo nginx -t

# Check firewall
sudo ufw status
```

### Issue: CORS errors

```bash
# The backend has been configured for:
# - https://practus-ai.amzur.com
# - http://practus-ai.amzur.com
# - https://216.48.184.189
# - http://216.48.184.189

# If you need to add more domains, edit:
nano /root/GIT_REPOSITORIES/Practus-ai/practus-ai/backend/main.py

# Then restart backend
sudo systemctl restart practus-backend
```

### Issue: SSL certificate issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Force renew
sudo certbot renew --force-renewal

# Check auto-renewal timer
sudo systemctl status certbot.timer
```

---

## Monitoring

### Real-time Logs

```bash
# Watch all logs together
sudo journalctl -u practus-backend -u practus-frontend -f

# Watch Nginx logs
sudo tail -f /var/log/nginx/practus-ai-access.log /var/log/nginx/practus-ai-error.log
```

### System Resources

```bash
# Check CPU and memory
htop

# Check disk space
df -h

# Check service status
systemctl status practus-* --no-pager
```

---

## Backup and Maintenance

### Backup Configuration Files

```bash
# Create backup directory
mkdir -p ~/practus-backups

# Backup service files
sudo cp /etc/systemd/system/practus-*.service ~/practus-backups/

# Backup Nginx configuration
sudo cp /etc/nginx/sites-available/practus-ai ~/practus-backups/

# Backup SSL certificates
sudo cp -r /etc/letsencrypt ~/practus-backups/letsencrypt-backup
```

### Update Application

```bash
# Pull latest changes
cd /root/GIT_REPOSITORIES/Practus-ai/practus-ai
git pull

# Install dependencies if needed
cd backend
pip install -r requirements.txt

cd ../frontend
npm install

# Restart services
sudo systemctl restart practus-backend
sudo systemctl restart practus-frontend
```

---

## Security Recommendations

1. **Firewall**: Only allow ports 80, 443, and SSH
2. **SSL**: Always use HTTPS in production
3. **Updates**: Keep system and packages updated
4. **Backups**: Regular backups of database and configurations
5. **Monitoring**: Set up monitoring and alerting
6. **Logs**: Regularly review logs for suspicious activity

---

## Architecture Overview

```
Internet
    ↓
Nginx (Port 80/443)
    ├─→ Frontend (Port 3030) → React/Vite App
    └─→ Backend API (Port 8080) → FastAPI Python App
            ↓
        SQLite Database
```

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u practus-backend -u practus-frontend -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/practus-ai-error.log`
3. Verify DNS: `nslookup practus-ai.amzur.com`
4. Check services: `sudo systemctl status practus-*`

---

## Quick Reference

| Component | Port | Service Name | Config Location |
|-----------|------|--------------|-----------------|
| Backend | 8080 | practus-backend | /etc/systemd/system/practus-backend.service |
| Frontend | 3030 | practus-frontend | /etc/systemd/system/practus-frontend.service |
| Nginx | 80, 443 | nginx | /etc/nginx/sites-available/practus-ai |
| SSL Certs | - | certbot | /etc/letsencrypt/ |

---

**Deployment Date**: October 16, 2025  
**Version**: 1.0.0  
**Maintainer**: Amzur Technologies
