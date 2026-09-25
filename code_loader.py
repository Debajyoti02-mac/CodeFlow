# Basic path loader 
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter 
import chromadb

def load_files():
    files = []
    for file in Path(".").glob("*.py"):
        files.append({
            "file": str(file),
            "content": file.read_text()
        })
    return files

text_spliter = RecursiveCharacterTextSplitter(chunk_size=1000 , chunk_overlap=150)

if __name__ == "__main__":
    docs = load_files()

    chunks = []
    
    for doc in docs:
        file_chunks = text_spliter.split_text(doc['content'])
        
        for chunk in file_chunks:
            chunks.append({
                'file':doc['file'],
                'content':chunk
            })

    client = chromadb.PersistentClient(path="./CodeFlowDB")

    collection = client.get_or_create_collection(
    name="code"
    )
    documents = [chunk["content"] for chunk in chunks]

    ids = [str(i) for i in range(len(chunks))]

    metadatas = [
    {"file": chunk["file"]}
    for chunk in chunks
]

    collection.upsert(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)
    results = collection.query(
    query_texts=["where is git commit implemented?"],
    n_results=3
)

    print(results["documents"])

    print("Stored:", collection.count())
    print("total chunks ", len(chunks))
    print(chunks[0])
        


