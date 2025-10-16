from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./practus.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

class DataSource(Base):
    __tablename__ = "datasources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    file_path = Column(String)
    row_count = Column(Integer)
    status = Column(String, default="loaded")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime)

class AgentInsightDB(Base):
    __tablename__ = "agent_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    agent_type = Column(String)
    insight_data = Column(Text)
    timestamp = Column(DateTime)

class ActionItemDB(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    problem_id = Column(Integer)
    title = Column(String)
    description = Column(Text)
    priority = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime)

class ActionOutcomeDB(Base):
    __tablename__ = "action_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    action_item_id = Column(Integer)
    outcome = Column(Text)
    timestamp = Column(DateTime)

class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    quality_score = Column(Float)
    issues = Column(Text)
    uploaded_at = Column(DateTime)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
