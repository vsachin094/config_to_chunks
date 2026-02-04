import os
import json
import argparse
from typing import List

from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

DEFAULT_CHUNK_DIR = "config_chunks"
DEFAULT_INDEX_DIR = "index/faiss"

def load_documents(chunks_dir: str) -> List[Document]:
    docs = []
    files = sorted([f for f in os.listdir(chunks_dir) if f.endswith(".json")])
    if not files:
        raise SystemExit(f"No .json chunk files found in {chunks_dir}")
    for file in files:
        with open(os.path.join(chunks_dir, file)) as f:
            for c in json.load(f):
                docs.append(Document(page_content=c["content"], metadata=c.get("metadata", {})))
    return docs

def main():
    argp = argparse.ArgumentParser(description="Build FAISS index from chunk JSON files.")
    argp.add_argument("--chunks-dir", default=DEFAULT_CHUNK_DIR, help="Directory of chunks JSON files")
    argp.add_argument("--faiss-dir", default=DEFAULT_INDEX_DIR, help="FAISS output directory")
    argp.add_argument("--embedding-model", default=None, help="Embedding model name")
    args = argp.parse_args()

    docs = load_documents(args.chunks_dir)
    embed_kwargs = {}
    if args.embedding_model:
        embed_kwargs["model"] = args.embedding_model
    store = FAISS.from_documents(docs, OpenAIEmbeddings(**embed_kwargs))
    os.makedirs(args.faiss_dir, exist_ok=True)
    store.save_local(args.faiss_dir)
    print(f"[DONE] FAISS index created at {args.faiss_dir} with {len(docs)} docs")

if __name__ == "__main__":
    main()
