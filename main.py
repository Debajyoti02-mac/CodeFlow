from pathlib import Path
import time
from agent import graph
from auth import create_token, get_current_user, hash_password, verify_password
from database import SQL_base, User, create_db
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphRecursionError
from logger import logger
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="API_system")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Serve UI
@app.get("/", response_class=HTMLResponse)
def serve_ui():
  with open("index.html", "r", encoding="utf-8") as f:
    return f.read()

# Request Models
class API(BaseModel):
  id: int
  question: str
class ChatRequest(BaseModel):
  question: str
  limit: int = 100

class LoginRequest(BaseModel):
  email: str
  password: str
class RegisterRequest(BaseModel):
  email: str
  password: str

# PUT /ask
@app.put("/ask")
def update(
    response: API,
    user_id: int = Depends(get_current_user),
    db=Depends(create_db),
):
  question = (
      db.query(SQL_base)
      .filter(SQL_base.id == response.id, SQL_base.user_id == user_id)
      .first()
  )

  if not question:
    raise HTTPException(status_code=404, detail="Question not found")

  question.question = response.question
  db.commit()
  db.refresh(question)

  return {"updated": question}


# DELETE /ask
@app.delete("/ask")
def delete_question(
    id: int, user_id: int = Depends(get_current_user), db=Depends(create_db)
):
  question = (
      db.query(SQL_base)
      .filter(SQL_base.id == id, SQL_base.user_id == user_id)
      .first()
  )

  if not question:
    raise HTTPException(status_code=404, detail="Question not found")

  deleted_id = question.id
  db.delete(question)
  db.commit()

  return {"status": "delete", "delete": deleted_id}


# GET /ask
@app.get("/ask")
def fetch(user_id: int = Depends(get_current_user), db=Depends(create_db)):
  try:
    questions = (
        db.query(SQL_base).filter(SQL_base.user_id == user_id).all()
    )
    return [
        {
            "id": q.id,
            "answer": q.answer,
            "question": q.question,
            "user_id": q.user_id,
        }
        for q in questions
    ]
  except Exception as e:
    logger.error(f"Fetch error: {e}")
    raise HTTPException(status_code=500, detail=str(e))


# POST /chat
@app.post("/chat")
@limiter.limit("10/minute")
def asking(
    request: Request,
    data: ChatRequest,
    user_id: int = Depends(get_current_user),
    db=Depends(create_db),
):
  logger.info("Chat request received")
  try:
    logger.info("Agent started")
    start = time.time()

    try:
      result = graph.invoke(
          {
              "messages": [HumanMessage(content=data.question)],
              "user_id": user_id,
          },
          config={"recursion_limit": 25},
      )
      answer = result["messages"][-1].content
    except GraphRecursionError:
      logger.warning(
          f"Graph recursion limit reached for question: {data.question}"
      )
      answer = (
          "The agent reached the maximum step limit without concluding. "
          "Please rephrase or ask a more specific question."
      )

    end = time.time()
    logger.info(f"Time taken {end - start:.2f}s")

    new_question = SQL_base(
        user_id=user_id,
        limit=data.limit,
        question=data.question,
        answer=answer,
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return {
        "id": new_question.id,
        "question": new_question.question,
        "answer": new_question.answer,
    }

  except Exception as e:
    logger.error(f"Agent error: {e}")
    raise HTTPException(status_code=500, detail=str(e))


# GET /api/workspace/download
@app.get("/api/workspace/download")
def download_file(filename: str, user_id: int = Depends(get_current_user)):
  user_workspace = (
      Path("workspace") / str(user_id) / "generated"
  ).resolve()
  user_workspace.mkdir(parents=True, exist_ok=True)

  target = (user_workspace / filename).resolve()

  if not target.is_relative_to(user_workspace):
    raise HTTPException(status_code=403, detail="Access denied")

  if not target.exists() or target.is_dir():
    raise HTTPException(status_code=404, detail="File not found")

  return FileResponse(
      path=target, filename=target.name, media_type="application/octet-stream"
  )


# POST /login
@app.post("/login")
def login(data: LoginRequest, db=Depends(create_db)):
  user = db.query(User).filter(User.email == data.email).first()

  if not user or not verify_password(data.password, user.password):
    raise HTTPException(status_code=401, detail="Invalid email or password")

  return {"access_token": create_token(user.id), "token_type": "bearer"}


# POST /register
@app.post("/register")
def register(data: RegisterRequest, db=Depends(create_db)):
  existing = db.query(User).filter(User.email == data.email).first()
  if existing:
    raise HTTPException(status_code=400, detail="User already exists")

  user = User(email=data.email, password=hash_password(data.password))
  db.add(user)
  db.commit()
  db.refresh(user)

  return {"access_token": create_token(user.id), "token_type": "bearer"}

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
import shutil

# POST /api/workspace/upload
@app.post("/api/workspace/upload")
async def upload_file(
    file: UploadFile = File(...), user_id: int = Depends(get_current_user)
):
  user_workspace = (
      Path("workspace") / str(user_id) / "generated"
  ).resolve()
  user_workspace.mkdir(parents=True, exist_ok=True)

  file_path = (user_workspace / file.filename).resolve()

  # Prevent path traversal
  if not file_path.is_relative_to(user_workspace):
    raise HTTPException(status_code=403, detail="Access denied")

  try:
    with open(file_path, "wb") as buffer:
      shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "filename": file.filename,
        "message": f"File '{file.filename}' uploaded successfully.",
    }
  except Exception as e:
    logger.error(f"Upload error: {e}")
    raise HTTPException(status_code=500, detail="Failed to save file")
