import os
import argparse

from .chunk_configs import load_os_map, resolve_os_type, process_file as chunk_process_file
from .merge_chunks import (
    process_file as merge_process_file,
    DEFAULT_OUT_DIR as MERGE_DEFAULT_OUT_DIR
)

DEFAULT_CONFIG_DIR = "configs"
DEFAULT_CHUNK_DIR = "config_chunks"
DEFAULT_MERGE_OUT_DIR = MERGE_DEFAULT_OUT_DIR
DEFAULT_FAISS_DIR = "index/faiss"

def collect_chunk_files(chunks_dir: str):
    files = sorted([f for f in os.listdir(chunks_dir) if f.endswith(".json")])
    if not files:
        raise SystemExit(f"No .json chunk files found in {chunks_dir}")
    return [os.path.join(chunks_dir, f) for f in files]

def run_chunking(args) -> str:
    os_map = load_os_map(args.os_map) if args.os_map else None
    out_dir = args.out_dir

    if args.config:
        os_type = args.os_type or resolve_os_type(
            os_map,
            os.path.basename(args.config),
            os.path.splitext(os.path.basename(args.config))[0]
        )
        detect = args.detect_os and not os_type
        chunk_process_file(args.config, os_type, out_dir, detect=detect)
        return out_dir

    cfg_dir = args.config_dir or DEFAULT_CONFIG_DIR
    files = sorted([f for f in os.listdir(cfg_dir) if f.endswith(".cfg")])
    if not files:
        raise SystemExit(f"No .cfg files found in {cfg_dir}")

    if args.os_type:
        for file in files:
            chunk_process_file(os.path.join(cfg_dir, file), args.os_type, out_dir)
        return out_dir

    if os_map:
        for file in files:
            device = os.path.splitext(file)[0]
            os_type = resolve_os_type(os_map, file, device)
            if not os_type and args.detect_os:
                chunk_process_file(os.path.join(cfg_dir, file), None, out_dir, detect=True)
                continue
            if not os_type:
                raise SystemExit(f"Missing os_type for {file} in --os-map (or use --detect-os)")
            chunk_process_file(os.path.join(cfg_dir, file), os_type, out_dir)
        return out_dir

    if args.detect_os:
        for file in files:
            chunk_process_file(os.path.join(cfg_dir, file), None, out_dir, detect=True)
        return out_dir

    print("[WARN] No os_type provided. Using generic parser for all configs.")
    for file in files:
        chunk_process_file(os.path.join(cfg_dir, file), "generic", out_dir)
    return out_dir

def run_mongo(args, chunks_dir: str):
    from pymongo import MongoClient
    from .utils.mongo_writer import process_chunks_file as mongo_process_chunks_file
    files = collect_chunk_files(chunks_dir)
    if args.dry_run:
        devices_col = None
        chunks_col = None
    else:
        client = MongoClient(args.mongo_uri)
        db = client[args.mongo_db]
        devices_col = db[args.devices_col]
        chunks_col = db[args.chunks_col]
    for path in files:
        mongo_process_chunks_file(
            path,
            args.mongo_configs_dir,
            args.embed,
            args.embedding_model,
            devices_col,
            chunks_col,
            args.dry_run,
            mongo_uri=args.mongo_uri,
            mongo_db=args.mongo_db,
            devices_col_name=args.devices_col,
            chunks_col_name=args.chunks_col
        )

def run_faiss(args, chunks_dir: str):
    try:
        from langchain.embeddings import OpenAIEmbeddings
        from langchain.vectorstores import FAISS
    except Exception:
        raise SystemExit("OpenAIEmbeddings not available. Install langchain and openai.")

    from .utils.faiss_index import load_documents as faiss_load_documents
    docs = faiss_load_documents(chunks_dir)
    embed_kwargs = {}
    if args.embedding_model:
        embed_kwargs["model"] = args.embedding_model
    store = FAISS.from_documents(docs, OpenAIEmbeddings(**embed_kwargs))
    os.makedirs(args.faiss_dir, exist_ok=True)
    store.save_local(args.faiss_dir)
    print(f"[DONE] FAISS index created at {args.faiss_dir} with {len(docs)} docs")

