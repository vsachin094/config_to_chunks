import argparse
import json
from typing import TypedDict, List, Dict, Any
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

DEFAULT_INDEX_DIR = "index/faiss"
DEFAULT_K = 8

class GraphState(TypedDict):
    question: str
    retrieved_docs: List[Document]
    response: Dict[str, Any]

def load_store(index_dir: str):
    return FAISS.load_local(index_dir, OpenAIEmbeddings())

def retrieve_node_factory(index_dir: str, k: int):
    def retrieve_node(state: GraphState):
        store = load_store(index_dir)
        state["retrieved_docs"] = store.similarity_search(state["question"], k=k)
        return state

    return retrieve_node

def reason_node(state: GraphState):
    llm = ChatOpenAI(temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """Use ONLY the configs below. Return STRICT JSON.
{ "found": true|false, "results": [] }
Question: {question}
Configs: {configs}
""")
    configs_text = "\n".join(d.page_content for d in state["retrieved_docs"])
    resp = llm.invoke(prompt.format_messages(question=state["question"], configs=configs_text))
    try:
        parsed = json.loads(resp.content)
    except:
        parsed = {"found": False, "results": []}
    state["response"] = {"query": state["question"], **parsed}
    return state

def build_graph(index_dir: str, k: int):
    g = StateGraph(GraphState)
    g.add_node("retrieve", retrieve_node_factory(index_dir, k))
    g.add_node("reason", reason_node)
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "reason")
    return g.compile()

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description="LangGraph test app for NetConfig retrieval.")
    argp.add_argument("--index-dir", default=DEFAULT_INDEX_DIR, help="FAISS index directory")
    argp.add_argument("--k", type=int, default=DEFAULT_K, help="Number of docs to retrieve")
    args = argp.parse_args()

    app = build_graph(args.index_dir, args.k)
    while True:
        q = input("Ask: ")
        if q == "exit":
            break
        print(json.dumps(app.invoke({"question": q})["response"], indent=2))
