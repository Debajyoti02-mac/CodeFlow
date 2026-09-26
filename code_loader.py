from pathlib import Path
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)


def load_code_chunks():
  chunks = []
  # Recursively find .py files, ignoring virtual environments and cache
  for file in Path(".").rglob("*.py"):
    if any(p in file.parts for p in (".venv", "venv", "__pycache__")):
      continue
    try:
      content = file.read_text(encoding="utf-8", errors="ignore")
      for i, piece in enumerate(splitter.split_text(content)):
        chunks.append({
            "id": f"{file}_{i}",
            "file": str(file),
            "content": piece,
        })
    except Exception:
      pass
  return chunks


if __name__ == "__main__":
  chunks = load_code_chunks()
  if not chunks:
    print("No Python files found.")
    exit()

  client = chromadb.PersistentClient(path="./CodeFlowDB")
  collection = client.get_or_create_collection(name="code")

  collection.upsert(
      ids=[c["id"] for c in chunks],
      documents=[c["content"] for c in chunks],
      metadatas=[{"file": c["file"]} for c in chunks],
  )

  print(f"Indexed {len(chunks)} chunks into CodeFlowDB.")
