from fastapi import FastAPI , HTTPException , Depends , Request 
from database import SQL_base , create_db
from agent import graph
from pydantic import BaseModel
from langchain_core.messages import HumanMessage 
from logger import logger

# Rate limiter 
from slowapi import Limiter 
from slowapi.util import get_remote_address 
from slowapi.errors import RateLimitExceeded 
from slowapi import _rate_limit_exceeded_handler 

limiter = Limiter(key_func=get_remote_address)

# Conection build 
app = FastAPI(title = "API_system")
app.state.limiter = limiter 
app.add_exception_handler(RateLimitExceeded , _rate_limit_exceeded_handler)

# Data Define 
class API(BaseModel):
    question: str = None
    user_id: int = None
    id: int = None
    limit: int = 100
#put method    
@app.put("/ask")
def update(response:API , db=Depends(create_db)):
    question = db.query(SQL_base).filter(SQL_base.id==response.id).first()
    if not question:
        raise HTTPException(status_code=400 , detail="question doesnot find out")
    question.question = response.question
    db.commit()
    db.refresh(question)
    return {'updated':question}

#delete method
@app.delete("/ask")  
def delete_question(id : int , db=Depends(create_db)):
    question = db.query(SQL_base).filter(SQL_base.id==id).first() 
    if not question :
        raise HTTPException(status_code=400,detail="question not in database")
    delete = question.id 
    db.delete(question)
    db.commit()
    
    return {
        'status':'delete',
        'delete':delete
    }


#Get method     
@app.get("/ask")
def fetch(db=Depends(create_db)):
    try:
        question = db.query(SQL_base).all()
        return [{
            'id':q.id , 'answer':q.answer , 'question':q.question ,'user_id':q.user_id}
            for q in question
        ]
    except Exception as e :
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=400 , detail=str(e))
    

import time 
# Post connection 
@app.post("/chat")
@limiter.limit("10/minute")
def asking(request:Request , response:API , db=Depends(create_db)):
    
    logger.info("chat request recived")
    try:
        logger.info("Agent started")
        start = time.time()
        result = graph.invoke({
        'messages':[HumanMessage(content=(response.question))]
    })
        end = time.time()
        logger.info(f'time taken {end-start:.2f}s')
        answer = result['messages'][-1].content 
        
    
        new_question  = SQL_base(
            user_id = response.user_id , 
            limit = response.limit , 
            question = response.question,
            answer = answer
        )
        
        db.add(new_question)
        db.commit()
        db.refresh(new_question)
        
        return {
            'id':new_question.id,
            'question':new_question.question,
            'answer':new_question.answer
            }
        
    except Exception as e :
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=400 , detail=str(e))