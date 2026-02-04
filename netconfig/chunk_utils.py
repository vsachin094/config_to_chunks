from typing import List, Dict, Any

from .parsers import get_parser

try:
    from langchain.embeddings import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

def derive_section_type(section: str, chunk_type: str) -> str:
    if chunk_type == "global" or not section:
        return "global"
    return section.split()[0].lower()

def build_chunks(device: str, os_type: str, text: str) -> List[Dict[str, Any]]:
    parser = get_parser(os_type)
    chunks = parser.chunk(device, text)
    for idx, c in enumerate(chunks):
        c["metadata"]["os_type"] = os_type
        c["metadata"]["chunk_index"] = idx
        c["metadata"]["section_type"] = derive_section_type(
            c["metadata"].get("section"),
            c["metadata"].get("chunk_type")
        )
        c["metadata"]["chunk_id"] = f"{device}|{c['metadata'].get('section','global')}|{idx}"
    return chunks

def embed_chunks(chunks: List[Dict[str, Any]], model: str = None) -> List[List[float]]:
    if OpenAIEmbeddings is None:
        raise RuntimeError("OpenAIEmbeddings not available. Install langchain and openai.")
    kwargs = {}
    if model:
        kwargs["model"] = model
    embedder = OpenAIEmbeddings(**kwargs)
    texts = [c["content"] for c in chunks]
    return embedder.embed_documents(texts)
