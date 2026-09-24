import os
import numexpr as ne
from langchain_core.tools import tool
# Calculator Tool
@tool
def calculator(expression: str):
    """Calculate a mathematical expression."""
    try:
        result = ne.evaluate(expression)
        return result.item()
    except Exception as e:
        return str(e)


# File Operation Tool
@tool
def file_handler(filename: str,operation: str,content: str = ""):
    """
    Handles basic file operations such as create, read, append, and delete.
    """
    try:
        if operation == "read":
            with open(filename, "r") as file:
                return file.read()
        elif operation == "create":
            with open(filename, "w") as file:
                file.write(content)
            return f"File created: {filename}"
        elif operation == "append":
            with open(filename, "a") as file:
                file.write(content)
            return f"Content added to: {filename}"
        elif operation == "delete":
            if os.path.exists(filename):
                os.remove(filename)
                return f"File deleted: {filename}"
            return "File not found."
        else:
            return "Invalid operation."
    except Exception as e:
        return str(e)

# List of file return 
@tool
def list_files(path: str = "workspace"):
    """List all files and folders inside the given directory."""
    try:
        return os.listdir(path)
    except Exception as e:
        return str(e)
    
# terminal add 
import subprocess 
from langchain_core.tools import tool 

@tool 
def terminal(command:str):
    """Execute a terminal command inside the CodeFlow workspace.""" 
    try : 
        result = subprocess.run(
            command , 
            shell=True , 
            capture_output=True , 
            text=True , 
            cwd="workspace",
            timeout=30
        )
        
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return str(e)
    
# LLM connction 
from langchain_groq import ChatGroq 
import os 
from dotenv import load_dotenv 
load_dotenv()
key = os.getenv('GROQ_API_KEY')
LLM = ChatGroq(model="openai/gpt-oss-120b",api_key=key)

LLM.invoke("hii ?").content 

# LLM conection with the langGraph 
from langgraph.graph import START , StateGraph , END 
from langgraph.graph.message import add_messages , Annotated 
from typing import TypedDict 
tools = [calculator,file_handler,list_files,terminal]
# State create  
class state(TypedDict):
    messages : Annotated[list,add_messages]

# llm state contention  
tool_blind = LLM.bind_tools(tools=tools)

#tool connection 
def tool_connection(state:state):
    response = tool_blind.invoke(state['messages'])
    return {'messages':response} 
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

Builder = StateGraph(state)

Builder.add_node("conection", tool_connection)
Builder.add_node("tools", ToolNode(tools))

Builder.add_edge(START, "conection")

Builder.add_conditional_edges(
    "conection",
    tools_condition
)

Builder.add_edge("tools", "conection")

graph = Builder.compile()
graph

from langchain_core.messages import HumanMessage
result = graph.invoke({
    "messages": [
        HumanMessage(
            content="Create workspace/file.txt containing: Hello CodeFlow"
        )
    ]
})

print(result)