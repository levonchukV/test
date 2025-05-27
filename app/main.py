from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from . import models
from .database import engine, get_db
from .wait_for_db import wait_for_db

if not wait_for_db():
    raise Exception("Could not connect to database")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class TaskBase(BaseModel):
    text: str
    completed: bool
    user_id: str

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
    
    response = templates.TemplateResponse(
        "index.html",
        {"request": request, "user_id": user_id}
    )
    
    if not request.cookies.get("user_id"):
        response.set_cookie(
            key="user_id",
            value=user_id,
            httponly=True,
            max_age=365 * 24 * 60 * 60,  # 1 year
            samesite="lax"
        )
    
    return response

@app.get("/api/tasks")
async def get_tasks(user_id: str, db: Session = Depends(get_db)):
    tasks = db.query(models.Task).filter(models.Task.user_id == user_id).all()
    return tasks

@app.post("/api/tasks")
async def create_task(text: str = Form(...), user_id: str = Form(...), db: Session = Depends(get_db)):
    task = models.Task(
        id=str(uuid.uuid4()),
        text=text,
        completed=False,
        user_id=user_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: str, user_id: str = Form(...), completed: bool = Form(...), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.completed = completed
    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"} 