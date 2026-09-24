from fastapi import FastAPI 
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
    
# Post conection 
@app.post("/ask")
def asking(response:API):
    try:
        result = graph.invoke({
        'messages':[HumanMessage(content=(response.question))]
    })
    
        return {
            'answer':result['messages'][-1].content
        }
    except Exception as e :
        return str(e)