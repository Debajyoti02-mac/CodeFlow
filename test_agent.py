from langchain_core.messages import HumanMessage
from agent import graph


def test_code_search():
    result = graph.invoke({
        "messages": [
            HumanMessage(
                content="Where is the database session created?"
            )
        ]
    })

    assert result["messages"][-1].content