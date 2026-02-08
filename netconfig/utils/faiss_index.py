from typing import List, Optional

from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

class FaissIndex:
    def __init__(self, store: FAISS, embedder: OpenAIEmbeddings):
        self.store = store
        self.embedder = embedder

    @classmethod
    def from_documents(cls, docs: List[Document], embedding_model: Optional[str] = None):
        embed_kwargs = {}
        if embedding_model:
            embed_kwargs["model"] = embedding_model
        embedder = OpenAIEmbeddings(**embed_kwargs)
        store = FAISS.from_documents(docs, embedder)
        return cls(store, embedder)

    @classmethod
    def load(cls, faiss_dir: str, embedding_model: Optional[str] = None):
        embed_kwargs = {}
        if embedding_model:
            embed_kwargs["model"] = embedding_model
        embedder = OpenAIEmbeddings(**embed_kwargs)
        store = FAISS.load_local(faiss_dir, embedder)
        return cls(store, embedder)

    def save(self, faiss_dir: str):
        self.store.save_local(faiss_dir)

    def add_documents(self, docs: List[Document]):
        self.store.add_documents(docs)

    def rebuild(self, docs: List[Document]):
        self.store = FAISS.from_documents(docs, self.embedder)

    def delete_ids(self, ids: List[str]):
        if hasattr(self.store, "delete"):
            return self.store.delete(ids)
        raise NotImplementedError("Delete is not supported by this FAISS wrapper/version.")

    def similarity_search(self, query: str, k: int = 8):
        return self.store.similarity_search(query, k=k)
