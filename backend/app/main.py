import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, String, ForeignKey, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from pwdlib import PasswordHash

DATABASE_URL=os.environ.get("DATABASE_URL","postgresql+psycopg://planbig:planbig_dev@localhost:5432/planbig")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(engine)
password_hash=PasswordHash.recommended()
SESSION_COOKIE="planbig_session"
SESSION_DAYS=7

class Base(DeclarativeBase):pass
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120))
    email:Mapped[str]=mapped_column(String(320),unique=True,index=True)
    password_digest:Mapped[str]=mapped_column(String(255))
    role:Mapped[str]=mapped_column(String(20),default="customer")
class LoginSession(Base):
    __tablename__="login_sessions"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))

class RegisterInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    email:EmailStr
    password:str=Field(min_length=12,max_length=128)
    role:Literal["customer","provider"]="customer"
class LoginInput(BaseModel):
    email:EmailStr
    password:str

app=FastAPI(title="Plan Big API",version="0.1.0")
def db_session():
    with SessionLocal() as db:yield db
def public_user(user:User):
    return {"id":user.id,"name":user.name,"email":user.email,"role":user.role}
def token_digest(token:str)->str:
    return hashlib.sha256(token.encode()).hexdigest()
def set_session(response:Response,db:Session,user:User):
    token=secrets.token_urlsafe(48)
    db.add(LoginSession(user_id=user.id,token_hash=token_digest(token),expires_at=datetime.now(timezone.utc)+timedelta(days=SESSION_DAYS)))
    db.commit()
    response.set_cookie(SESSION_COOKIE,token,httponly=True,secure=os.environ.get("COOKIE_SECURE","false").lower()=="true",samesite="lax",max_age=SESSION_DAYS*86400,path="/")
def current_user(request:Request,db:Session=Depends(db_session)):
    token=request.cookies.get(SESSION_COOKIE)
    if not token:raise HTTPException(401,"Not authenticated")
    session=db.scalar(select(LoginSession).where(LoginSession.token_hash==token_digest(token)))
    if session is None or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401,"Session expired")
    user=db.get(User,session.user_id)
    if user is None:raise HTTPException(401,"User not found")
    return user
@app.get("/api/v1/health")
def health():return {"status":"ok","service":"Plan Big"}
@app.post("/api/v1/auth/register",status_code=201)
def register(payload:RegisterInput,response:Response,db:Session=Depends(db_session)):
    email=str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email==email)) is not None:raise HTTPException(409,"Email already registered")
    user=User(name=payload.name.strip(),email=email,password_digest=password_hash.hash(payload.password),role=payload.role)
    db.add(user)
    try:db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409,"Unable to register account")
    db.refresh(user)
    set_session(response,db,user)
    return public_user(user)
@app.post("/api/v1/auth/login")
def login(payload:LoginInput,response:Response,db:Session=Depends(db_session)):
    user=db.scalar(select(User).where(User.email==str(payload.email).lower()))
    if user is None or not password_hash.verify(payload.password,user.password_digest):
        raise HTTPException(401,"Invalid email or password")
    set_session(response,db,user)
    return public_user(user)
@app.get("/api/v1/auth/me")
def me(user:User=Depends(current_user)):return public_user(user)
@app.post("/api/v1/auth/logout")
def logout(request:Request,response:Response,db:Session=Depends(db_session)):
    token=request.cookies.get(SESSION_COOKIE)
    if token:
        session=db.scalar(select(LoginSession).where(LoginSession.token_hash==token_digest(token)))
        if session:db.delete(session);db.commit()
    response.delete_cookie(SESSION_COOKIE,path="/")
    return {"message":"Logged out"}
