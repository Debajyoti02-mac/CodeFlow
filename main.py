from fastapi import FastAPI , HTTPException , Depends 
from database import SQL_base , create_db
from agent import graph
from pydantic import BaseModel
from langchain_core.messages import HumanMessage 

# Conection build 
app = FastAPI(title = "API_system")

# Data Define 
class API(BaseModel):
    question : str 
    user_id : int = None 
    limit : int = 100 
    
@app.get("/ask")
def fetch(response:API , db=Depends(create_db)):
    try:
        question = db.query(SQL_base).all()
        return [{
            'id':q.id , 'answer':q.answer , 'question':q.question ,'user_id':q.user_id}
            for q in question
        ]
    except Exception as e :
        return HTTPException(status_code=400 , detail=str(e))
    

# Post conection 
@app.post("/chat")
def asking(response:API):
    try:
        result = graph.invoke({
        'messages':[HumanMessage(content=(response.question))]
    })
    
        return {
            'answer':result['messages'][-1].content
        }
    except Exception as e :
        return HTTPException(status_code=400 , details=str(e))