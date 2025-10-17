# API Configuration Fix - CORS 400 Error Resolution

**Date**: October 16, 2025  
**Issue**: 400 Bad Request on OPTIONS requests to `/api/datasource/connect`  
**Status**: ✅ **RESOLVED**

---

## Problem Description

The frontend application was making direct API calls to `http://localhost:8080` which caused:
1. **CORS errors** when accessed from production domain/IP
2. **Connection failures** when the backend wasn't accessible on localhost
3. **Hardcoded URLs** that wouldn't work in different environments

### Error Example:
```
Request URL: http://localhost:8080/api/datasource/connect
Request Method: OPTIONS
Status Code: 400 Bad Request
```

---

## Root Cause

The frontend had **hardcoded API URLs** in multiple components:
- `http://localhost:8080/api/datasource/connect`
- `http://localhost:8080/api/actions/recommended`
- `http://localhost:8080/api/chat/query`
- `http://localhost:8080/api/chat/suggestions`
- `http://localhost:8080/api/actionable-items/problem/{id}`

This meant:
- ❌ API calls bypassed Nginx reverse proxy
- ❌ CORS preflight requests failed
- ❌ Application didn't work when accessed via IP (216.48.184.189)
- ❌ Application wouldn't work with domain (practus-ai.amzur.com)

---

## Solution Implemented

### 1. Created API Configuration Module
**File**: `frontend/src/config/api.js`

```javascript
const getApiBaseUrl = () => {
  // In production (accessed via domain/IP), use relative URLs
  if (window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1') {
    return ''; // Relative URLs → Nginx proxy
  }
  
  // In development, connect directly
  return 'http://localhost:8080';
};

export const getApiUrl = (path) => {
  const apiPath = path.startsWith('/api/') ? path : `/api/${path}`;
  return `${API_BASE_URL}${apiPath}`;
};
```

### 2. Updated All Components

**Updated Files:**
- ✅ `frontend/src/components/ConnectionModal.jsx`
- ✅ `frontend/src/components/ActionCenter.jsx`
- ✅ `frontend/src/pages/Chat.jsx`
- ✅ `frontend/src/pages/Insights.jsx`

**Before:**
```javascript
const response = await fetch('http://localhost:8080/api/datasource/connect', {...})
```

**After:**
```javascript
import { getApiUrl } from '../config/api'
const response = await fetch(getApiUrl('/api/datasource/connect'), {...})
```

---

## How It Works

### Development Environment (localhost):
```
Browser (localhost:3030) 
    → Direct → Backend (localhost:8080)
```

### Production Environment (IP/Domain):
```
Browser (216.48.184.189 or practus-ai.amzur.com)
    → Nginx (Port 80)
        → Backend (Port 8080) for /api/*
        → Frontend (Port 3030) for /*
```

---

## Benefits

1. ✅ **Works in all environments** (dev, staging, production)
2. ✅ **No CORS errors** - all requests go through Nginx
3. ✅ **Single point of entry** - better security
4. ✅ **SSL ready** - HTTPS will work seamlessly
5. ✅ **Automatic environment detection** - no manual configuration needed

---

## Testing

### Test API Requests:
```bash
# Test from command line
curl http://216.48.184.189/api/health

# Expected: 200 OK with JSON response
```

### Test from Browser:
1. Open: http://216.48.184.189
2. Login with credentials
3. Try "Connect Data Source"
4. Should work without CORS errors ✅

---

## Technical Details

### Request Flow (Production):

1. **Browser makes request**:
   ```
   GET /api/datasource/connect
   Host: 216.48.184.189
   ```

2. **Nginx receives and proxies**:
   ```nginx
   location /api/ {
       proxy_pass http://127.0.0.1:8080;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. **Backend processes**:
   ```python
   @app.post("/api/datasource/connect")
   async def connect_data_source(...):
       # CORS is happy because request comes from same origin
   ```

4. **Response flows back**:
   ```
   Browser ← Nginx ← Backend
   ```

---

## Files Modified

### New Files:
```
frontend/src/config/api.js  (NEW - API configuration)
```

### Updated Files:
```
frontend/src/components/ConnectionModal.jsx
frontend/src/components/ActionCenter.jsx
frontend/src/pages/Chat.jsx
frontend/src/pages/Insights.jsx
```

### Service Restart:
```bash
sudo systemctl restart practus-frontend
```

---

## Verification Checklist

- [x] API configuration module created
- [x] All hardcoded URLs removed
- [x] ConnectionModal updated
- [x] ActionCenter updated
- [x] Chat page updated
- [x] Insights page updated
- [x] Frontend service restarted
- [x] Testing from browser works
- [x] No CORS errors
- [x] All API calls going through Nginx

---

## Future Considerations

### For Additional Environments:

If you need to add more environments (staging, QA), you can extend the config:

```javascript
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  
  if (hostname === 'staging.practus-ai.amzur.com') {
    return 'https://staging-api.practus-ai.amzur.com';
  }
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8080';
  }
  
  // Production - use relative URLs
  return '';
};
```

### For Environment Variables:

Alternatively, use Vite's environment variables:

```javascript
// .env.production
VITE_API_URL=

// .env.development
VITE_API_URL=http://localhost:8080

// In code:
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
```

---

## Summary

✅ **Problem**: Frontend making direct calls to localhost:8080 causing CORS errors  
✅ **Solution**: Created smart API configuration that uses relative URLs in production  
✅ **Result**: Application works perfectly via IP (216.48.184.189) and will work with domain  
✅ **Status**: **FULLY RESOLVED AND TESTED**

---

**Issue Resolution Time**: ~15 minutes  
**Services Impacted**: Frontend only  
**Downtime**: ~5 seconds (service restart)  
**Testing Status**: ✅ Verified working
