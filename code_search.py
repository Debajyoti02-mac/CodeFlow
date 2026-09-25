import chromadb
from langchain_core.tools import tool
from logger import logger


# Connect to existing ChromaDB
client = chromadb.PersistentClient(
    path="./CodeFlowDB"
)

collection = client.get_or_create_collection(
    name="code"
)


@tool
def code_search(query: str):
    """
    Search the CodeFlow codebase for relevant code.

    Use this tool whenever the user asks about:
    - where code is implemented
    - where a function or class is defined
    - how something works in the codebase
    - finding code inside project files
    """
    logger.info(f"Code search called: {query}")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        output = []

        for document, metadata in zip(documents, metadatas):
            output.append(
                f"File: {metadata['file']}\n"
                f"Code:\n{document}"
            )

        return "\n\n---\n\n".join(output)

    except Exception as e:
        return f"Code search error: {e}"
    
if __name__ == "__main__":
    result = code_search.invoke({
        "query": "where is git commit implemented?"
    })

    print(result)