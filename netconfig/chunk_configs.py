import os
import json
import argparse
from .parsers import get_parser, detect_os_type
from .chunk_utils import build_chunks

DEFAULT_CONFIG_DIR = "./configs"
DEFAULT_CHUNK_DIR = "config_chunks"

def load_os_map(path):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("os_map must be a JSON object mapping filename/device to os_type")
    return data

def resolve_os_type(os_map, filename, device):
    if not os_map:
        return None
    if filename in os_map:
        return os_map[filename]
    if device in os_map:
        return os_map[device]
    return None

def process_file(path, os_type, out_dir, detect=False):
    device = os.path.basename(path)
    if device.endswith(".cfg"):
        device = device[:-4]
    with open(path) as f:
        text = f.read()

    if detect and not os_type:
        detected, scores = detect_os_type(text)
        if detected:
            os_type = detected
            print(f"[INFO] {device}: detected os_type={os_type} scores={scores}")
        else:
            os_type = "generic"
            print(f"[WARN] {device}: OS detection ambiguous (scores={scores}). Using generic parser.")

    if not os_type:
        raise SystemExit(f"Missing os_type for {device}. Provide --os-type, --os-map, or --detect-os.")

    parser = get_parser(os_type)
    chunks = build_chunks(device, os_type, text)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{device}.json")
    with open(out_path, "w") as f:
        json.dump(chunks, f, indent=2)

    print(f"[OK] {device}: {len(chunks)} chunks created ({parser.NAME})")

def main():
    argp = argparse.ArgumentParser(description="Chunk network configs by OS type.")
    argp.add_argument("--config", help="Path to a single config file")
    argp.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Directory of .cfg files")
    argp.add_argument("--os-type", help="OS type (ios, iosxe, iosxr, nxos, eos)")
    argp.add_argument("--os-map", help="JSON map of filename/device -> os_type")
    argp.add_argument("--detect-os", action="store_true", help="Auto-detect OS type when not provided")
    argp.add_argument("--out-dir", default=DEFAULT_CHUNK_DIR, help="Output directory for chunks")
    args = argp.parse_args()

    os_map = load_os_map(args.os_map) if args.os_map else None

    if args.config:
        os_type = args.os_type or resolve_os_type(
            os_map,
            os.path.basename(args.config),
            os.path.splitext(os.path.basename(args.config))[0]
        )
        detect = args.detect_os and not os_type
        process_file(args.config, os_type, args.out_dir, detect=detect)
        return

    cfg_dir = args.config_dir
    files = sorted([f for f in os.listdir(cfg_dir) if f.endswith(".cfg")])
    if not files:
        raise SystemExit(f"No .cfg files found in {cfg_dir}")

    if args.os_type:
        for file in files:
            process_file(os.path.join(cfg_dir, file), args.os_type, args.out_dir)
        return

    if os_map:
        for file in files:
            device = os.path.splitext(file)[0]
            os_type = resolve_os_type(os_map, file, device)
            if not os_type and args.detect_os:
                process_file(os.path.join(cfg_dir, file), None, args.out_dir, detect=True)
                continue
            if not os_type:
                raise SystemExit(f"Missing os_type for {file} in --os-map (or use --detect-os)")
            process_file(os.path.join(cfg_dir, file), os_type, args.out_dir)
        return

    if args.detect_os:
        for file in files:
            process_file(os.path.join(cfg_dir, file), None, args.out_dir, detect=True)
        return

    print("[WARN] No os_type provided. Using generic parser for all configs.")
    for file in files:
        process_file(os.path.join(cfg_dir, file), "generic", args.out_dir)

if __name__ == "__main__":
    main()
