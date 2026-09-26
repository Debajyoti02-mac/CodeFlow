from langchain_core.messages import HumanMessage
from agent import graph


def test_code_search():
  result = graph.invoke(
      {
          "messages": [
              HumanMessage(content="Where is the database session created?")
          ],
          "user_id": 1,
      },
      config={"recursion_limit": 8},
  )

  last_message = result["messages"][-1].content
  assert last_message
  assert "database" in last_message.lower() or "session" in last_message.lower()
