# Practus AI Business Intelligence Platform

AI-powered business intelligence solution addressing 6 critical business challenges through predictive analytics and machine learning.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key

### Backend Setup

1. Navigate to backend:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update `.env` with your Gemini API key:
```
GEMINI_API_KEY=your-actual-api-key-here
```

4. Run the server:
```bash
python main.py
```

Backend runs on http://localhost:8000

### Frontend Setup

1. Navigate to frontend:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend runs on http://localhost:3000

## 🔐 Login Credentials
- Username: `admin`
- Password: `admin`

## 📊 Features

### 1. Data Source Management
- Upload 5 CSV files (Deals Archive, Stage History, Whizible, Plotting Tool, Skill Mapping)
- Real-time validation and data quality checks
- AI-powered field mapping suggestions

### 2. Interactive Visualizations
- Sales funnel analysis with Plotly
- Deal stage distribution charts
- AI-generated insights for each visualization
- Cross-filtering and drill-down capabilities

### 3. Dev Mode
- AI-recommended ML models for each problem
- Model comparison and selection
- Parameter tuning interface
- Explainable AI recommendations

### 4. Insights Dashboard
- Solutions for all 6 business problems:
  1. Revenue Forecasting
  2. Deal Drop-off Analysis
  3. Effort vs Budget Tracking
  4. Client Retention Insights
  5. Hiring & Cost Forecasting
  6. Automation Opportunities
- Prioritized action items with impact quantification
- 30/60/90 day action plans

## 🏗️ Tech Stack

- **Frontend**: React 18 + Tailwind CSS + Plotly.js
- **Backend**: FastAPI + SQLite
- **AI**: Google Gemini API
- **ML**: Scikit-learn, Prophet, XGBoost

## 📁 Project Structure

```
practus/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   ├── .env             # Environment variables
│   └── uploads/         # Uploaded CSV files
├── frontend/
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   └── App.jsx      # Main app component
│   └── package.json     # Node dependencies
├── PRD.md              # Product Requirements Document
└── README.md           # This file
```

## 🎯 Usage Workflow

1. **Login** with admin/admin
2. **Upload** your 5 CSV files on the Data Source page
3. **Explore** visualizations and AI insights
4. **Configure** ML models in Dev Mode (AI auto-selects optimal models)
5. **Review** actionable insights and 30/60/90 day plans

## 🔧 API Endpoints

- `POST /api/auth/login` - User authentication
- `POST /api/datasource/upload` - Upload CSV files
- `GET /api/datasource/list` - List uploaded files
- `GET /api/datasource/preview/{id}` - Preview data
- `POST /api/ai/analyze` - Generate AI insights
- `GET /api/visualizations/funnel` - Sales funnel data
- `GET /api/insights/problems` - List all problems
- `GET /api/devmode/recommend-model` - Get model recommendations

## 📝 Next Steps

- [ ] Add CRM integration (Salesforce, HubSpot, Zoho)
- [ ] Implement real-time data sync
- [ ] Add custom dashboard builder
- [ ] Deploy with Docker
- [ ] Add role-based access control

## 📄 License

Proprietary - Practus © 2025

