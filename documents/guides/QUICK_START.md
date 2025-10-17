# 🚀 QUICK START - Run in 2 Minutes!

## Step 1: Start Backend (Terminal 1)

```bash
cd backend
python main.py
```

**Wait for:** `INFO: Uvicorn running on http://0.0.0.0:8000`

---

## Step 2: Start Frontend (Terminal 2 - NEW WINDOW)

```bash
cd frontend
npm run dev
```

**Wait for:** `Local: http://localhost:5173/`

---

## Step 3: Open Browser & Test

1. Go to: **http://localhost:5173**
2. Login: `admin` / `admin`
3. Click **"AI Chat"** in navigation
4. Try: **"Show me deals stuck in the pipeline"**

---

## ✅ Success = AI responds with analysis!

## ❌ Problems?

**Backend won't start:**
```bash
cd backend
del practus.db
python main.py
```

**Frontend errors:** Check `IMPLEMENTATION_STEPS.md` for full troubleshooting

---

**That's it!** You now have a working AI agent system.

See `IMPLEMENTATION_STEPS.md` for detailed testing guide.


