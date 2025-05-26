from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os, datetime, base64
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loveconcierge.db")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# App setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    whatsapp_number = Column(String)
    tier = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AdviceLog(Base):
    __tablename__ = "advice_logs"
    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    goal = Column(String)
    advice = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic schemas
class UserCreate(BaseModel):
    name: str
    email: str
    whatsapp_number: str
    tier: str

class MessageRequest(BaseModel):
    situation: str
    email: str

# Routes
@app.get("/")
def read_root():
    return {"msg": "Hello from Love Concierge Backend"}

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="User already exists")
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return {"msg": "User registered", "user": db_user.name}

@app.post("/generate-message")
def suggest_message(request: MessageRequest, db: Session = Depends(get_db)):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a dating assistant."},
            {"role": "user", "content": f"I need help with: {request.situation}"}
        ]
    )
    advice = response.choices[0].message["content"]
    db.add(AdviceLog(user_email=request.email, goal=request.situation, advice=advice))
    db.commit()
    return {"message": advice}

@app.post("/upload-convo")
def upload_convo(
    file: UploadFile = File(...),
    goal: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    content = base64.b64encode(file.file.read()).decode("utf-8")
    prompt = f"This is a screenshot from a dating app. The user's goal is: '{goal}'. Provide advice and a message suggestion."
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "You are a dating coach reviewing a screenshot."},
            {"role": "user", "content": prompt, "image": {"data": content, "mime_type": file.content_type}}
        ]
    )
    advice = response.choices[0].message["content"]
    db.add(AdviceLog(user_email=email, goal=goal, advice=advice))
    db.commit()
    return {"advice": advice}

@app.get("/history/{email}")
def get_history(email: str, db: Session = Depends(get_db)):
    entries = db.query(AdviceLog).filter_by(user_email=email).all()
    return [
        {
            "goal": e.goal,
            "advice": e.advice,
            "timestamp": e.timestamp.isoformat()
        } for e in entries
    ]

