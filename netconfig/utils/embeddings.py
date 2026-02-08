from typing import List, Dict, Any, Optional

try:
    from langchain.embeddings import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

def embed_chunks(chunks: List[Dict[str, Any]], model: Optional[str] = None) -> List[List[float]]:
    if OpenAIEmbeddings is None:
        raise RuntimeError("OpenAIEmbeddings not available. Install langchain and openai.")
    kwargs = {}
    if model:
        kwargs["model"] = model
    embedder = OpenAIEmbeddings(**kwargs)
    texts = [c["content"] for c in chunks]
    return embedder.embed_documents(texts)