def run_merge(args, chunks_dir: str):
    separator = "\n" if args.merge_no_separator else args.merge_separator

    if args.config:
        device = os.path.splitext(os.path.basename(args.config))[0]
        chunk_path = os.path.join(chunks_dir, f"{device}.json")
        if not os.path.isfile(chunk_path):
            raise SystemExit(f"Chunks not found for {device}: {chunk_path}")
        merge_process_file(chunk_path, args.merge_out_dir, args.merge_out, separator)
        return

    files = collect_chunk_files(chunks_dir)
    for path in files:
        merge_process_file(path, args.merge_out_dir, None, separator)

def main():
    argp = argparse.ArgumentParser(description="NetConfig: chunk configs and enable optional outputs via flags.")
    argp.add_argument("--config", help="Path to a single config file")
    argp.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Directory of .cfg files")
    argp.add_argument("--os-type", help="OS type (ios, iosxe, iosxr, nxos, eos)")
    argp.add_argument("--os-map", help="JSON map of filename/device -> os_type")
    argp.add_argument("--detect-os", action="store_true", help="Auto-detect OS type when not provided")
    argp.add_argument("--out-dir", default=DEFAULT_CHUNK_DIR, help="Output directory for chunks")

    argp.add_argument("--dump-mongo", action="store_true", help="Write chunks to MongoDB")
    argp.add_argument("--mongo-uri", default=os.getenv("MONGO_URI", ""), help="MongoDB URI (or set MONGO_URI)")
    argp.add_argument("--mongo-configs-dir", default=None, help="Optional configs dir to attach raw_config")
    argp.add_argument("--mongo-db", default="net_config", help="Mongo database name")
    argp.add_argument("--devices-col", default="devices", help="Devices collection name")
    argp.add_argument("--chunks-col", default="chunks", help="Chunks collection name")
    argp.add_argument("--embed", action="store_true", help="Create embeddings (Mongo and/or FAISS)")
    argp.add_argument("--dry-run", action="store_true", help="Preview Mongo writes without writing")

    argp.add_argument("--dump-vector", action="store_true", help="Build FAISS index from chunks")
    argp.add_argument("--faiss-dir", default=DEFAULT_FAISS_DIR, help="FAISS output directory")
    argp.add_argument("--embedding-model", default=None, help="Embedding model name")

    argp.add_argument("--merge-config", action="store_true", help="Merge chunks back into full config(s)")
    argp.add_argument("--merge-out-dir", default=DEFAULT_MERGE_OUT_DIR, help="Output directory for merged configs")
    argp.add_argument("--merge-out", help="Output file path (only for --config)")
    argp.add_argument("--merge-separator", default="\n!\n", help="Separator between chunks")
    argp.add_argument("--merge-no-separator", action="store_true", help="Do not add separators between chunks")

    args = argp.parse_args()

    if args.embed and not (args.dump_mongo or args.dump_vector):
        print("[WARN] --embed set but no output selected. Use --dump-mongo and/or --dump-vector.")

    if args.dump_mongo and not args.mongo_uri and not args.dry_run:
        raise SystemExit("Missing MongoDB URI. Use --mongo-uri or set MONGO_URI.")

    # Always chunk from configs first (default behavior)
    chunks_dir = run_chunking(args)

    if args.dump_mongo:
        run_mongo(args, chunks_dir)

    if args.dump_vector:
        if not args.embed:
            print("[INFO] --dump-vector will create embeddings for FAISS.")
        run_faiss(args, chunks_dir)

    if args.merge_config:
        run_merge(args, chunks_dir)

if __name__ == "__main__":
    main()
