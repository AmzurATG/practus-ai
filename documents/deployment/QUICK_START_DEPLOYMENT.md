# Practus AI Deployment - Quick Start

## 🎯 What You Need to Know

**Your Configuration:**
- Domain: `practus-ai.amzur.com`
- IP Address: `216.48.184.189`
- Backend runs on: `8080` (internal)
- Frontend runs on: `3030` (internal)
- Public access via: `80` (HTTP) and `443` (HTTPS)

---

## 🚀 Quick Deployment (3 Steps)

### Step 1: Run the Automated Deployment Script

```bash
cd /root/GIT_REPOSITORIES/Practus-ai/practus-ai
./deploy.sh
```

This will automatically:
- Install required packages (Nginx, Certbot)
- Create system services
- Configure Nginx reverse proxy
- Start all services

### Step 2: Setup SSL Certificate

**IMPORTANT**: Make sure your DNS record `practus-ai.amzur.com` is pointing to `216.48.184.189` first!

```bash
sudo certbot --nginx -d practus-ai.amzur.com
```

Follow the prompts:
1. Enter your email address
2. Agree to terms of service
3. Choose "2" to redirect HTTP to HTTPS

### Step 3: Access Your Application

After SSL setup:
- **Domain**: https://practus-ai.amzur.com
- **IP**: http://216.48.184.189

---

## 📋 Manual Commands (If Needed)

### Deploy Services Manually

```bash
# 1. Copy service files
sudo cp practus-backend.service /etc/systemd/system/
sudo cp practus-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Copy Nginx config
sudo cp nginx-practus-ai.conf /etc/nginx/sites-available/practus-ai
sudo ln -sf /etc/nginx/sites-available/practus-ai /etc/nginx/sites-enabled/

# 3. Test Nginx config
sudo nginx -t

# 4. Start services
sudo systemctl enable --now practus-backend
sudo systemctl enable --now practus-frontend
sudo systemctl restart nginx
```

### Verify Everything is Running

```bash
# Check services
sudo systemctl status practus-backend
sudo systemctl status practus-frontend
sudo systemctl status nginx

# Check ports
sudo lsof -i :8080  # Backend
sudo lsof -i :3030  # Frontend
sudo lsof -i :80    # Nginx
sudo lsof -i :443   # Nginx HTTPS
```

---

## 🔧 Common Commands

### Service Management

```bash
# Backend
sudo systemctl restart practus-backend
sudo journalctl -u practus-backend -f

# Frontend
sudo systemctl restart practus-frontend
sudo journalctl -u practus-frontend -f

# Nginx
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/practus-ai-error.log
```

### Quick Troubleshooting

```bash
# If services won't start, check logs
sudo journalctl -u practus-backend -n 100
sudo journalctl -u practus-frontend -n 100

# If ports are blocked
sudo lsof -ti :8080 | xargs sudo kill -9
sudo lsof -ti :3030 | xargs sudo kill -9

# If DNS issues
nslookup practus-ai.amzur.com
curl -I http://216.48.184.189
```

---

## 📁 Files Created

All configuration files are in: `/root/GIT_REPOSITORIES/Practus-ai/practus-ai/`

- `deploy.sh` - Automated deployment script
- `practus-backend.service` - Backend systemd service
- `practus-frontend.service` - Frontend systemd service
- `nginx-practus-ai.conf` - Nginx reverse proxy config
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide

---

## ⚠️ Important Notes

1. **DNS First**: Make sure DNS is pointing to your IP before running Certbot
2. **Firewall**: Ensure ports 80 and 443 are open
3. **CORS Updated**: Backend already configured for your domain and IP
4. **Auto-Start**: Services will automatically start on server reboot
5. **SSL Renewal**: Certbot will auto-renew your SSL certificate

---

## 🆘 Need Help?

**Check Logs:**
```bash
# All services
sudo journalctl -u practus-backend -u practus-frontend -f

# Nginx
sudo tail -f /var/log/nginx/practus-ai-error.log
```

**Restart Everything:**
```bash
sudo systemctl restart practus-backend practus-frontend nginx
```

**Check Status:**
```bash
sudo systemctl status practus-*
```

---

## 🎉 Success Checklist

- [ ] Run `./deploy.sh` successfully
- [ ] Backend service running (`sudo systemctl status practus-backend`)
- [ ] Frontend service running (`sudo systemctl status practus-frontend`)
- [ ] Nginx running (`sudo systemctl status nginx`)
- [ ] DNS pointing to 216.48.184.189
- [ ] SSL certificate installed (`sudo certbot --nginx -d practus-ai.amzur.com`)
- [ ] Application accessible at https://practus-ai.amzur.com

---

**Ready to deploy? Run:** `./deploy.sh`
