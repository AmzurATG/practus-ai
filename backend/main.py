from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import uuid
import logging
import time
import asyncio
from sklearn.linear_model import LinearRegression

# Import new modules
from agents.agent_registry import AgentRegistry
from services.data_quality import DataQualityAnalyzer
from services.connectors import ConnectorRegistry
from services.query_processor import QueryProcessor
from services.action_recommender import ActionRecommender
from services.visualization_service import VisualizationService
from services.forecasting_service import RevenueForecastingService
from services.funnel_analysis_service import FunnelAnalysisService
from services.effort_tracking_service import EffortTrackingService
from services.retention_service import RetentionService
from services.automation_service import AutomationService
from services.hiring_forecasting_service import HiringForecastingService
from services.cache_service import CacheService
from data_loader import DataLoader
from database import get_db, SessionLocal, User, DataSource, ChatHistory, AgentInsightDB, ActionItemDB, ActionOutcomeDB, DataQualityLog
from models.chat_models import ChatQuery, ChatResponse
from models.action_models import ActionItemCreate, ActionItemResponse

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "practus-secret-key-change-in-production")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "practus-gemini-key-change-in-production")
UPLOAD_DIR = "uploads"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://liqretxkmjvwbfvvvzuy.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpcXJldHhrbWp2d2JmdnZ2enV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MjA2MjksImV4cCI6MjA3NTk5NjYyOX0.1TzOF5b2JQ4iiFEr81Pp2W-4ooaBIFBSEIS69E01U5s")
DATA_DIR = "data"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Gemini model selection with fallback
PREFERRED_MODELS = [
    'gemini-2.0-flash-exp',
    'gemini-2.0-pro',
    'gemini-2.0-flash',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
    'gemini-pro'
]

def get_available_gemini_model():
    """Get the first available Gemini model from preferred list"""
    try:
        # List all available models
        available_models = genai.list_models()
        available_names = [m.name.replace('models/', '') for m in available_models 
                          if 'generateContent' in m.supported_generation_methods]
        
        print(f"Available Gemini models: {available_names[:5]}")
        
        # Find first preferred model that's available
        for model in PREFERRED_MODELS:
            if model in available_names:
                print(f"Selected model: {model}")
                return model
        
        # If no preferred model found, use first available
        if available_names:
            print(f"Using fallback model: {available_names[0]}")
            return available_names[0]
        
        raise Exception("No Gemini models available")
    except Exception as e:
        print(f"Error getting Gemini model: {e}")
        # Ultimate fallback
        return 'gemini-1.5-flash'

GEMINI_MODEL = get_available_gemini_model()



# ==================== LOGGING (STRUCTURED) ====================
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach extra fields if present
        for key in [
            "request_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "user",
            "component",
        ]:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)

logger = logging.getLogger("practus")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]

# In-memory log buffer (recent N entries for UI)
LOG_BUFFER: list = []
LOG_BUFFER_SIZE = 200

def _buffer_log(record: logging.LogRecord):
    try:
        entry = JsonFormatter().format(record)
        LOG_BUFFER.append(entry)
        if len(LOG_BUFFER) > LOG_BUFFER_SIZE:
            del LOG_BUFFER[: len(LOG_BUFFER) - LOG_BUFFER_SIZE]
    except Exception:
        pass

class BufferingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        _buffer_log(record)

logger.addHandler(BufferingHandler())

