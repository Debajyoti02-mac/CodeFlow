import os
import shlex
import subprocess
from pathlib import Path
from typing import Annotated, Literal, TypedDict
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import InjectedState, ToolNode, tools_condition
import numexpr as ne
from langchain_community.tools import DuckDuckGoSearchResults
from code_search import code_search
from git_tools import (
    git_add,
    git_commit,
    git_diff,
    git_log,
    git_push,
    git_status,
)
from logger import logger 

# Ensure base workspace exists
Path("workspace").mkdir(parents=True, exist_ok=True) 

# 1. Constants 
SENSITIVE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
}

ALLOWED_COMMANDS = {
    "ls",
    "pwd",
    "cat",
    "echo",
    "mkdir",
    "touch",
    "python",
}
# 1. Websearch 
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

ddg_search = DuckDuckGoSearchResults()


@tool
def web_search(query: str):
  """Search the web for up-to-date information, news, documentation, or facts

  not found in the local workspace.
  """
  try:
    results = ddg_search.run(query)
    return results if results else "No web results found."
  except Exception as e:
    return f"Web search error: {str(e)}"


# 2. Calculator Tool
@tool
def calculator(expression: str):
  """Calculate a mathematical expression."""
  logger.info(f"the calculator called : {expression}")
  try:
    result = ne.evaluate(expression)
    return result.item()
  except Exception as e:
    logger.info(f"the error is :{str(e)}")
    return str(e)

# 3. File Operation Tool
@tool
def file_handler(
    filename: str,
    operation: Literal["create", "read", "append", "delete"],
    content: str = "",
    user_id: Annotated[int, InjectedState("user_id")] = None,
):
  """Manage files for the authenticated user.

  Args:
      filename: Name or relative path of the file.
      operation: Action to perform ('create', 'read', 'append', or 'delete').
      content: Text to write (used for 'create' and 'append').
  """
  try:
    if user_id is None:
      return "User authentication required."

    user_workspace = (
        Path("workspace") / str(user_id) / "generated"
    ).resolve()
    user_workspace.mkdir(parents=True, exist_ok=True)

    path = (user_workspace / filename).resolve()

    if not path.is_relative_to(user_workspace):
      return "Access denied."

    if path.name in SENSITIVE_FILES:
      return "Access denied: sensitive file"

    if operation == "read":
      if not path.exists():
        return f"File not found: {filename}"

          # Handle PDF files
      if path.suffix.lower() == ".pdf":
        try:
          reader = PdfReader(path)
          extracted = "\n".join(
                  [page.extract_text() or "" for page in reader.pages]
              )
          return (
                  extracted.strip()
              if extracted.strip()
              else "PDF contains no readable text."
              )
        except Exception as e:
              return f"Error reading PDF: {e}"

          # Handle text files
      with open(path, "r", encoding="utf-8", errors="ignore") as file:
        data = file.read()
        return data if data else "File is empty."


    elif operation == "create":
      with open(path, "w") as file:
        file.write(content)
      return f"File created: {filename}"

    elif operation == "append":
      with open(path, "a") as file:
        file.write(content)
      return f"Content added: {filename}"

    elif operation == "delete":
      if path.exists():
        path.unlink()
        return f"File deleted: {filename}"
      return "File not found."

    return "Invalid operation."

  except Exception as e:
    logger.error(f"File tool error: {e}")
    return str(e)

# 4. List Files Tool
@tool
def list_files(user_id: Annotated[int, InjectedState("user_id")] = None):
  """List all files uploaded in the user's workspace."""
  if user_id is None:
    return "User authentication required."

  user_workspace = Path("workspace") / str(user_id) / "generated"
  if not user_workspace.exists():
    return "No files uploaded yet."

  files = [f for f in os.listdir(user_workspace) if not f.startswith(".")]
  return (
      f"Files in user workspace: {files}"
      if files
      else "No files in user workspace."
  )



# 5. Terminal Tool
def is_safe_command(command: str):
  return ".." not in command and not command.startswith("/")


def is_sensitive_file(path: str):
  return Path(path).name in SENSITIVE_FILES


@tool
def terminal(command: str):
  """Execute a terminal command inside the CodeFlow workspace."""
  logger.info(f"Terminal tool called: {command}")

  try:
    parts = shlex.split(command)
    if not parts:
      return "Empty command."

    if parts[0] not in ALLOWED_COMMANDS:
      logger.warning(f"Blocked terminal command: {command}")
      return f"Command not allowed: {parts[0]}"

    if not is_safe_command(command):
      logger.warning(f"Blocked unsafe command: {command}")
      return "Access denied: unsafe path"

    for part in parts[1:]:
      if is_sensitive_file(part):
        logger.warning(f"Blocked sensitive file access: {part}")
        return "Access denied: sensitive file"

    result = subprocess.run(
        parts, capture_output=True, text=True, cwd="workspace", timeout=30
    )

    logger.info("Terminal tool completed")
    output = (result.stdout or "").strip()
    errors = (result.stderr or "").strip()

    if output:
      return output
    if errors:
      return errors
    return "Command executed successfully (no output)."

  except Exception as e:
    logger.error(f"Terminal tool error: {e}")
    return str(e)

# 6. LLM Setup
load_dotenv()
key = os.getenv("GROQ_API_KEY")
LLM = ChatGroq(model="openai/gpt-oss-120b", api_key=key)

tools = [
    calculator,
    file_handler,
    list_files,
    terminal,
    git_status,
    git_diff,
    git_log,
    git_add,
    git_commit,
    git_push,
    code_search,
    web_search
]


# 7. State and Graph
class State(TypedDict):
  messages: Annotated[list, add_messages]
  user_id: int


tool_bound = LLM.bind_tools(tools=tools)
from langchain_core.messages import SystemMessage
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are an assistant with access to user workspace files. "
        "When the user asks to read, review, or summarize 'my file' or 'my pdf' without specifying a name, "
        "always call list_files first to find what they uploaded, then call file_handler with operation='read'."
    )
)

def tool_connection(state: State):
  logger.info("Tool connection started")

  # Add SYSTEM_PROMPT to the front of the messages list
  messages = [SYSTEM_PROMPT] + state["messages"]

  response = tool_bound.invoke(messages)
  logger.info("tool connection complete")
  return {"messages": [response]}


Builder = StateGraph(State)
Builder.add_node("connection", tool_connection)
Builder.add_node("tools", ToolNode(tools))

Builder.add_edge(START, "connection")
Builder.add_conditional_edges("connection", tools_condition)
Builder.add_edge("tools", "connection")

graph = Builder.compile()

# 8. Execution with recursion_limit to stop loops
if __name__ == "__main__":
  response = graph.invoke(
      {
          "messages": [
              HumanMessage(
                  content=(
                      "Create a file called test_auth.py containing"
                      " print('hello')"
                  )
              )
          ],
          "user_id": 6,
      },
      config={"recursion_limit": 10},
  )

  print(response["messages"][-1].content)
