import os
import json
import argparse
from typing import List, Dict, Any

DEFAULT_CHUNK_DIR = "config_chunks"
DEFAULT_OUT_DIR = "merged_config"

def load_chunks(path: str) -> List[Dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Invalid chunks format in {path}: expected a list")
    return data

def order_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not chunks:
        return chunks
    has_index = all("chunk_index" in c.get("metadata", {}) for c in chunks)
    if has_index:
        return sorted(chunks, key=lambda c: c["metadata"]["chunk_index"])
    return chunks

def merge_chunks(chunks: List[Dict[str, Any]], separator: str) -> str:
    ordered = order_chunks(chunks)
    parts = [c.get("content", "").rstrip() for c in ordered]
    merged = separator.join(parts).rstrip() + "\n"
    return merged

def device_name_from_file(path: str) -> str:
    base = os.path.basename(path)
    if base.endswith(".json"):
        base = base[:-5]
    return base

def write_config(out_path: str, content: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(content)

def process_file(path: str, out_dir: str, out_path: str, separator: str):
    chunks = load_chunks(path)
    merged = merge_chunks(chunks, separator)
    device = device_name_from_file(path)
    target = out_path or os.path.join(out_dir, f"{device}.cfg")
    write_config(target, merged)
    print(f"[OK] {device}: config written to {target}")

def main():
    argp = argparse.ArgumentParser(description="Merge chunked JSON back into full configs.")
    argp.add_argument("--chunks", help="Path to a single chunks JSON file")
    argp.add_argument("--chunks-dir", default=DEFAULT_CHUNK_DIR, help="Directory of chunks JSON files")
    argp.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Output directory for reconstructed configs")
    argp.add_argument("--out", help="Output file path (only for --chunks)")
    argp.add_argument("--separator", default="\n!\n", help="Separator between chunks")
    argp.add_argument("--no-separator", action="store_true", help="Do not add separators between chunks")
    args = argp.parse_args()

    separator = "\n" if args.no_separator else args.separator

    if args.chunks:
        process_file(args.chunks, args.out_dir, args.out, separator)
        return

    files = sorted([f for f in os.listdir(args.chunks_dir) if f.endswith(".json")])
    if not files:
        raise SystemExit(f"No .json chunk files found in {args.chunks_dir}")

    for file in files:
        process_file(os.path.join(args.chunks_dir, file), args.out_dir, None, separator)

if __name__ == "__main__":
    main()