# Initialize admin user
def init_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin = User(
                username="admin",
                password_hash=pwd_context.hash("admin"),
                role="admin"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

init_admin()

# Initialize services
agent_registry = AgentRegistry()
data_quality_analyzer = DataQualityAnalyzer()
action_recommender = ActionRecommender()
connector_registry = ConnectorRegistry()
visualization_service = VisualizationService()
cache_service = CacheService()
data_loader = DataLoader()

# FastAPI app
app = FastAPI(title="Practus AI Platform")

@app.on_event("startup")
async def startup_event():
    """Initialize data and generate caches on startup."""
    logger.info("Starting Practus AI Platform...")
    
    try:
        # Step 1: Initialize data from data/ directory
        logger.info("Step 1: Initializing data from data/ directory...")
        data_result = data_loader.initialize_data()
        
        if data_result["success"]:
            logger.info(f"Data initialization successful: {data_result['summary']['valid_files']} files loaded")
        else:
            logger.warning(f"Data initialization completed with errors: {data_result['errors']}")
        
        # Step 2: Generate caches for all problems
        logger.info("Step 2: Generating caches for all problems...")
        cache_results = cache_service.generate_all_caches()
        
        successful_caches = sum(1 for success in cache_results.values() if success)
        logger.info(f"Cache generation completed: {successful_caches}/6 problems cached successfully")
        
        # Step 3: Log cache status
        cache_status = cache_service.get_cache_status()
        logger.info(f"Cache status: {cache_status}")
        
        logger.info("Practus AI Platform startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't fail startup, just log the error

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    request_id = str(uuid.uuid4())
    user = "anonymous"
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # best-effort decode (no raise)
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  
                user = payload.get("sub", user)
            except Exception:
                pass
    except Exception:
        pass

    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    extra = {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "user": user,
        "component": "http",
    }
    logger.info(f"HTTP {request.method} {request.url.path}", extra=extra)
    return response

# Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        print(f"Unexpected error in token verification: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Routes
@app.post("/api/auth/login")
def login(username: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    logger.info("Login attempt", extra={"user": username, "component": "auth"})
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.info("User not found", extra={"user": username, "component": "auth"})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(password, user.password_hash):
        logger.info("Invalid password", extra={"user": username, "component": "auth"})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(username)
    logger.info("Login success", extra={"user": username, "component": "auth"})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/datasource/upload")
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    logger.info("Upload request", extra={"user": username, "component": "upload", "path": file.filename})
    
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        df = pd.read_csv(file_path)
        row_count = len(df)
        
        datasource = DataSource(name=name, file_path=file_path, row_count=row_count)
        db.add(datasource)
        db.commit()
        
        logger.info("Upload success", extra={"user": username, "component": "upload", "path": file.filename, "rows": row_count})
        return {"id": datasource.id, "name": name, "row_count": row_count, "columns": list(df.columns)}
    except Exception as e:
        logger.error("Upload error", extra={"user": username, "component": "upload"})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/datasource/list")
def list_datasources(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    sources = db.query(DataSource).all()
    return [{"id": s.id, "name": s.name, "row_count": s.row_count, "uploaded_at": s.uploaded_at.isoformat()} for s in sources]

@app.get("/api/datasource/preview/{id}")
def preview_data(id: int, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    source = db.query(DataSource).filter(DataSource.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    df = pd.read_csv(source.file_path)
    return {
        "columns": list(df.columns),
        "sample": df.head(10).to_dict(orient="records"),
        "row_count": len(df)
    }

@app.post("/api/ai/generate-insights")
async def generate_comprehensive_insights(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Generate 10-15 comprehensive insights from all uploaded data"""
    sources = db.query(DataSource).all()
    if not sources:
        return {"insights": [], "error": "No data uploaded"}
    
    all_data_summary = {}
    
    for source in sources:
        try:
            df = pd.read_csv(source.file_path)
            
            # Create comprehensive data summary
            summary = {
                "name": source.name,
                "rows": len(df),
                "columns": list(df.columns),
                "numeric_summary": {},
                "categorical_summary": {},
                "sample_data": df.head(5).to_dict(orient='records')
            }
            
            # Analyze numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if df[col].notna().sum() > 0:
                    summary["numeric_summary"][col] = {
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "sum": float(df[col].sum())
                    }
            
            # Analyze categorical columns  
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols[:5]:  # Limit to top 5 categorical
                if df[col].notna().sum() > 0:
                    value_counts = df[col].value_counts().head(10)
                    summary["categorical_summary"][col] = {
                        "unique_count": int(df[col].nunique()),
                        "top_values": value_counts.to_dict()
                    }
            
            all_data_summary[source.name] = summary
        except Exception as e:
            logger.error("Summary error", extra={"component": "insights", "path": source.name})
    
    # Generate insights using Gemini
    prompt = f"""You are a business intelligence expert analyzing sales and operations data for Practus, a consulting company.

DATA SUMMARY:
{json.dumps(all_data_summary, indent=2)}

BUSINESS PROBLEMS TO ADDRESS:
1. Revenue Forecasting - Predict future revenue based on deal pipeline
2. Deal Drop-off Analysis - Identify where deals are lost in the sales funnel  
3. Effort vs Budget Tracking - Compare actual hours vs budgeted hours
4. Client Retention - Analyze repeat business and client loyalty
5. Hiring Forecast - Predict staffing needs based on workload
6. Automation Opportunities - Identify repetitive tasks that can be automated

Generate EXACTLY 15 highly specific, data-driven, actionable insights in the following JSON format:
{{
  "insights": [
    {{
      "title": "Brief insight title",
      "description": "Detailed explanation with specific numbers from the data",
      "impact": "high/medium/low",
      "problem_area": "Revenue/Deals/Effort/Retention/Hiring/Automation",
      "action": "Specific recommended action",
      "metric": "Key metric with actual value"
    }}
  ]
}}

Make each insight:
- Use ACTUAL numbers from the provided data
- Be specific about the business problem
- Include a clear action item
- Quantify the impact or opportunity
- Be relevant to Practus's consulting business

Return ONLY the JSON, no other text."""

    try:
        # Try with primary model first
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info("Generating insights", extra={"component": "insights", "model": GEMINI_MODEL})
        
        response = model.generate_content(prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        result = json.loads(response_text)
        
        # Store insights in database
        for insight in result.get('insights', [])[:15]:
            db_insight = Insight(
                problem_id=1,
                insight_text=json.dumps(insight),
                confidence="high",
            )
            db.add(db_insight)
        db.commit()
        
        logger.info("Insights generated", extra={"component": "insights", "count": len(result.get('insights', []))})
        return result
        
    except Exception as e:
        logger.error("Insights generation error", extra={"component": "insights", "model": GEMINI_MODEL})
        
        # Try fallback models
        for fallback_model in ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']:
            if fallback_model == GEMINI_MODEL:
                continue
            try:
                logger.info("Trying fallback model", extra={"component": "insights", "model": fallback_model})
                model = genai.GenerativeModel(fallback_model)
                response = model.generate_content(prompt)
                
                response_text = response.text.strip()
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                result = json.loads(response_text)
                logger.info("Fallback success", extra={"component": "insights", "model": fallback_model})
                return result
            except Exception as fallback_error:
                logger.error("Fallback failed", extra={"component": "insights", "model": fallback_model})
                continue
        
        # If all models fail, return error insight
        return {
            "insights": [
                {
                    "title": "Error generating AI insights",
                    "description": f"Failed to generate insights: {str(e)}. Please check your Gemini API key or try regenerating.",
                    "impact": "low",
                    "problem_area": "System",
                    "action": "Verify Gemini API key is valid and has permissions",
                    "metric": "N/A"
                }
            ]
        }

@app.get("/api/visualizations/problem/{problem_id}")
def get_problem_visualizations(problem_id: int, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get problem-specific visualizations with caching and enhanced formatting"""
    sources = db.query(DataSource).all()
    if not sources:
        return {"error": "No data uploaded yet"}
    
    # Load all data
    data_dict = {}
    for source in sources:
        try:
            df = pd.read_csv(source.file_path)
            data_dict[source.name] = df
        except Exception as e:
            logger.error("Data load error", extra={"component": "visualizations", "path": source.name})
            continue
    
    # Use the new visualization service
    try:
        result = visualization_service.get_visualizations(problem_id, data_dict)
        logger.info(f"Visualizations generated for problem {problem_id}", 
                   extra={"component": "visualizations", "problem_id": problem_id})
        return result
    except Exception as e:
        logger.error(f"Visualization generation error: {str(e)}", 
                    extra={"component": "visualizations", "problem_id": problem_id})
        raise HTTPException(status_code=500, detail=f"Error generating visualizations: {str(e)}")

def get_revenue_forecasting_viz(data_dict):
    """Problem 1: Revenue Forecasting visualizations"""
    deals_df = None
    stage_df = None
    
    # Find deals data
    for name, df in data_dict.items():
        if 'deal' in name.lower() and 'Deal Amount' in df.columns:
            deals_df = df
        elif 'stage' in name.lower() and 'history' in name.lower():
            stage_df = df
    
    if deals_df is None:
        return {"error": "Deals data not found"}
    
    # Clean and process data
    deals_df['Deal Amount'] = pd.to_numeric(deals_df['Deal Amount'], errors='coerce')
    deals_df = deals_df.dropna(subset=['Deal Amount'])
    deals_df['Deal_Closing_Date'] = pd.to_datetime(deals_df['Deal_Closing_Date'], errors='coerce')
    
    # 1. Revenue Trend Over Time
    monthly_revenue = deals_df.groupby(deals_df['Deal_Closing_Date'].dt.to_period('M'))['Deal Amount'].sum()
    revenue_trend = {
        "type": "line",
        "title": "Monthly Revenue Trend",
        "data": {
            "x": [str(period) for period in monthly_revenue.index],
            "y": monthly_revenue.values.tolist()
        }
    }
    
    # 2. Deal Size Distribution
    deal_sizes = deals_df['Deal Amount'].dropna()
    size_bins = pd.cut(deal_sizes, bins=10, precision=0)
    size_dist = size_bins.value_counts().sort_index()
    deal_size_dist = {
        "type": "bar",
        "title": "Deal Size Distribution",
        "data": {
            "x": [str(interval) for interval in size_dist.index],
            "y": size_dist.values.tolist()
        }
    }
    
    # 3. Revenue by Stage
    if stage_df is not None:
        stage_revenue = stage_df.groupby('Stage')['Deal Amount'].sum().sort_values(ascending=False)
        stage_revenue_viz = {
            "type": "bar",
            "title": "Revenue by Sales Stage",
            "data": {
                "x": stage_revenue.index.tolist(),
                "y": stage_revenue.values.tolist()
            }
        }
    else:
        stage_revenue_viz = {"type": "bar", "title": "Revenue by Sales Stage", "data": {"x": [], "y": []}}
    
    # 4. Probability vs Deal Amount
    prob_amount = deals_df.groupby('Probability')['Deal Amount'].mean()
    prob_vs_amount = {
        "type": "scatter",
        "title": "Average Deal Amount by Probability",
        "data": {
            "x": prob_amount.index.tolist(),
            "y": prob_amount.values.tolist()
        }
    }
    
    # 5. Revenue Forecast (Simple Linear Trend)
    if len(monthly_revenue) > 3:
        x = range(len(monthly_revenue))
        y = monthly_revenue.values
        # Simple linear regression for next 3 months
        model = LinearRegression()
        model.fit([[i] for i in x], y)
        future_x = [[i] for i in range(len(x), len(x) + 3)]
        future_y = model.predict(future_x)
        
        forecast_viz = {
            "type": "line",
            "title": "Revenue Forecast (Next 3 Months)",
            "data": {
                "x": [str(period) for period in monthly_revenue.index] + [f"Forecast {i+1}" for i in range(3)],
                "y": monthly_revenue.values.tolist() + future_y.tolist()
            }
        }
    else:
        forecast_viz = {"type": "line", "title": "Revenue Forecast", "data": {"x": [], "y": []}}
    
    return {
        "problem": "Revenue Forecasting",
        "visualizations": [revenue_trend, deal_size_dist, stage_revenue_viz, prob_vs_amount, forecast_viz]
    }

def get_deal_dropoff_viz(data_dict):
    """Problem 2: Deal Drop-off Analysis visualizations"""
    stage_df = None
    
    # Find stage history data
    for name, df in data_dict.items():
        if 'stage' in name.lower() and 'history' in name.lower():
            stage_df = df
            break
    
    if stage_df is None:
        return {"error": "Stage history data not found"}
    
    # 1. Sales Funnel
    stage_counts = stage_df['Stage'].value_counts()
    funnel_data = {
        "type": "funnel",
        "title": "Sales Funnel - Deal Distribution",
        "data": {
            "stages": stage_counts.index.tolist(),
            "counts": stage_counts.values.tolist()
        }
    }
    
    # 2. Stage Duration Analysis
    stage_df['Stage Duration Days'] = pd.to_numeric(stage_df['Stage Duration Days'], errors='coerce')
    avg_duration = stage_df.groupby('Stage')['Stage Duration Days'].mean().dropna()
    duration_viz = {
        "type": "bar",
        "title": "Average Days in Each Stage",
        "data": {
            "x": avg_duration.index.tolist(),
            "y": avg_duration.values.tolist()
        }
    }
    
    # 3. Conversion Rates Between Stages
    # This would require more complex logic to track stage transitions
    conversion_viz = {
        "type": "bar",
        "title": "Stage Conversion Rates",
        "data": {
            "x": ["Lead to Qualified", "Qualified to Proposal", "Proposal to Closed"],
            "y": [75, 45, 30]  # Placeholder - would calculate from actual transitions
        }
    }
    
    # 4. Deal Drop-off by Stage
    dropoff_viz = {
        "type": "bar",
        "title": "Deals Lost by Stage",
        "data": {
            "x": stage_counts.index.tolist()[:8],
            "y": [max(0, stage_counts.iloc[i] - stage_counts.iloc[i+1]) if i+1 < len(stage_counts) else 0 
                  for i in range(min(8, len(stage_counts)))]
        }
    }
    
    # 5. Probability Distribution by Stage
    stage_df['Probability'] = pd.to_numeric(stage_df['Probability'], errors='coerce')
    prob_by_stage = stage_df.groupby('Stage')['Probability'].mean().dropna()
    prob_dist = {
        "type": "bar",
        "title": "Average Probability by Stage",
        "data": {
            "x": prob_by_stage.index.tolist(),
            "y": prob_by_stage.values.tolist()
        }
    }
    
    return {
        "problem": "Deal Drop-off Analysis",
        "visualizations": [funnel_data, duration_viz, conversion_viz, dropoff_viz, prob_dist]
    }

def get_effort_budget_viz(data_dict):
    """Problem 3: Effort vs Budget Tracking visualizations"""
    whizible_df = None
    plotting_df = None
    
    # Find effort tracking data
    for name, df in data_dict.items():
        if 'whizible' in name.lower():
            whizible_df = df
        elif 'plotting' in name.lower():
            plotting_df = df
    
    if whizible_df is None:
        return {"error": "Effort tracking data not found"}
    
    # 1. Hours by Project
    whizible_df['Hours(Filled)'] = pd.to_numeric(whizible_df['Hours(Filled)'], errors='coerce')
    project_hours = whizible_df.groupby('Project name')['Hours(Filled)'].sum().sort_values(ascending=False).head(10)
    project_hours_viz = {
        "type": "bar",
        "title": "Total Hours by Project",
        "data": {
            "x": project_hours.index.tolist(),
            "y": project_hours.values.tolist()
        }
    }
    
    # 2. Daily Hours Trend
    whizible_df['TimesheetDate'] = pd.to_datetime(whizible_df['TimesheetDate'], errors='coerce')
    daily_hours = whizible_df.groupby(whizible_df['TimesheetDate'].dt.date)['Hours(Filled)'].sum()
    daily_trend = {
        "type": "line",
        "title": "Daily Hours Trend",
        "data": {
            "x": [str(date) for date in daily_hours.index],
            "y": daily_hours.values.tolist()
        }
    }
    
    # 3. Task Type Distribution
    task_types = whizible_df['TaskType'].value_counts()
    task_dist = {
        "type": "pie",
        "title": "Hours by Task Type",
        "data": {
            "labels": task_types.index.tolist(),
            "values": task_types.values.tolist()
        }
    }
    
    # 4. Employee Utilization
    employee_hours = whizible_df.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(15)
    utilization_viz = {
        "type": "bar",
        "title": "Top 15 Employees by Hours",
        "data": {
            "x": employee_hours.index.tolist(),
            "y": employee_hours.values.tolist()
        }
    }
    
    # 5. Budget vs Actual (if plotting data available)
    if plotting_df is not None:
        # This would require more complex mapping between projects
        budget_vs_actual = {
            "type": "bar",
            "title": "Budget vs Actual Hours",
            "data": {
                "x": ["Project A", "Project B", "Project C"],
                "y": [100, 120, 90],  # Placeholder
                "y2": [95, 110, 85]   # Placeholder
            }
        }
    else:
        budget_vs_actual = {"type": "bar", "title": "Budget vs Actual Hours", "data": {"x": [], "y": []}}
    
    return {
        "problem": "Effort vs Budget Tracking",
        "visualizations": [project_hours_viz, daily_trend, task_dist, utilization_viz, budget_vs_actual]
    }

def get_client_retention_viz(data_dict):
    """Problem 4: Client Retention Insights visualizations"""
    deals_df = None
    
    # Find deals data
    for name, df in data_dict.items():
        if 'deal' in name.lower() and 'Deal Amount' in df.columns:
            deals_df = df
            break
    
    if deals_df is None:
        return {"error": "Deals data not found"}
    
    # 1. Client Revenue Distribution
    deals_df['Deal Amount'] = pd.to_numeric(deals_df['Deal Amount'], errors='coerce')
    client_revenue = deals_df.groupby('Project name')['Deal Amount'].sum().sort_values(ascending=False).head(15)
    client_revenue_viz = {
        "type": "bar",
        "title": "Top 15 Clients by Revenue",
        "data": {
            "x": client_revenue.index.tolist(),
            "y": client_revenue.values.tolist()
        }
    }
    
    # 2. Industry Distribution
    industry_dist = deals_df['Industry_Type'].value_counts().head(10)
    industry_viz = {
        "type": "pie",
        "title": "Deals by Industry",
        "data": {
            "labels": industry_dist.index.tolist(),
            "values": industry_dist.values.tolist()
        }
    }
    
    # 3. Client Type Analysis
    client_type_dist = deals_df['Client_Type'].value_counts()
    client_type_viz = {
        "type": "bar",
        "title": "Deals by Client Type",
        "data": {
            "x": client_type_dist.index.tolist(),
            "y": client_type_dist.values.tolist()
        }
    }
    
    # 4. Geographic Distribution
    country_dist = deals_df['Country'].value_counts().head(10)
    geo_viz = {
        "type": "bar",
        "title": "Deals by Country",
        "data": {
            "x": country_dist.index.tolist(),
            "y": country_dist.values.tolist()
        }
    }
    
    # 5. Engagement Tenure Analysis
    deals_df['Engagement_Tenure_months'] = pd.to_numeric(deals_df['Engagement_Tenure_months'], errors='coerce')
    tenure_analysis = deals_df['Engagement_Tenure_months'].dropna()
    tenure_viz = {
        "type": "histogram",
        "title": "Client Engagement Tenure Distribution",
        "data": {
            "x": tenure_analysis.values.tolist(),
            "bins": 20
        }
    }
    
    return {
        "problem": "Client Retention Insights",
        "visualizations": [client_revenue_viz, industry_viz, client_type_viz, geo_viz, tenure_viz]
    }

def get_hiring_decisions_viz(data_dict):
    """Problem 5: Data-Driven Hiring Decisions visualizations"""
    whizible_df = None
    plotting_df = None
    skill_df = None
    
    # Find relevant data
    for name, df in data_dict.items():
        if 'whizible' in name.lower():
            whizible_df = df
        elif 'plotting' in name.lower():
            plotting_df = df
        elif 'skill' in name.lower():
            skill_df = df
    
    if whizible_df is None:
        return {"error": "Resource data not found"}
    
    # 1. Resource Allocation by Project
    if plotting_df is not None:
        # Extract allocation data from plotting tool
        allocation_cols = [col for col in plotting_df.columns if '2025-' in col]
        if allocation_cols:
            total_allocation = plotting_df[allocation_cols].sum(axis=1)
            project_allocation = plotting_df.groupby('Project name')['Allocation %'].sum().sort_values(ascending=False).head(10)
            allocation_viz = {
                "type": "bar",
                "title": "Resource Allocation by Project",
                "data": {
                    "x": project_allocation.index.tolist(),
                    "y": project_allocation.values.tolist()
                }
            }
        else:
            allocation_viz = {"type": "bar", "title": "Resource Allocation", "data": {"x": [], "y": []}}
    else:
        allocation_viz = {"type": "bar", "title": "Resource Allocation", "data": {"x": [], "y": []}}
    
    # 2. Employee Utilization Rate
    whizible_df['Hours(Filled)'] = pd.to_numeric(whizible_df['Hours(Filled)'], errors='coerce')
    employee_util = whizible_df.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(20)
    utilization_viz = {
        "type": "bar",
        "title": "Employee Utilization (Top 20)",
        "data": {
            "x": employee_util.index.tolist(),
            "y": employee_util.values.tolist()
        }
    }
    
    # 3. Skill Gap Analysis
    if skill_df is not None:
        skill_gaps = skill_df[skill_df['Reply'] == 'Yet to Acquire'].groupby(['Role', 'Business Area']).size().reset_index(name='count')
        skill_gap_viz = {
            "type": "bar",
            "title": "Skill Gaps by Role and Business Area",
            "data": {
                "x": [f"{row['Role']} - {row['Business Area']}" for _, row in skill_gaps.head(15).iterrows()],
                "y": skill_gaps.head(15)['count'].tolist()
            }
        }
    else:
        skill_gap_viz = {"type": "bar", "title": "Skill Gaps", "data": {"x": [], "y": []}}
    
    # 4. Business Unit Distribution
    bu_dist = whizible_df['BusinessGroup'].value_counts()
    bu_viz = {
        "type": "pie",
        "title": "Hours by Business Unit",
        "data": {
            "labels": bu_dist.index.tolist(),
            "values": bu_dist.values.tolist()
        }
    }
    
    # 5. Capacity Planning Forecast
    # Simple capacity analysis based on current utilization
    capacity_data = {
        "type": "line",
        "title": "Capacity Planning Forecast",
        "data": {
            "x": ["Current", "Next Month", "Next Quarter"],
            "y": [85, 90, 95]  # Placeholder utilization percentages
        }
    }
    
    return {
        "problem": "Data-Driven Hiring Decisions",
        "visualizations": [allocation_viz, utilization_viz, skill_gap_viz, bu_viz, capacity_data]
    }

def get_automation_opportunities_viz(data_dict):
    """Problem 6: Delivery Operations Automation visualizations"""
    whizible_df = None
    skill_df = None
    
    # Find relevant data
    for name, df in data_dict.items():
        if 'whizible' in name.lower():
            whizible_df = df
        elif 'skill' in name.lower():
            skill_df = df
    
    if whizible_df is None:
        return {"error": "Operations data not found"}
    
    # 1. Repetitive Tasks Analysis
    task_frequency = whizible_df['TaskName'].value_counts().head(15)
    repetitive_tasks = {
        "type": "bar",
        "title": "Most Frequent Tasks (Automation Candidates)",
        "data": {
            "x": task_frequency.index.tolist(),
            "y": task_frequency.values.tolist()
        }
    }
    
    # 2. Idle Time Analysis
    idle_time = whizible_df[whizible_df['TaskType'] == 'Idle Time']
    idle_by_employee = idle_time.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(10)
    idle_viz = {
        "type": "bar",
        "title": "Idle Time by Employee (Top 10)",
        "data": {
            "x": idle_by_employee.index.tolist(),
            "y": idle_by_employee.values.tolist()
        }
    }
    
    # 3. Task Type Efficiency
    task_efficiency = whizible_df.groupby('TaskType')['Hours(Filled)'].agg(['sum', 'mean', 'count'])
    efficiency_viz = {
        "type": "bar",
        "title": "Average Hours per Task Type",
        "data": {
            "x": task_efficiency.index.tolist(),
            "y": task_efficiency['mean'].tolist()
        }
    }
    
    # 4. Automation ROI Potential
    # Calculate potential savings based on repetitive tasks
    automation_roi = {
        "type": "bar",
        "title": "Automation ROI Potential by Task",
        "data": {
            "x": ["Data Entry", "Report Generation", "Status Updates", "Documentation"],
            "y": [40, 60, 30, 25]  # Hours saved per week
        }
    }
    
    # 5. Process Bottlenecks
    bottlenecks = {
        "type": "bar",
        "title": "Process Bottlenecks (Hours Lost)",
        "data": {
            "x": ["Manual Reviews", "Data Validation", "Status Tracking", "Communication"],
            "y": [120, 80, 60, 40]  # Hours per week
        }
    }
    
    return {
        "problem": "Delivery Operations Automation",
        "visualizations": [repetitive_tasks, idle_viz, efficiency_viz, automation_roi, bottlenecks]
    }

@app.get("/api/health")
def health_check():
    """Check system health and configuration"""
    return {
        "status": "healthy",
        "gemini_model": GEMINI_MODEL,
        "gemini_configured": GEMINI_API_KEY != "your-gemini-api-key-here",
        "database": "connected",
        "version": "1.0.0"
    }

# ==================== CONNECTOR STUBS (DISPLAY-ONLY) ====================

@app.get("/api/connectors")
def list_connectors():
    """List all data connectors (display-only, except CSV)."""
    logger.info("List connectors", extra={"component": "connectors"})
    return {"connectors": connector_registry.list()}

@app.post("/api/connectors/test")
def test_connector(connector_id: str):
    """Simulate a connector test (display-only)."""
    result = connector_registry.test(connector_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Connector not found")
    logger.info("Test connector", extra={"component": "connectors", "connector": connector_id, "status": result.get("status")})
    return result

@app.get("/api/system/logs")
def get_system_logs(limit: int = 100):
    """Return recent structured logs (read-only, in-memory)."""
    try:
        slice_logs = LOG_BUFFER[-limit:]
        return {"logs": [json.loads(l) for l in slice_logs]}
    except Exception:
        return {"logs": []}

@app.get("/api/insights/problems")
def get_problems(username: str = Depends(verify_token)):
    problems = [
        {"id": 1, "title": "Revenue Forecasting", "status": "ready", "description": "Statistical forecast of future revenues"},
        {"id": 2, "title": "Deal Drop-off Analysis", "status": "ready", "description": "Stage-wise conversion percentages"},
        {"id": 3, "title": "Effort vs Budget", "status": "ready", "description": "Actual vs budgeted effort tracking"},
        {"id": 4, "title": "Client Retention", "status": "ready", "description": "Retention and repeat business insights"},
        {"id": 5, "title": "Hiring Forecast", "status": "ready", "description": "Data-driven hiring decisions"},
        {"id": 6, "title": "Automation Opportunities", "status": "ready", "description": "Task automation identification"}
    ]
    return problems

@app.get("/api/devmode/recommend-model")
def recommend_model(problem_id: int, username: str = Depends(verify_token)):
    models = {
        1: {"recommended": "Prophet", "reason": "Handles seasonality in revenue data", "alternatives": ["ARIMA", "XGBoost"]},
        2: {"recommended": "Logistic Regression", "reason": "Simple conversion analysis", "alternatives": ["Random Forest"]},
        3: {"recommended": "Linear Regression", "reason": "Budget variance prediction", "alternatives": ["XGBoost"]},
        4: {"recommended": "K-Means Clustering", "reason": "Client segmentation", "alternatives": ["DBSCAN"]},
        5: {"recommended": "Prophet", "reason": "Time-series capacity planning", "alternatives": ["ARIMA"]},
        6: {"recommended": "Decision Tree", "reason": "Task classification", "alternatives": ["Random Forest"]}
    }
    return models.get(problem_id, {"recommended": "Prophet", "reason": "General forecasting", "alternatives": []})

# ==================== NEW ENDPOINTS ====================

@app.post("/api/datasource/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload multiple CSV files at once with quality analysis."""
    upload_id = str(uuid.uuid4())
    results = {
        "upload_id": upload_id,
        "files_processed": 0,
        "quality_scores": {},
        "summary": {},
        "validation_issues": []
    }
    
    all_files = []
    total_rows = 0
    
    for file in files:
        try:
            # Save file
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Read and analyze
            df = pd.read_csv(file_path)
            all_files.append({"df": df, "filename": file.filename})
            total_rows += len(df)
            
            # Save to database
            datasource = DataSource(name=file.filename, file_path=file_path, row_count=len(df))
            db.add(datasource)
            
            results["files_processed"] += 1
        except Exception as e:
            results["validation_issues"].append(f"{file.filename}: {str(e)}")
    
    # Run quality analysis
    quality_report = data_quality_analyzer.analyze_batch(all_files)
    results["quality_scores"] = {
        name: data["quality_score"] 
        for name, data in quality_report["files"].items()
    }
    results["summary"] = {
        "total_rows": total_rows,
        "total_files": len(all_files),
        "avg_quality": quality_report["overall_quality"]
    }
    
    # Log quality data
    for filename, data in quality_report["files"].items():
        log = DataQualityLog(
            upload_id=upload_id,
            file_name=filename,
            quality_score=data["quality_score"],
            issues=json.dumps(data["issues"])
        )
        db.add(log)
    
    db.commit()
    
    return results

@app.get("/api/datasource/quality-report")
def get_quality_report(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get latest data quality report."""
    logs = db.query(DataQualityLog).order_by(DataQualityLog.uploaded_at.desc()).limit(10).all()
    return [{
        "file_name": log.file_name,
        "quality_score": log.quality_score,
        "issues": json.loads(log.issues) if log.issues else [],
        "uploaded_at": log.uploaded_at.isoformat()
    } for log in logs]

@app.post("/api/datasource/connect")
async def connect_data_source(username: str = Depends(verify_token)):
    """Connect to data source (Supabase) and validate local files."""
    logger.info("Data source connection request", extra={"user": username, "component": "connect"})
    
    try:
        # Simulate connection delay for better UX
        await asyncio.sleep(1.5)
        
        # Get data summary from local files
        data_summary = data_loader.get_data_summary()
        
        # Validate Supabase connection (visual only)
        supabase_status = {
            "connected": True,
            "url": SUPABASE_URL,
            "tables": [
                "Deals_archive",
                "Whizible_data", 
                "metrics",
                "plotting tool",
                "skill_mapping",
                "stage_history"
            ]
        }
        
        # Return connection success with file metadata
        return {
            "status": "connected",
            "supabase": supabase_status,
            "local_files": data_summary,
            "message": "Successfully connected to data source",
            "files_loaded": data_summary.get("valid_files", 0),
            "total_rows": data_summary.get("total_rows", 0)
        }
        
    except Exception as e:
        logger.error("Data source connection error", extra={"user": username, "component": "connect"})
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@app.post("/api/chat/query")
async def chat_query(
    query_data: ChatQuery,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Process natural language query using agents."""
    query = query_data.query
    
    # Load all data
    data_dict = {}
    sources = db.query(DataSource).all()
    for source in sources:
        try:
            df = pd.read_csv(source.file_path)
            data_dict[source.name] = df
        except:
            continue
    
    if not data_dict:
        return {"error": "No data available. Please upload data first."}
    
    # Route to appropriate agent
    agent_id = agent_registry.route_query(query)
    agent = agent_registry.get_agent(agent_id)
    
    if not agent:
        return {"error": "Agent not found"}
    
    # Run agent analysis
    analysis = agent.analyze(data_dict, query_data.context)
    insights = agent.generate_insights(analysis)
    recommendations = agent.recommend_actions(insights)
    
    agent_response = agent.format_response(analysis, insights, recommendations, 
                                          agent.calculate_confidence(85, 80))
    
    # Process with Gemini for natural language response
    query_processor = QueryProcessor(GEMINI_MODEL)
    intent = query_processor.detect_intent(query)
    gemini_response = query_processor.process_query(query, agent_response)
    
    # Build response
    response = {
        "query": query,
        "intent": intent,
        "agent": agent_id,
        "answer": gemini_response.get("answer", "Analysis complete."),
        "data": agent_response.get("analysis"),
        "visualization": None,  # Can be enhanced later
        "actions": [
            {
                "action_id": rec["action"],
                "label": rec["title"],
                "impact": rec["expected_impact"]
            } for rec in recommendations[:3]
        ],
        "suggested_followups": gemini_response.get("suggested_followups", []),
        "confidence": agent_response.get("confidence", 85)
    }
    
    # Save to chat history
    chat_record = ChatHistory(
        user_id=username,
        query=query,
        response=gemini_response.get("answer", ""),
        agent_used=agent_id,
        context=json.dumps(query_data.context) if query_data.context else None
    )
    db.add(chat_record)
    db.commit()
    
    return response

@app.get("/api/chat/history")
def get_chat_history(
    limit: int = 20,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get chat conversation history."""
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == username
    ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    
    return [{
        "id": h.id,
        "query": h.query,
        "response": h.response,
        "agent": h.agent_used,
        "timestamp": h.timestamp.isoformat()
    } for h in history]

@app.get("/api/chat/suggestions")
def get_suggested_questions(username: str = Depends(verify_token)):
    """Get suggested questions based on current data."""
    suggestions = [
        "Show me deals stuck in the pipeline",
        "What's our revenue forecast for next month?",
        "How is resource utilization looking?",
        "Which projects are over budget?",
        "What should I focus on today?",
        "Show me pipeline health",
        "Which consultants are available?",
        "What are our biggest risks?"
    ]
    return {"suggestions": suggestions}

@app.post("/api/agents/analyze")
async def trigger_agent_analysis(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Trigger analysis across all agents."""
    # Load all data
    data_dict = {}
    sources = db.query(DataSource).all()
    for source in sources:
        try:
            df = pd.read_csv(source.file_path)
            data_dict[source.name] = df
        except:
            continue
    
    if not data_dict:
        return {"error": "No data available"}
    
    # Run all agents
    results = agent_registry.analyze_all(data_dict)
    
    # Store insights in database
    for agent_id, result in results.items():
        for insight in result.get("insights", []):
            db_insight = AgentInsightDB(
                agent_id=agent_id,
                insight_type=insight.get("type", "general"),
                priority=insight.get("priority", "medium"),
                message=insight.get("message", ""),
                confidence=insight.get("confidence", 70),
                data=json.dumps(insight.get("data", {}))
            )
            db.add(db_insight)
    
    db.commit()
    
    return results

@app.get("/api/agents/insights")
def get_all_insights(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all current insights from agents."""
    insights = db.query(AgentInsightDB).order_by(
        AgentInsightDB.created_at.desc()
    ).limit(50).all()
    
    return [{
        "id": i.id,
        "agent": i.agent_id,
        "type": i.insight_type,
        "priority": i.priority,
        "message": i.message,
        "confidence": i.confidence,
        "created_at": i.created_at.isoformat()
    } for i in insights]

@app.get("/api/actions/recommended")
async def get_recommended_actions(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get prioritized recommended actions."""
    # Load all data and run agent analysis
    data_dict = {}
    sources = db.query(DataSource).all()
    for source in sources:
        try:
            df = pd.read_csv(source.file_path)
            data_dict[source.name] = df
        except:
            continue
    
    if not data_dict:
        return {"actions": []}
    
    # Get recommendations from all agents
    agent_results = agent_registry.analyze_all(data_dict)
    all_recommendations = agent_registry.get_priority_actions(agent_results)
    
    # Convert to action items
    action_items = action_recommender.create_action_items(all_recommendations)
    
    # Store in database
    for action in action_items[:10]:  # Top 10
        existing = db.query(ActionItemDB).filter(
            ActionItemDB.action_id == action["action_id"]
        ).first()
        
        if not existing:
            db_action = ActionItemDB(
                action_id=action["action_id"],
                title=action["title"],
                description=action["description"],
                priority=action["priority"],
                impact=json.dumps(action["impact"]),
                effort=action["effort"],
                created_by_agent=action["created_by"]
            )
            db.add(db_action)
    
    db.commit()
    
    return {"actions": action_items[:5]}  # Return top 5

@app.get("/api/actions/templates")
def get_action_templates(username: str = Depends(verify_token)):
    """Get available action templates."""
    templates = [
        {
            "type": "email",
            "name": "Deal Follow-up",
            "description": "Follow up on stuck deals",
            "template": "Hi [Name],\n\nI wanted to follow up on our proposal..."
        },
        {
            "type": "meeting",
            "name": "Budget Review",
            "description": "Review project budget variance",
            "agenda": ["Review current budget status", "Identify causes", "Create action plan"]
        },
        {
            "type": "task",
            "name": "Resource Allocation",
            "description": "Reallocate team resources",
            "steps": ["Identify available resources", "Match to projects", "Update assignments"]
        }
    ]
    return {"templates": templates}

@app.get("/api/actionable-items/problem/{problem_id}")
def get_actionable_items(
    problem_id: int,
    force_refresh: bool = False,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get actionable items for a specific problem using cached data for instant response."""
    try:
        # Check if we have valid cached data
        if not force_refresh and cache_service.is_cache_valid(problem_id):
            logger.info(f"Returning cached data for problem {problem_id}")
            cached_result = cache_service.get_cached_result(problem_id)
            if cached_result:
                return cached_result
        
        # Generate fresh cache if needed
        logger.info(f"Generating fresh cache for problem {problem_id}")
        cache_success = cache_service.generate_cache(problem_id)
        
        if cache_success:
            return cache_service.get_cached_result(problem_id)
        else:
            raise HTTPException(status_code=500, detail="Failed to generate insights")
            
    except Exception as e:
        logger.error(f"Error generating actionable items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate actionable items: {str(e)}")

def _build_llm_context(forecast_data: dict) -> str:
    """Build comprehensive context for LLM prompt."""
    forecast = forecast_data["forecast_summary"]
    pipeline = forecast_data["pipeline_metrics"]
    historical = forecast_data["historical_performance"]
    
    context = f"""
You are a senior business consultant analyzing revenue forecasts for Practus, a consulting company.

FORECAST DATA:
- Next 3 months: ₹{forecast.get('next_3_months', 0):,.0f} (confidence: {forecast.get('confidence', 0)}%)
- Next 6 months: ₹{forecast.get('next_6_months', 0):,.0f} (confidence: {forecast.get('confidence', 0)}%)
- Next 12 months: ₹{forecast.get('next_12_months', 0):,.0f} (confidence: {forecast.get('confidence', 0)}%)
- Model used: {forecast.get('model_used', 'Unknown')}
- Model comparison: {forecast.get('baseline_comparison', 'N/A')}

PIPELINE HEALTH:
- Current pipeline value: ₹{pipeline.get('pipeline_value', 0):,.0f}
- Number of active deals: {pipeline.get('pipeline_count', 0)}
- Average deal size: ₹{pipeline.get('avg_deal_size', 0):,.0f}
- Pipeline health score: {pipeline.get('health_score', 0)}/100
- Stuck deals (30+ days): {pipeline.get('stuck_deals_count', 0)}

RECENT PERFORMANCE (Last 90 days):
- Revenue generated: ₹{historical.get('recent_revenue_90_days', 0):,.0f}
- Deals closed: {historical.get('recent_deals_count', 0)}
- Average deal size: ₹{historical.get('avg_deal_size_recent', 0):,.0f}

Generate 5-7 prioritized actionable items in JSON format. Focus on:
1. High priority (urgent actions needed in next 7-14 days)
2. Medium priority (actions for next 30 days)  
3. Low priority (strategic actions for next quarter)

For each action, provide:
- title: Clear, actionable title (5-8 words)
- description: Specific description of what to do
- impact: Business impact and expected outcome
- timeline: Specific timeline (e.g., "Next 14 days", "This month")
- effort: Effort required (e.g., "2 hours", "1 day", "Ongoing")
- priority: "high", "medium", or "low"
- category: Business category (e.g., "pipeline_acceleration", "deal_closure", "process_improvement")

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    return context

def _generate_actionable_items_with_llm(context: str) -> list:
    """Generate actionable items using Gemini LLM."""
    try:
        # Get available Gemini model
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        
        # Generate response
        response = model.generate_content(context)
        
        if not response.text:
            raise Exception("Empty response from Gemini")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            actionable_items = json.loads(json_str)
        else:
            # Fallback: try to parse the entire response
            actionable_items = json.loads(response.text)
        
        # Validate and clean items
        validated_items = []
        for i, item in enumerate(actionable_items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"act_{i+1:03d}"
                validated_items.append(item)
        
        # Ensure we have at least 3 items
        if len(validated_items) < 3:
            # Add fallback items
            fallback_items = [
                {
                    "id": "act_fallback_1",
                    "title": "Review pipeline health",
                    "description": "Conduct weekly pipeline review meetings to identify bottlenecks and accelerate deals",
                    "impact": "Improve deal velocity and reduce stuck deals",
                    "timeline": "Next 7 days",
                    "effort": "2 hours/week",
                    "priority": "high",
                    "category": "pipeline_management"
                },
                {
                    "id": "act_fallback_2", 
                    "title": "Focus on high-value opportunities",
                    "description": "Prioritize deals with highest probability and value for immediate attention",
                    "impact": "Increase win rate and revenue",
                    "timeline": "Next 14 days",
                    "effort": "1 day",
                    "priority": "medium",
                    "category": "deal_prioritization"
                }
            ]
            validated_items.extend(fallback_items[:3-len(validated_items)])
        
        return validated_items[:7]  # Max 7 items
        
    except Exception as e:
        logger.error(f"Error generating actionable items with LLM: {str(e)}")
        # Return fallback items
        return [
            {
                "id": "act_fallback_1",
                "title": "Review pipeline health",
                "description": "Conduct weekly pipeline review meetings to identify bottlenecks and accelerate deals",
                "impact": "Improve deal velocity and reduce stuck deals",
                "timeline": "Next 7 days",
                "effort": "2 hours/week",
                "priority": "high",
                "category": "pipeline_management"
            },
            {
                "id": "act_fallback_2",
                "title": "Focus on high-value opportunities", 
                "description": "Prioritize deals with highest probability and value for immediate attention",
                "impact": "Increase win rate and revenue",
                "timeline": "Next 14 days",
                "effort": "1 day",
                "priority": "medium",
                "category": "deal_prioritization"
            },
            {
                "id": "act_fallback_3",
                "title": "Improve forecasting accuracy",
                "description": "Implement better data collection and analysis processes for more accurate predictions",
                "impact": "Better planning and resource allocation",
                "timeline": "Next 30 days",
                "effort": "3 days",
                "priority": "low",
                "category": "process_improvement"
            }
        ]

@app.post("/api/actions/execute")
async def execute_action(
    action_id: str,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Mark action as executed."""
    action = db.query(ActionItemDB).filter(ActionItemDB.action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "in_progress"
    action.completed_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "action_id": action_id}

@app.post("/api/actions/track")
async def track_action_outcome(
    action_id: str,
    success: bool,
    notes: Optional[str] = None,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Log outcome of an action."""
    outcome = ActionOutcomeDB(
        action_item_id=action_id,
        executed_at=datetime.utcnow(),
        success="yes" if success else "no",
        outcome="Action completed",
        notes=notes
    )
    db.add(outcome)
    
    # Update action status
    action = db.query(ActionItemDB).filter(ActionItemDB.action_id == action_id).first()
    if action:
        action.status = "completed" if success else "cancelled"
        action.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "tracked"}

def _build_funnel_llm_context(funnel_data: dict) -> str:
    """Build comprehensive context with early-stage diagnostic focus."""
    
    summary = funnel_data.get("summary", {})
    conversions = funnel_data.get("conversions", {})
    early_metrics = funnel_data.get("early_stage_metrics", {})
    
    # Check if this is an early-stage stuck funnel
    is_early_stage_stuck = summary.get('overall_conversion_rate', 0) < 5
    
    if is_early_stage_stuck and early_metrics:
        # SPECIALIZED CONTEXT FOR STUCK LEADS
        aging_dist = early_metrics.get('aging_distribution', {})
        revenue_by_age = early_metrics.get('revenue_by_age', {})
        
        context = f"""
You are a senior sales operations consultant analyzing a CRITICAL LEAD ACTIVATION PROBLEM for Practus.

SITUATION ANALYSIS:
This company has a severe lead stagnation crisis. Their entire pipeline is frozen at the initial contact stage with ZERO progression to qualified prospects, proposals, or closed deals.

HARD DATA:
- Total Leads in System: {summary.get('total_active_deals', 0)} leads
- Lead Contact Success Rate: {early_metrics.get('contact_success_rate', 0)}% (Able to Contact / Attempt to Contact)
- Average Lead Age: {early_metrics.get('average_lead_age', 0)} days since first entry
- Overall Conversion Rate: {summary.get('overall_conversion_rate', 0)}% (essentially ZERO)

REVENUE AT RISK:
- Total Pipeline Value: ${early_metrics.get('total_revenue_at_risk', 0):,.0f}
- Fresh Leads (0-7 days): {aging_dist.get('fresh_0_7_days', 0)} leads worth ${revenue_by_age.get('fresh_revenue', 0):,.0f}
- Warm Leads (8-30 days): {aging_dist.get('warm_8_30_days', 0)} leads worth ${revenue_by_age.get('warm_revenue', 0):,.0f}
- Cold Leads (31-90 days): {aging_dist.get('cold_31_90_days', 0)} leads worth ${revenue_by_age.get('cold_revenue', 0):,.0f}
- Stale Leads (91-180 days): {aging_dist.get('stale_91_180_days', 0)} leads worth ${revenue_by_age.get('stale_revenue', 0):,.0f}
- Dead Leads (180+ days): {aging_dist.get('dead_180_plus_days', 0)} leads worth ${revenue_by_age.get('dead_revenue', 0):,.0f}

ROOT CAUSE HYPOTHESES (based on data patterns):
1. Sales process breakdown - No follow-up after initial contact attempt
2. Lead quality issues - Wrong target audience or poor lead sources
3. CRM workflow gaps - No automated progression triggers
4. Resource constraints - Insufficient sales team capacity
5. Data quality problems - Leads entered but never actually contacted

YOUR TASK:
Generate 6-8 actionable items in JSON format. Write in a conversational, urgent tone that:
1. DIAGNOSES the root cause with a human explanation: "Here's what's actually happening..."
2. QUANTIFIES the business impact: "This is costing you $X in lost revenue"
3. PRESCRIBES specific actions: "Do these 3 things in the next 7 days..."
4. PROJECTS the ROI: "If you activate 20% of cold leads, expect $Y additional revenue"

PRIORITIZATION FRAMEWORK:
- HIGH PRIORITY (2-3 items): Actions that can activate high-value leads in next 7-14 days
  - Focus on contactable leads with highest deal values
  - Quick wins with measurable revenue impact
  - Example ROI projection: "Prioritizing top 50 contactable leads worth $2M could yield $400K closed deals (20% conversion)"

- MEDIUM PRIORITY (2-3 items): Process fixes to prevent future stagnation (30-day timeline)
  - CRM workflow automation
  - Lead qualification criteria
  - Example ROI projection: "Implementing lead scoring could improve contact success rate from {early_metrics.get('contact_success_rate', 0)}% to 35%, saving 120 hours/month"

- LOW PRIORITY (1-2 items): Strategic improvements (60-90 day timeline)
  - Lead source evaluation
  - Sales training programs
  - Example ROI projection: "Improving lead quality could reduce dead lead rate by 40%, worth $X annually"

For each action provide:
- title: Action-oriented with urgency (e.g., "URGENT: Activate 127 high-value contactable leads before they go cold")
- description: Human explanation of WHY this matters and WHAT to do (conversational, 2-3 sentences)
- impact: SPECIFIC ROI projection with numbers (e.g., "Potential revenue: $420K from 20% conversion of $2.1M pipeline segment")
- timeline: Exact timeframe (e.g., "Next 7 days", "By end of month")
- effort: Realistic (e.g., "2 days sales team focus", "4 hours setup + ongoing")
- priority: "high" | "medium" | "low"
- category: "lead_activation" | "process_fix" | "strategic_improvement" | "revenue_recovery"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title with urgency",
    "description": "Conversational explanation with specific context from the data",
    "impact": "Quantified ROI projection with specific numbers and percentages",
    "timeline": "Specific timeframe",
    "effort": "Realistic effort estimate",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    else:
        # STANDARD FUNNEL CONTEXT (when there IS progression)
        durations = funnel_data.get("durations", {})
        stuck_deals = funnel_data.get("stuck_deals", [])
        segments = funnel_data.get("segments", {})
        
        # Build stage conversion details
        stage_conversions_text = ""
        for conversion in conversions.get("stage_conversions", []):
            stage_conversions_text += f"- {conversion['transition']}: {conversion['rate']}% conversion ({conversion['deals_dropped']} deals dropped)\n"
        
        # Build duration analysis
        duration_text = ""
        for stage, stats in durations.items():
            duration_text += f"- {stage}: {stats['avg']} days average (max: {stats['max']} days)\n"
        
        # Build stuck deals summary
        stuck_deals_text = ""
        if stuck_deals:
            total_stuck_value = sum(deal['amount'] for deal in stuck_deals)
            stuck_deals_text = f"- {len(stuck_deals)} deals stuck 30+ days (total value: ₹{total_stuck_value:,.0f})\n"
            stuck_deals_text += f"- Top stuck deal: ₹{stuck_deals[0]['amount']:,.0f} in {stuck_deals[0]['stage']} for {stuck_deals[0]['days_stuck']} days\n"
        
        # Build segment analysis
        segment_text = ""
        if "large_deals" in segments:
            segment_text += f"- Large deals (>₹1M): {segments['large_deals']['conversion']}% conversion vs {segments.get('small_deals', {}).get('conversion', 0)}% for smaller deals\n"
        
        context = f"""
You are a senior sales operations consultant analyzing deal funnel performance for Practus, a consulting company.

FUNNEL OVERVIEW:
- Overall Conversion Rate: {summary.get('overall_conversion_rate', 0)}% (from lead to won)
- Total Deals in Pipeline: {summary.get('total_active_deals', 0)} deals
- Average Sales Cycle: {summary.get('avg_sales_cycle_days', 0)} days

STAGE-BY-STAGE CONVERSION:
{stage_conversions_text}

BOTTLENECKS IDENTIFIED:
- Biggest Drop-off: {summary.get('top_bottleneck', 'No data available')}
- Stuck Deals: {summary.get('stuck_deals_count', 0)} deals stuck 30+ days in pipeline
{stuck_deals_text}

DURATION ANALYSIS:
{duration_text}

SEGMENT ANALYSIS:
{segment_text}

Generate 5-7 actionable items in JSON format. Write in a conversational, business-focused tone that:
1. Speaks directly to the reader ("You should..." vs "Recommend to...")
2. Provides specific numbers and context
3. Explains WHY each action matters
4. Mixes strategic insights with tactical next steps

Structure:
- 2-3 HIGH priority (urgent, immediate impact)
- 2-3 MEDIUM priority (important, 30-day timeline)
- 1-2 LOW priority (strategic, long-term improvements)

For each action provide:
- title: Clear, action-oriented (e.g., "Accelerate 12 deals stuck in proposal stage")
- description: Conversational explanation of the issue and what to do
- impact: Business outcome in real terms (revenue, conversion rate, time saved)
- timeline: Specific (e.g., "Next 7 days", "By end of month")
- effort: Realistic (e.g., "2 hours", "1 day", "Ongoing")
- priority: "high" | "medium" | "low"
- category: "conversion_improvement" | "bottleneck_resolution" | "process_optimization" | "deal_acceleration"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    
    return context

# Cache for funnel actionable items
_funnel_actionable_cache = None

def _generate_funnel_actionable_items(context: str) -> list:
    """Generate actionable items using Gemini LLM for funnel analysis."""
    global _funnel_actionable_cache
    
    # Return cached items if available
    if _funnel_actionable_cache is not None:
        logger.info("Returning cached funnel actionable items")
        return _funnel_actionable_cache
    
    try:
        logger.info("Generating new funnel actionable items (will be cached)")
        
        # Get available Gemini model
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        
        # Generate response
        response = model.generate_content(context)
        
        if not response.text:
            raise Exception("Empty response from Gemini")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            actionable_items = json.loads(json_str)
        else:
            # Fallback: try to parse the entire response
            actionable_items = json.loads(response.text)
        
        # Validate and clean items
        validated_items = []
        for i, item in enumerate(actionable_items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"funnel_act_{i+1:03d}"
                validated_items.append(item)
        
        # Ensure we have at least 3 items
        if len(validated_items) < 3:
            # Add fallback items
            fallback_items = [
                {
                    "id": "funnel_fallback_1",
                    "title": "Review stuck deals immediately",
                    "description": "You have deals stuck in the pipeline for 30+ days. These deals have significantly lower conversion rates. Immediate action: conduct a pipeline review meeting this week to identify which deals to accelerate and which to close as lost.",
                    "impact": "Improve pipeline velocity and focus resources on winnable deals",
                    "timeline": "Next 7 days",
                    "effort": "4 hours",
                    "priority": "high",
                    "category": "deal_acceleration"
                },
                {
                    "id": "funnel_fallback_2", 
                    "title": "Optimize bottleneck stage",
                    "description": "Your funnel analysis shows a significant drop-off at one stage. Focus on improving the conversion rate at this bottleneck by reviewing your sales process and providing additional training or resources.",
                    "impact": "Increase overall conversion rate and pipeline efficiency",
                    "timeline": "Next 30 days",
                    "effort": "2 days",
                    "priority": "medium",
                    "category": "bottleneck_resolution"
                },
                {
                    "id": "funnel_fallback_3",
                    "title": "Implement stage duration tracking",
                    "description": "Set up automated alerts for deals that exceed average stage duration. This will help you identify at-risk deals early and take corrective action before they become stuck.",
                    "impact": "Proactive deal management and improved conversion rates",
                    "timeline": "Next 60 days",
                    "effort": "1 week",
                    "priority": "low",
                    "category": "process_optimization"
                }
            ]
            validated_items.extend(fallback_items[:3-len(validated_items)])
        
        final_items = validated_items[:7]  # Max 7 items
        
        # Cache the results
        _funnel_actionable_cache = final_items
        
        return final_items
        
    except Exception as e:
        logger.error(f"Error generating funnel actionable items with LLM: {str(e)}")
        # Return fallback items
        fallback_items = [
            {
                "id": "funnel_fallback_1",
                "title": "Review stuck deals immediately",
                "description": "You have deals stuck in the pipeline for 30+ days. These deals have significantly lower conversion rates. Immediate action: conduct a pipeline review meeting this week to identify which deals to accelerate and which to close as lost.",
                "impact": "Improve pipeline velocity and focus resources on winnable deals",
                "timeline": "Next 7 days",
                "effort": "4 hours",
                "priority": "high",
                "category": "deal_acceleration"
            },
            {
                "id": "funnel_fallback_2",
                "title": "Optimize bottleneck stage",
                "description": "Your funnel analysis shows a significant drop-off at one stage. Focus on improving the conversion rate at this bottleneck by reviewing your sales process and providing additional training or resources.",
                "impact": "Increase overall conversion rate and pipeline efficiency",
                "timeline": "Next 30 days",
                "effort": "2 days",
                "priority": "medium",
                "category": "bottleneck_resolution"
            },
            {
                "id": "funnel_fallback_3",
                "title": "Implement stage duration tracking",
                "description": "Set up automated alerts for deals that exceed average stage duration. This will help you identify at-risk deals early and take corrective action before they become stuck.",
                "impact": "Proactive deal management and improved conversion rates",
                "timeline": "Next 60 days",
                "effort": "1 week",
                "priority": "low",
                "category": "process_optimization"
            }
        ]
        
        # Cache fallback items too
        _funnel_actionable_cache = fallback_items
        
        return fallback_items

def _build_effort_llm_context(effort_data: dict) -> str:
    """Build comprehensive context for effort tracking LLM prompt."""
    variance = effort_data["variance_summary"]
    breakdown = effort_data["breakdown_analysis"]
    anomalies = effort_data["anomalies"]
    root_causes = effort_data["root_causes"]
    
    # Build variance overview
    variance_text = f"""
VARIANCE OVERVIEW:
- Total Projects Analyzed: {variance.get('total_projects_analyzed', 0)}
- Projects Over Budget: {variance.get('overrun_projects', 0)} ({variance.get('overrun_rate', 0)}%)
- Average Variance: {variance.get('avg_variance_pct', 0)}% overrun
- Total Variance Hours: {variance.get('total_variance_hours', 0):,.0f} hours
"""
    
    # Build top overrun projects
    overrun_text = ""
    if variance.get('at_risk_projects'):
        overrun_text = "\nTOP OVERRUN PROJECTS:\n"
        for i, project in enumerate(variance['at_risk_projects'][:5], 1):
            overrun_text += f"{i}. Project {project.get('Project name', 'Unknown')}: {project.get('Variance_Percentage', 0):.1f}% overrun\n"
            overrun_text += f"   - Planned: {project.get('Budgeted_Hours_Per_Month', 0):.0f} hrs, Actual: {project.get('Actual_Hours', 0):.0f} hrs\n"
            overrun_text += f"   - Status: {project.get('Status', 'Unknown')}\n"
    
    # Build task type analysis
    task_text = ""
    if 'by_task_type' in breakdown and 'top_task_types' in breakdown['by_task_type']:
        task_text = "\nBREAKDOWN BY TASK TYPE:\n"
        for task in breakdown['by_task_type']['top_task_types'][:5]:
            task_text += f"- {task.get('TaskType', 'Unknown')}: {task.get('Total_Hours', 0):.0f} hours across {task.get('Project_Count', 0)} projects\n"
    
    # Build idle time analysis
    idle_text = ""
    if 'by_task_type' in breakdown and 'idle_time_analysis' in breakdown['by_task_type']:
        idle_data = breakdown['by_task_type']['idle_time_analysis']
        if idle_data.get('total_idle_hours', 0) > 0:
            idle_text = f"\nIDLE TIME ANALYSIS:\n"
            idle_text += f"- Total Idle Hours: {idle_data.get('total_idle_hours', 0):.0f} hours\n"
            idle_text += f"- Employees with Idle Time: {idle_data.get('idle_employees', 0)}\n"
            idle_text += f"- Projects with Idle Time: {idle_data.get('idle_projects', 0)}\n"
    
    # Build anomalies section
    anomaly_text = ""
    if anomalies.get('detected_anomalies', 0) > 0:
        anomaly_text = f"\nANOMALIES DETECTED:\n"
        anomaly_text += f"- {anomalies.get('detected_anomalies', 0)} anomalous projects identified\n"
        anomaly_text += f"- Anomaly Rate: {anomalies.get('anomaly_rate', 0):.1f}% of all projects\n"
        if anomalies.get('anomaly_details'):
            anomaly_text += f"- Top Anomaly: {anomalies['anomaly_details'][0].get('explanation', 'Unusual pattern detected')}\n"
    
    # Build root causes
    root_cause_text = ""
    if root_causes.get('overrun_factors'):
        root_cause_text = "\nROOT CAUSES IDENTIFIED:\n"
        for factor in root_causes['overrun_factors'][:3]:
            root_cause_text += f"- {factor.get('factor', 'Unknown')}: {factor.get('description', 'No description')}\n"
    
    if root_causes.get('systemic_issues'):
        root_cause_text += "\nSYSTEMIC ISSUES:\n"
        for issue in root_causes['systemic_issues'][:3]:
            root_cause_text += f"- {issue.get('factor', 'Unknown')}: {issue.get('description', 'No description')}\n"
    
    context = f"""
You are a senior project management consultant analyzing effort variance for Practus, a consulting company.

{variance_text}{overrun_text}{task_text}{idle_text}{anomaly_text}{root_cause_text}

Generate 5-7 actionable items in JSON format. Write in a conversational, business-focused tone that:
1. Speaks directly to the reader ("You should..." vs "Recommend to...")
2. Provides specific numbers and context from the data
3. Explains WHY each action matters
4. Mixes immediate tactical actions with strategic improvements

Structure:
- 2-3 HIGH priority (urgent, immediate impact on overruns)
- 2-3 MEDIUM priority (important, 30-day timeline)
- 1-2 LOW priority (strategic, long-term process improvements)

For each action provide:
- title: Clear, action-oriented (e.g., "Address 5 projects with 40%+ overruns immediately")
- description: Conversational explanation of the issue and what to do
- impact: Business outcome in real terms (hours saved, cost reduction, efficiency gains)
- timeline: Specific (e.g., "Next 7 days", "By end of month")
- effort: Realistic (e.g., "2 hours", "1 day", "Ongoing")
- priority: "high" | "medium" | "low"
- category: "overrun_management" | "resource_optimization" | "estimation_improvement" | "process_enhancement"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    return context

# Cache for effort actionable items
_effort_actionable_cache = None

# Cache for retention actionable items
_retention_actionable_cache = None

# Cache for automation actionable items
_automation_actionable_cache = None

# Cache for hiring actionable items
_hiring_actionable_cache = None

def _generate_effort_actionable_items(context: str) -> list:
    """Generate actionable items using Gemini LLM for effort tracking analysis."""
    global _effort_actionable_cache
    
    # Return cached items if available
    if _effort_actionable_cache is not None:
        logger.info("Returning cached effort actionable items")
        return _effort_actionable_cache
    
    try:
        logger.info("Generating new effort actionable items (will be cached)")
        
        # Get available Gemini model
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        
        # Generate response
        response = model.generate_content(context)
        
        if not response.text:
            raise Exception("Empty response from Gemini")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            actionable_items = json.loads(json_str)
        else:
            # Fallback: try to parse the entire response
            actionable_items = json.loads(response.text)
        
        # Validate and clean items
        validated_items = []
        for i, item in enumerate(actionable_items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"effort_act_{i+1:03d}"
                validated_items.append(item)
        
        # Ensure we have at least 3 items
        if len(validated_items) < 3:
            # Add fallback items
            fallback_items = [
                {
                    "id": "effort_fallback_1",
                    "title": "Review critical overrun projects immediately",
                    "description": "You have projects with significant overruns that need immediate attention. Schedule emergency project review meetings this week to assess the situation, identify root causes, and implement corrective actions.",
                    "impact": "Prevent further cost overruns and improve project delivery",
                    "timeline": "Next 7 days",
                    "effort": "4 hours",
                    "priority": "high",
                    "category": "overrun_management"
                },
                {
                    "id": "effort_fallback_2", 
                    "title": "Optimize resource allocation and reduce idle time",
                    "description": "Your analysis shows significant idle time across resources. Review current project assignments and reallocate underutilized resources to projects that need additional support.",
                    "impact": "Improve resource utilization and reduce project overruns",
                    "timeline": "Next 14 days",
                    "effort": "2 days",
                    "priority": "medium",
                    "category": "resource_optimization"
                },
                {
                    "id": "effort_fallback_3",
                    "title": "Implement better estimation processes",
                    "description": "Set up standardized estimation templates and historical data analysis to improve future project planning accuracy. Include buffer time for complex tasks and skill-level considerations.",
                    "impact": "Reduce future overruns and improve project predictability",
                    "timeline": "Next 30 days",
                    "effort": "1 week",
                    "priority": "low",
                    "category": "estimation_improvement"
                }
            ]
            validated_items.extend(fallback_items[:3-len(validated_items)])
        
        final_items = validated_items[:7]  # Max 7 items
        
        # Cache the results
        _effort_actionable_cache = final_items
        
        return final_items
        
    except Exception as e:
        logger.error(f"Error generating effort actionable items with LLM: {str(e)}")
        # Return fallback items
        fallback_items = [
            {
                "id": "effort_fallback_1",
                "title": "Review critical overrun projects immediately",
                "description": "You have projects with significant overruns that need immediate attention. Schedule emergency project review meetings this week to assess the situation, identify root causes, and implement corrective actions.",
                "impact": "Prevent further cost overruns and improve project delivery",
                "timeline": "Next 7 days",
                "effort": "4 hours",
                "priority": "high",
                "category": "overrun_management"
            },
            {
                "id": "effort_fallback_2", 
                "title": "Optimize resource allocation and reduce idle time",
                "description": "Your analysis shows significant idle time across resources. Review current project assignments and reallocate underutilized resources to projects that need additional support.",
                "impact": "Improve resource utilization and reduce project overruns",
                "timeline": "Next 14 days",
                "effort": "2 days",
                "priority": "medium",
                "category": "resource_optimization"
            },
            {
                "id": "effort_fallback_3",
                "title": "Implement better estimation processes",
                "description": "Set up standardized estimation templates and historical data analysis to improve future project planning accuracy. Include buffer time for complex tasks and skill-level considerations.",
                "impact": "Reduce future overruns and improve project predictability",
                "timeline": "Next 30 days",
                "effort": "1 week",
                "priority": "low",
                "category": "estimation_improvement"
            }
        ]
        
        # Cache fallback items too
        _effort_actionable_cache = fallback_items
        
        return fallback_items

def _build_retention_llm_context(retention_data: dict) -> str:
    """Build comprehensive context for retention analysis LLM prompt."""
    summary = retention_data["retention_summary"]
    segmentation = retention_data["segmentation_analysis"]
    at_risk = retention_data["at_risk_clients"]
    repeat_patterns = retention_data["repeat_patterns"]
    anomalies = retention_data["anomalies"]
    
    # Build context sections
    summary_text = f"""
RETENTION OVERVIEW:
- Total clients analyzed: {summary.get('total_clients_analyzed', 0)}
- At-risk clients: {summary.get('at_risk_clients', 0)} ({summary.get('at_risk_clients', 0)/max(summary.get('total_clients_analyzed', 1), 1)*100:.1f}% of total)
- Repeat business rate: {summary.get('repeat_business_rate', 0):.1f}%
- Average retention score: {summary.get('avg_retention_score', 0):.1f}/100
- Average churn risk: {summary.get('avg_churn_risk', 0):.1f}/100
"""
    
    at_risk_text = ""
    if at_risk and len(at_risk) > 0:
        top_risks = at_risk[:5]
        at_risk_text = f"""
TOP AT-RISK CLIENTS:
"""
        for i, client in enumerate(top_risks, 1):
            at_risk_text += f"- {client.get('Client_Name', 'Unknown')}: {client.get('Churn_Risk_Score', 0):.1f}% risk, {client.get('Deal_Count', 0)} deals, {client.get('Days_Since_Last_Activity', 0)} days inactive\n"
    
    repeat_text = f"""
REPEAT BUSINESS PATTERNS:
- Repeat clients: {repeat_patterns.get('repeat_clients', 0)} out of {repeat_patterns.get('total_clients', 0)}
- High-value repeat clients: {repeat_patterns.get('high_value_repeat', 0)}
- Quick repeaters (≤6 months): {repeat_patterns.get('quick_repeaters', 0)}
- Average time between deals: {repeat_patterns.get('avg_time_between_deals', 0):.0f} days
- Average deals per client: {repeat_patterns.get('avg_deals_per_client', 0):.1f}
"""
    
    segmentation_text = ""
    if segmentation.get('by_industry_size'):
        industry_data = segmentation['by_industry_size']
        if industry_data.get('top_industry'):
            segmentation_text += f"""
CLIENT SEGMENTATION:
- Top performing industry: {industry_data.get('top_industry', 'Unknown')}
- Top size category: {industry_data.get('top_size_category', 'Unknown')}
- Total segments analyzed: {industry_data.get('total_segments', 0)}
"""
    
    anomaly_text = ""
    if anomalies and anomalies.get('total_anomalies', 0) > 0:
        anomaly_text = f"""
ANOMALY DETECTION:
- Total anomalies detected: {anomalies.get('total_anomalies', 0)}
- High-risk anomalies: {anomalies.get('high_risk_anomalies', 0)}
- Average anomaly score: {anomalies.get('avg_anomaly_score', 0):.2f}
"""
        if anomalies.get('anomaly_types'):
            anomaly_text += "Anomaly types:\n"
            for anomaly_type, count in anomalies['anomaly_types'].items():
                anomaly_text += f"- {anomaly_type}: {count} clients\n"
    
    context = f"""
You are a senior client relationship management consultant analyzing client retention for Practus, a consulting company.

{summary_text}{at_risk_text}{repeat_text}{segmentation_text}{anomaly_text}

Generate 5-7 actionable items in JSON format. Write in a conversational, business-focused tone that:
1. Speaks directly to the reader ("You should..." vs "Recommend to...")
2. Provides specific numbers and context from the data
3. Explains WHY each action matters for client retention
4. Mixes immediate tactical actions with strategic improvements

Structure:
- 2-3 HIGH priority (urgent, immediate impact on at-risk clients)
- 2-3 MEDIUM priority (important, 30-day timeline)
- 1-2 LOW priority (strategic, long-term retention improvements)

For each action provide:
- title: Clear, action-oriented (e.g., "Re-engage 5 high-risk clients immediately")
- description: Conversational explanation of the issue and what to do
- impact: Business outcome in real terms (revenue retention, client satisfaction, repeat business)
- timeline: Specific (e.g., "Next 7 days", "By end of month")
- effort: Realistic (e.g., "2 hours", "1 day", "Ongoing")
- priority: "high" | "medium" | "low"
- category: "client_reengagement" | "segment_optimization" | "retention_strategy" | "relationship_building"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    return context

def _build_automation_llm_context(automation_data: dict) -> str:
    """Build comprehensive context for automation analysis LLM prompt."""
    summary = automation_data["automation_summary"]
    top_candidates = automation_data["top_candidates"]
    task_clusters = automation_data["task_clusters"]
    automation_breakdown = automation_data["automation_breakdown"]
    roi_analysis = automation_data["roi_analysis"]
    
    # Build summary text
    summary_text = f"""
AUTOMATION OPPORTUNITY ANALYSIS SUMMARY:
- Total tasks analyzed: {summary.get('total_tasks_analyzed', 0)}
- Automatable tasks: {summary.get('automatable_tasks', 0)} ({summary.get('automation_percentage', 0):.1f}% of all tasks)
- High priority automation candidates: {summary.get('high_priority_tasks', 0)}
- Average automation score: {summary.get('avg_automation_score', 0):.1f}/100
- Total monthly hours: {summary.get('total_monthly_hours', 0):.1f}
- Potential monthly savings: {summary.get('potential_monthly_savings', 0):.1f} hours
- Top automation type: {summary.get('top_automation_type', 'Unknown')}
"""
    
    # Build top candidates text
    candidates_text = "\nTOP AUTOMATION CANDIDATES:\n"
    for i, candidate in enumerate(top_candidates[:5], 1):
        candidates_text += f"""
{i}. {candidate.get('TaskName', 'Unknown Task')}
   - Type: {candidate.get('TaskType', 'Unknown')}
   - Frequency: {candidate.get('Avg_Monthly_Frequency', 0):.1f} times/month
   - Hours per entry: {candidate.get('Avg_Hours_Per_Entry', 0):.1f}
   - Monthly hours: {candidate.get('Monthly_Hours', 0):.1f}
   - Automation score: {candidate.get('Automation_Score', 0):.1f}/100
   - Priority: {candidate.get('Automation_Priority', 'Unknown')}
   - Suggested approach: {candidate.get('Automation_Type', 'Unknown')}
   - Estimated savings: {candidate.get('Estimated_Monthly_Savings', 0):.1f} hours/month
"""
    
    # Build task clusters text
    clusters_text = "\nTASK CLUSTERS (ML-DISCOVERED PATTERNS):\n"
    for cluster in task_clusters[:5]:
        clusters_text += f"""
- Cluster {cluster.get('cluster_id', 0)}: {cluster.get('task_count', 0)} tasks
  - Avg frequency: {cluster.get('avg_frequency', 0):.1f} times/month
  - Total hours: {cluster.get('total_hours', 0):.1f}/month
  - Avg automation score: {cluster.get('avg_automation_score', 0):.1f}/100
  - Sample tasks: {', '.join(cluster.get('sample_tasks', []))}
"""
    
    # Build automation breakdown text
    breakdown_text = "\nAUTOMATION TYPE BREAKDOWN:\n"
    for breakdown in automation_breakdown:
        breakdown_text += f"""
- {breakdown.get('Automation_Type', 'Unknown')}: {breakdown.get('Task_Count', 0)} tasks
  - Total hours: {breakdown.get('Total_Hours', 0):.1f}/month
  - Avg automation score: {breakdown.get('Avg_Score', 0):.1f}/100
"""
    
    # Build ROI analysis text
    roi_text = f"""
ROI ANALYSIS:
- Total monthly hours: {roi_analysis.get('total_monthly_hours', 0):.1f}
- Total potential savings: {roi_analysis.get('total_potential_savings', 0):.1f} hours/month
- Automation percentage: {roi_analysis.get('automation_percentage', 0):.1f}% of total effort
"""
    
    context = f"""
You are a senior automation consultant analyzing task automation opportunities for Practus, a consulting company.

{summary_text}{candidates_text}{clusters_text}{breakdown_text}{roi_text}

Generate 5-7 actionable items in JSON format. Write in a conversational, business-focused tone that:
1. Speaks directly to the reader ("You should..." vs "Recommend to...")
2. Provides specific numbers and context from the data
3. Explains WHY each automation opportunity matters for efficiency
4. Mixes immediate tactical actions with strategic automation initiatives

Structure:
- 2-3 HIGH priority (immediate automation wins with high ROI)
- 2-3 MEDIUM priority (important automation projects, 30-day timeline)
- 1-2 LOW priority (strategic automation initiatives, long-term)

For each action provide:
- title: Clear, action-oriented (e.g., "Automate status report generation with Python script")
- description: Conversational explanation of the automation opportunity and implementation approach
- impact: Business outcome in real terms (hours saved, efficiency gains, cost reduction)
- timeline: Specific (e.g., "Next 2 weeks", "By end of month")
- effort: Realistic (e.g., "1 day", "1 week", "Ongoing")
- priority: "high" | "medium" | "low"
- category: "rpa_automation" | "api_integration" | "process_optimization" | "workflow_automation"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    return context

def _generate_retention_actionable_items(context: str) -> list:
    """Generate actionable items using Gemini LLM for retention analysis."""
    global _retention_actionable_cache
    
    # Return cached items if available
    if _retention_actionable_cache is not None:
        logger.info("Returning cached retention actionable items")
        return _retention_actionable_cache
    
    try:
        logger.info("Generating new retention actionable items (will be cached)")
        
        # Get available Gemini model
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        
        # Generate response
        response = model.generate_content(context)
        
        if not response.text:
            raise Exception("Empty response from Gemini")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            actionable_items = json.loads(json_str)
        else:
            # Fallback: try to parse the entire response
            actionable_items = json.loads(response.text)
        
        # Validate and clean items
        validated_items = []
        for i, item in enumerate(actionable_items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"retention_act_{i+1:03d}"
                validated_items.append(item)
        
        # Ensure we have at least 3 items
        if len(validated_items) < 3:
            logger.warning("Generated fewer than 3 actionable items, using fallback")
            validated_items = _get_retention_fallback_items()
        
        # Cache the results
        _retention_actionable_cache = validated_items
        logger.info(f"Generated and cached {len(validated_items)} retention actionable items")
        
        return validated_items
        
    except Exception as e:
        logger.error(f"Error generating retention actionable items: {str(e)}")
        return _get_retention_fallback_items()

def _get_retention_fallback_items() -> list:
    """Fallback actionable items for retention analysis."""
    return [
        {
            "id": "retention_act_001",
            "title": "Re-engage top 5 at-risk clients immediately",
            "description": "Contact clients with highest churn risk scores within the next 7 days. Schedule follow-up calls to understand their current needs and address any concerns.",
            "impact": "Prevent potential revenue loss and improve client satisfaction",
            "timeline": "Next 7 days",
            "effort": "2 hours per client",
            "priority": "high",
            "category": "client_reengagement"
        },
        {
            "id": "retention_act_002",
            "title": "Implement client health scoring system",
            "description": "Create a systematic approach to track client engagement, satisfaction, and retention risk on a monthly basis.",
            "impact": "Proactive identification of at-risk clients and improved retention rates",
            "timeline": "By end of month",
            "effort": "1 week setup",
            "priority": "medium",
            "category": "retention_strategy"
        },
        {
            "id": "retention_act_003",
            "title": "Develop segment-specific retention strategies",
            "description": "Create tailored engagement approaches for different client segments based on industry, size, and behavioral patterns.",
            "impact": "Higher retention rates and increased repeat business",
            "timeline": "Next 30 days",
            "effort": "Ongoing",
            "priority": "medium",
            "category": "segment_optimization"
        }
    ]

def _build_hiring_llm_context(hiring_data: dict) -> str:
    """Build comprehensive context for hiring analysis LLM prompt."""
    summary = hiring_data["hiring_summary"]
    workload = hiring_data["workload_analysis"]
    skill_analysis = hiring_data["skill_analysis"]
    hiring_forecast = hiring_data["hiring_forecast"]
    cost_analysis = hiring_data["cost_analysis"]
    
    # Build summary text
    summary_text = f"""
HIRING FORECASTING ANALYSIS SUMMARY:
- Total employees needed: {summary.get('total_employees_needed', 0)}
- Total hiring cost: ${summary.get('total_hiring_cost', 0):,.0f}
- Current capacity utilization: {summary.get('current_capacity_utilization', 0):.1f}%
- Hiring priority: {summary.get('hiring_priority', 'Low')}
- Recommended timeline: {summary.get('recommended_timeline', 'No immediate need')}
- ROI percentage: {summary.get('roi_percentage', 0):.1f}%
- Confidence level: {summary.get('confidence_level', 'Low')}
"""
    
    # Build workload analysis text
    workload_text = f"""
WORKLOAD ANALYSIS:
- Average monthly hours: {workload.get('avg_monthly_hours', 0):.0f}
- Average employees: {workload.get('avg_employees', 0):.1f}
- Average hours per employee: {workload.get('avg_hours_per_employee', 0):.1f}
- Capacity utilization: {workload.get('capacity_utilization', 0):.1f}%
- Hours trend: {workload.get('hours_trend', 0):.1f}% per month
- Employee trend: {workload.get('employee_trend', 0):.1f}% per month
- Months analyzed: {workload.get('total_months_analyzed', 0)}
"""
    
    # Build skill analysis text
    skill_gaps = skill_analysis.get('skill_gaps', [])
    high_demand_skills = skill_analysis.get('high_demand_skills', [])
    
    skill_text = f"""
SKILL ANALYSIS:
- Total skill types: {skill_analysis.get('total_skill_types', 0)}
- High demand skills: {', '.join(high_demand_skills[:5]) if high_demand_skills else 'None identified'}
- Critical skill gaps: {len(skill_gaps)}
"""
    
    if skill_gaps:
        skill_text += "\nSkill Gap Details:\n"
        for gap in skill_gaps[:3]:
            skill_text += f"- {gap.get('skill', 'Unknown')}: {gap.get('demand_level', 'Unknown')} demand, {gap.get('avg_hours_per_employee', 0):.1f} hrs/employee\n"
    
    # Build hiring forecast text
    forecast_text = "\nHIRING SCENARIOS:\n"
    for scenario_key, scenario in hiring_forecast.items():
        if scenario_key != 'overall_recommendation':
            forecast_text += f"""
- {scenario.get('name', 'Unknown Scenario')}:
  - Employees needed: {scenario.get('additional_employees_needed', 0)}
  - Timeline: {scenario.get('timeline', 'Unknown')}
  - Priority: {scenario.get('priority', 'Unknown')}
  - Reasoning: {scenario.get('reasoning', 'No reasoning provided')}
"""
    
    # Build cost analysis text
    cost_text = f"""
COST ANALYSIS:
- Total hiring cost: ${cost_analysis.get('total_hiring_cost', 0):,.0f}
- Cost per employee: ${cost_analysis.get('cost_per_employee', 0):,.0f}
- Potential revenue increase: ${cost_analysis.get('potential_revenue_increase', 0):,.0f}
- ROI percentage: {cost_analysis.get('roi_percentage', 0):.1f}%
- Payback period: {cost_analysis.get('payback_period_months', 0)} months
"""
    
    context = f"""
You are a senior HR and business strategy consultant analyzing hiring and cost forecasting for Practus, a consulting company.

{summary_text}{workload_text}{skill_text}{forecast_text}{cost_text}

Generate 5-7 actionable items in JSON format. Write in a conversational, business-focused tone that:
1. Speaks directly to the reader ("You should..." vs "Recommend to...")
2. Provides specific numbers and context from the data
3. Explains WHY each hiring decision matters for business growth
4. Mixes immediate tactical actions with strategic hiring initiatives

Structure:
- 2-3 HIGH priority (urgent hiring needs, critical skill gaps)
- 2-3 MEDIUM priority (important hiring decisions, 30-90 day timeline)
- 1-2 LOW priority (strategic hiring, long-term workforce planning)

For each action provide:
- title: Clear, action-oriented (e.g., "Hire 3 senior developers within 60 days")
- description: Conversational explanation of the hiring need and business impact
- impact: Business outcome in real terms (revenue growth, capacity increase, skill coverage)
- timeline: Specific (e.g., "Next 30 days", "By end of quarter")
- effort: Realistic (e.g., "2 weeks", "1 month", "Ongoing")
- priority: "high" | "medium" | "low"
- category: "immediate_hiring" | "skill_based_hiring" | "capacity_planning" | "cost_optimization"

Return ONLY valid JSON array format:
[
  {{
    "title": "Action title",
    "description": "Detailed description",
    "impact": "Expected business impact",
    "timeline": "Timeline",
    "effort": "Effort required",
    "priority": "high|medium|low",
    "category": "category_name"
  }}
]
"""
    return context

def _generate_hiring_actionable_items(context: str) -> list:
    """Generate actionable items using Gemini LLM for hiring analysis."""
    global _hiring_actionable_cache
    
    # Return cached items if available
    if _hiring_actionable_cache is not None:
        logger.info("Returning cached hiring actionable items")
        return _hiring_actionable_cache
    
    try:
        # Generate using Gemini
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(context)
        response_text = response.text.strip()
        
        # Clean response text
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        import json
        items = json.loads(response_text)
        
        # Validate and add IDs
        validated_items = []
        for i, item in enumerate(items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"hiring_act_{i+1:03d}"
                validated_items.append(item)
        
        # Cache the results
        _hiring_actionable_cache = validated_items
        logger.info(f"Generated {len(validated_items)} hiring actionable items using Gemini")
        return validated_items
        
    except Exception as e:
        logger.error(f"Error generating hiring actionable items with Gemini: {str(e)}")
        # Return fallback items
        fallback_items = _get_hiring_fallback_items()
        _hiring_actionable_cache = fallback_items
        return fallback_items

def _get_hiring_fallback_items() -> list:
    """Fallback actionable items for hiring analysis."""
    return [
        {
            "id": "hiring_act_001",
            "title": "Hire 2-3 senior developers to address capacity constraints",
            "description": "Based on current workload analysis, you need additional senior developers to handle the growing project demand and maintain quality standards.",
            "impact": "Increase development capacity by 40% and reduce project delivery risks",
            "timeline": "Next 60 days",
            "effort": "4-6 weeks recruitment process",
            "priority": "high",
            "category": "immediate_hiring"
        },
        {
            "id": "hiring_act_002",
            "title": "Implement skill-based hiring strategy for high-demand areas",
            "description": "Focus recruitment efforts on specific skill gaps identified in your analysis to ensure optimal resource allocation and project success.",
            "impact": "Improve project delivery quality and reduce skill bottlenecks",
            "timeline": "Next 90 days",
            "effort": "2-3 months strategic planning",
            "priority": "medium",
            "category": "skill_based_hiring"
        },
        {
            "id": "hiring_act_003",
            "title": "Develop workforce capacity planning framework",
            "description": "Create a systematic approach to forecast hiring needs based on project pipeline and capacity utilization trends.",
            "impact": "Proactive hiring decisions and better resource planning",
            "timeline": "Next 30 days",
            "effort": "2 weeks framework development",
            "priority": "medium",
            "category": "capacity_planning"
        },
        {
            "id": "hiring_act_004",
            "title": "Optimize hiring costs through strategic recruitment channels",
            "description": "Analyze and optimize recruitment costs by focusing on high-ROI channels and reducing time-to-hire for critical positions.",
            "impact": "Reduce hiring costs by 20-30% while maintaining quality",
            "timeline": "Next 45 days",
            "effort": "3-4 weeks analysis and implementation",
            "priority": "low",
            "category": "cost_optimization"
        }
    ]

def _generate_automation_actionable_items(context: str) -> list:
    """Generate actionable items using Gemini LLM for automation analysis."""
    global _automation_actionable_cache
    
    # Return cached items if available
    if _automation_actionable_cache is not None:
        logger.info("Returning cached automation actionable items")
        return _automation_actionable_cache
    
    try:
        # Generate using Gemini
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(context)
        response_text = response.text.strip()
        
        # Clean response text
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        import json
        items = json.loads(response_text)
        
        # Validate and add IDs
        validated_items = []
        for i, item in enumerate(items):
            if isinstance(item, dict) and all(key in item for key in ['title', 'description', 'impact', 'timeline', 'effort', 'priority', 'category']):
                item['id'] = f"automation_act_{i+1:03d}"
                validated_items.append(item)
        
        # Cache the results
        _automation_actionable_cache = validated_items
        logger.info(f"Generated {len(validated_items)} automation actionable items using Gemini")
        return validated_items
        
    except Exception as e:
        logger.error(f"Error generating automation actionable items with Gemini: {str(e)}")
        # Return fallback items
        fallback_items = _get_automation_fallback_items()
        _automation_actionable_cache = fallback_items
        return fallback_items

def _get_automation_fallback_items() -> list:
    """Fallback actionable items for automation analysis."""
    return [
        {
            "id": "automation_act_001",
            "title": "Automate status report generation with Python script",
            "description": "Create an automated script to generate weekly status reports by pulling data from your project management tools. This will save significant manual effort and ensure consistency.",
            "impact": "Save 20+ hours per month on report generation and improve accuracy",
            "timeline": "Next 2 weeks",
            "effort": "3-5 days development",
            "priority": "high",
            "category": "api_integration"
        },
        {
            "id": "automation_act_002",
            "title": "Implement RPA for data entry tasks",
            "description": "Deploy Robotic Process Automation (RPA) bots to handle repetitive data entry tasks like timesheet updates, client information entry, and invoice processing.",
            "impact": "Reduce manual data entry by 60-80% and eliminate human errors",
            "timeline": "By end of month",
            "effort": "1-2 weeks setup",
            "priority": "high",
            "category": "rpa_automation"
        },
        {
            "id": "automation_act_003",
            "title": "Create automated project milestone tracking",
            "description": "Set up automated alerts and tracking for project milestones using your existing project management tools to reduce manual monitoring overhead.",
            "impact": "Improve project visibility and reduce manual tracking by 15+ hours/month",
            "timeline": "Next 3 weeks",
            "effort": "1 week configuration",
            "priority": "medium",
            "category": "workflow_automation"
        },
        {
            "id": "automation_act_004",
            "title": "Automate client communication workflows",
            "description": "Implement automated email sequences and follow-up reminders for client communications to ensure consistent touchpoints and reduce manual coordination.",
            "impact": "Improve client satisfaction and save 10+ hours/month on communication management",
            "timeline": "Next 4 weeks",
            "effort": "2 weeks setup",
            "priority": "medium",
            "category": "process_optimization"
        },
        {
            "id": "automation_act_005",
            "title": "Develop automated resource allocation system",
            "description": "Create a system to automatically match project requirements with available resources based on skills, availability, and workload to optimize team utilization.",
            "impact": "Improve resource utilization by 25% and reduce manual allocation time",
            "timeline": "Next 6 weeks",
            "effort": "3-4 weeks development",
            "priority": "low",
            "category": "api_integration"
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

