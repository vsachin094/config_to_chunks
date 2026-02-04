import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import MongoClient

from ..chunk_utils import embed_chunks

DEFAULT_CHUNK_DIR = "config_chunks"
DEFAULT_CONFIG_DIR = "configs"
DEFAULT_DB = "net_config"
DEFAULT_DEVICES_COL = "devices"
DEFAULT_CHUNKS_COL = "chunks"

def load_chunks(path: str) -> List[Dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Invalid chunks format in {path}: expected a list")
    return data

def device_from_file(path: str) -> str:
    name = os.path.basename(path)
    if name.endswith(".json"):
        name = name[:-5]
    return name

def read_raw_config(configs_dir: str, device: str) -> Optional[str]:
    if not configs_dir:
        return None
    cfg_path = os.path.join(configs_dir, f"{device}.cfg")
    if not os.path.isfile(cfg_path):
        return None
    with open(cfg_path) as f:
        return f.read()

def derive_section_type(section: Optional[str], chunk_type: Optional[str]) -> str:
    if chunk_type == "global" or not section:
        return "global"
    return section.split()[0].lower()

def normalize_chunks(chunks: List[Dict[str, Any]], device: str) -> List[Dict[str, Any]]:
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

def upsert_device(devices_col, device: str, os_type: Optional[str], raw_config: Optional[str], dry_run: bool):
    if dry_run:
        print(f"[DRY-RUN] upsert device {device} (os={os_type})")
        return
    update = {"updated_at": datetime.utcnow()}
    if os_type:
        update["os_type"] = os_type
    if raw_config is not None:
        update["raw_config"] = raw_config
    devices_col.update_one({"_id": device}, {"$set": update}, upsert=True)

def replace_chunks(chunks_col, device: str, chunks: List[Dict[str, Any]], embeddings=None, dry_run: bool = False):
    if dry_run:
        print(f"[DRY-RUN] replace chunks for {device}: {len(chunks)} chunks")
        return
    chunks_col.delete_many({"device": device})
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

    if docs:
        chunks_col.insert_many(docs, ordered=False)

def process_chunks_file(path: str, configs_dir: Optional[str], embed: bool, embed_model: Optional[str], devices_col, chunks_col, dry_run: bool, mongo_uri: Optional[str] = None, mongo_db: str = DEFAULT_DB, devices_col_name: str = DEFAULT_DEVICES_COL, chunks_col_name: str = DEFAULT_CHUNKS_COL):
    device = device_from_file(path)
    chunks = normalize_chunks(load_chunks(path), device)
    os_type = chunks[0].get("metadata", {}).get("os_type") if chunks else None
    raw_config = read_raw_config(configs_dir, device)
    embeddings = embed_chunks(chunks, embed_model) if embed else None

    if devices_col is None and chunks_col is None and not dry_run:
        if not mongo_uri:
            raise SystemExit("Missing MongoDB URI. Use --mongo-uri or set MONGO_URI.")
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        devices_col = db[devices_col_name]
        chunks_col = db[chunks_col_name]

    upsert_device(devices_col, device, os_type, raw_config, dry_run)
    replace_chunks(chunks_col, device, chunks, embeddings, dry_run=dry_run)
    if dry_run:
        print(f"[DRY-RUN] {device}: {len(chunks)} chunks ready (embed={bool(embed)})")
    else:
        print(f"[OK] {device}: {len(chunks)} chunks stored (embed={bool(embed)})")

def main():
    argp = argparse.ArgumentParser(description="Write chunk JSON into MongoDB (optional embeddings).")
    argp.add_argument("--chunks", help="Path to a single chunks JSON file")
    argp.add_argument("--chunks-dir", default=DEFAULT_CHUNK_DIR, help="Directory of chunks JSON files")
    argp.add_argument("--configs-dir", default=None, help="Optional configs dir to attach raw_config")
    argp.add_argument("--mongo-uri", default=os.getenv("MONGO_URI", ""), help="MongoDB URI (or set MONGO_URI)")
    argp.add_argument("--mongo-db", default=DEFAULT_DB, help="Mongo database name")
    argp.add_argument("--devices-col", default=DEFAULT_DEVICES_COL, help="Devices collection name")
    argp.add_argument("--chunks-col", default=DEFAULT_CHUNKS_COL, help="Chunks collection name")
    argp.add_argument("--embed", action="store_true", help="Create embeddings for each chunk")
    argp.add_argument("--embedding-model", default=None, help="Embedding model name")
    argp.add_argument("--dry-run", action="store_true", help="Preview actions without writing to MongoDB")
    args = argp.parse_args()

    if not args.mongo_uri and not args.dry_run:
        raise SystemExit("Missing MongoDB URI. Use --mongo-uri or set MONGO_URI.")

    if args.dry_run:
        devices_col = None
        chunks_col = None
    else:
        client = MongoClient(args.mongo_uri)
        db = client[args.mongo_db]
        devices_col = db[args.devices_col]
        chunks_col = db[args.chunks_col]

    if args.chunks:
        process_chunks_file(
            args.chunks,
            args.configs_dir,
            args.embed,
            args.embedding_model,
            devices_col,
            chunks_col,
            args.dry_run
        )
        return

    files = sorted([f for f in os.listdir(args.chunks_dir) if f.endswith(".json")])
    if not files:
        raise SystemExit(f"No .json chunk files found in {args.chunks_dir}")

    for file in files:
        process_chunks_file(
            os.path.join(args.chunks_dir, file),
            args.configs_dir,
            args.embed,
            args.embedding_model,
            devices_col,
            chunks_col,
            args.dry_run
        )

if __name__ == "__main__":
    main()
