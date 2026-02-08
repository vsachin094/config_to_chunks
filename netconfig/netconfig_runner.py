import os
import argparse
import json
from datetime import datetime

if __package__ is None or __package__ == "":
    import sys
    import os as _os
    sys.path.append(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))
    from netconfig.core.config_prep import prepare_configs
    from netconfig.core.chunk_builder import convert_config_to_chunks
    from netconfig.utils.embeddings import embed_chunks
else:
    from .core.config_prep import prepare_configs
    from .core.chunk_builder import convert_config_to_chunks
    from .utils.embeddings import embed_chunks

DEFAULT_CONFIG_DIR = "configs"
DEFAULT_CHUNK_DIR = "config_chunks"
DEFAULT_FAISS_DIR = "index/faiss"
DEFAULT_MONGO_URI = "mongodb://localhost:27017"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_APP_CONFIG = os.path.join(REPO_ROOT, "config.yaml")

def collect_chunk_files(chunks_dir: str):
    files = sorted([f for f in os.listdir(chunks_dir) if f.endswith(".json")])
    if not files:
        raise SystemExit(f"No .json chunk files found in {chunks_dir}")
    return [os.path.join(chunks_dir, f) for f in files]

def prepare_out_dir(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    removed = 0
    for name in os.listdir(out_dir):
        if name.endswith(".json"):
            os.remove(os.path.join(out_dir, name))
            removed += 1
    if removed:
        print(f"[INFO] Cleared {removed} existing chunk files from {out_dir}")

def load_chunks(path: str):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Invalid chunks format in {path}: expected a list")
    return data

def load_app_config(path: str = DEFAULT_APP_CONFIG):
    if not os.path.isfile(path):
        return {}
    try:
        import yaml
    except Exception:
        raise SystemExit("PyYAML is required to read config.yaml. Install pyyaml.")
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit("config.yaml must contain a top-level mapping.")
    return data

def derive_section_type(section, chunk_type):
    if chunk_type == "global" or not section:
        return "global"
    return section.split()[0].lower()

def normalize_chunks(chunks, device):
    for idx, c in enumerate(chunks):
        meta = c.setdefault("metadata", {})
        meta.setdefault("device", device)
        if "chunk_index" not in meta:
            meta["chunk_index"] = idx
        if "section_type" not in meta:
            meta["section_type"] = derive_section_type(meta.get("section"), meta.get("chunk_type"))
        if "chunk_id" not in meta:
            meta["chunk_id"] = f"{meta['device']}|{meta.get('section','global')}|{meta['chunk_index']}"
    return chunks

def run_chunking(args) -> str:
    out_dir = args.out_dir
    prepare_out_dir(out_dir)
    prepared = prepare_configs(
        config=args.config,
        config_dir=args.config_dir,
        os_type=args.os_type,
        os_map_path=args.os_map,
        detect_os=args.detect_os
    )
    for item in prepared:
        chunks = convert_config_to_chunks(item["device"], item["os_type"], item["text"], out_dir=out_dir)
        print(f"[OK] {item['device']}: {len(chunks)} chunks written to {out_dir}")
    return out_dir

def run_mongo(args, chunks_dir: str):
    if __package__ is None or __package__ == "":
        from netconfig.utils.mongo_writer import MongoStore
    else:
        from .utils.mongo_writer import MongoStore
    files = collect_chunk_files(chunks_dir)
    store = MongoStore(mongo_uri=args.mongo_uri, mongo_db=args.mongo_db, dry_run=args.dry_run)
    devices_collection = args.collection
    chunks_collection = f"{args.collection}_chunks"
    for path in files:
        device = os.path.splitext(os.path.basename(path))[0]
        chunks = normalize_chunks(load_chunks(path), device)
        os_type = chunks[0].get("metadata", {}).get("os_type") if chunks else None
        embeddings = embed_chunks(chunks, args.embedding_model) if args.embed else None

        device_doc = {"updated_at": datetime.utcnow()}
        if os_type:
            device_doc["os_type"] = os_type
        store.upsert(devices_collection, {"_id": device}, device_doc)

        store.delete_many(chunks_collection, {"device": device})
        docs = []
        for i, c in enumerate(chunks):
            meta = c.get("metadata", {})
            doc = {
                "device": meta.get("device", device),
                "os_type": meta.get("os_type"),
                "section": meta.get("section"),
                "section_type": meta.get("section_type"),
                "chunk_type": meta.get("chunk_type"),
                "chunk_index": meta.get("chunk_index"),
                "chunk_id": meta.get("chunk_id"),
                "content": c.get("content", ""),
                "created_at": datetime.utcnow()
            }
            if embeddings is not None:
                doc["embedding"] = embeddings[i]
            docs.append(doc)
        store.insert_many(chunks_collection, docs)

        if store.dry_run:
            print(f"[DRY-RUN] {device}: {len(chunks)} chunks ready (embed={bool(args.embed)})")
        else:
            print(f"[OK] {device}: {len(chunks)} chunks stored (embed={bool(args.embed)})")
    store.close()

def run_faiss(args, chunks_dir: str):
    try:
        from langchain.schema import Document
    except Exception:
        raise SystemExit("langchain is required for FAISS. Install langchain.")

    if __package__ is None or __package__ == "":
        from netconfig.utils.faiss_index import FaissIndex
    else:
        from .utils.faiss_index import FaissIndex

    docs = []
    for path in collect_chunk_files(chunks_dir):
        for c in load_chunks(path):
            docs.append(Document(page_content=c["content"], metadata=c.get("metadata", {})))
    index = FaissIndex.from_documents(docs, args.embedding_model)
    os.makedirs(args.faiss_dir, exist_ok=True)
    index.save(args.faiss_dir)
    print(f"[DONE] FAISS index created at {args.faiss_dir}")

def main():
    argp = argparse.ArgumentParser(description="NetConfig: chunk configs and enable optional outputs via flags.")
    argp.add_argument("--config", help="Path to a single config file")
    argp.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Directory of .cfg files")
    argp.add_argument("--os-type", help="OS type (ios, iosxe, iosxr, nxos, eos)")
    argp.add_argument("--os-map", help="JSON map of filename/device -> os_type")
    argp.add_argument("--detect-os", action="store_true", help="Auto-detect OS type when not provided")
    argp.add_argument("--out-dir", default=DEFAULT_CHUNK_DIR, help="Output directory for chunks")

    argp.add_argument("--mongo-dump", "--dump-mongo", action="store_true", help="Write chunks to MongoDB")
    argp.add_argument("--mongo-db", default=None, help="Mongo database name")
    argp.add_argument("--collection", "--mongo-collection", default=None, help="Base collection name (chunks stored in <name>_chunks)")
    argp.add_argument("--embed", action="store_true", help="Create embeddings (Mongo and/or FAISS)")
    argp.add_argument("--dry-run", action="store_true", help="Preview Mongo writes without writing")

    argp.add_argument("--dump-vector", action="store_true", help="Build FAISS index from chunks")
    argp.add_argument("--faiss-dir", default=DEFAULT_FAISS_DIR, help="FAISS output directory")
    argp.add_argument("--embedding-model", default=None, help="Embedding model name")

    args = argp.parse_args()

    app_config = load_app_config()
    mongo_cfg = app_config.get("mongo", {}) if isinstance(app_config.get("mongo", {}), dict) else {}
    args.mongo_db = args.mongo_db or mongo_cfg.get("db") or "net_config"
    args.collection = args.collection or mongo_cfg.get("collection") or "network_config"
    args.mongo_uri = mongo_cfg.get("uri") or DEFAULT_MONGO_URI

    if args.embed and not (args.mongo_dump or args.dump_vector):
        print("[WARN] --embed set but no output selected. Use --mongo-dump and/or --dump-vector.")

    if args.mongo_dump and not args.mongo_uri and not args.dry_run:
        raise SystemExit("Missing MongoDB URI. Set it in config.yaml.")

    # Always chunk from configs first (default behavior)
    chunks_dir = run_chunking(args)

    if args.mongo_dump:
        run_mongo(args, chunks_dir)

    if args.dump_vector:
        if not args.embed:
            print("[INFO] --dump-vector will create embeddings for FAISS.")
        run_faiss(args, chunks_dir)

if __name__ == "__main__":
    main()
