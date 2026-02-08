import os
import json
from typing import List, Dict, Any, Optional

from ..parsers import detect_os_type

DEFAULT_CONFIG_DIR = "configs"

def load_os_map(path: Optional[str]) -> Optional[Dict[str, str]]:
    if not path:
        return None
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("os_map must be a JSON object mapping filename/device to os_type")
    return data

def resolve_os_type(os_map: Optional[Dict[str, str]], filename: str, device: str) -> Optional[str]:
    if not os_map:
        return None
    if filename in os_map:
        return os_map[filename]
    if device in os_map:
        return os_map[device]
    return None

def read_config(path: str) -> str:
    with open(path) as f:
        return f.read()

def prepare_configs(
    config: Optional[str] = None,
    config_dir: Optional[str] = None,
    os_type: Optional[str] = None,
    os_map_path: Optional[str] = None,
    detect_os: bool = False
) -> List[Dict[str, Any]]:
    os_map = load_os_map(os_map_path)
    auto_detect = detect_os or (os_type is None and os_map_path is None)
    cfg_dir = config_dir or DEFAULT_CONFIG_DIR

    if config:
        files = [config]
    else:
        files = sorted([
            os.path.join(cfg_dir, f)
            for f in os.listdir(cfg_dir)
            if f.endswith(".cfg")
        ])
        if not files:
            raise SystemExit(f"No .cfg files found in {cfg_dir}")

    prepared: List[Dict[str, Any]] = []
    for path in files:
        filename = os.path.basename(path)
        device = os.path.splitext(filename)[0]
        text = read_config(path)

        resolved = os_type or resolve_os_type(os_map, filename, device)
        if not resolved and auto_detect:
            detected, scores = detect_os_type(text)
            if detected:
                resolved = detected
                print(f"[INFO] {device}: detected os_type={resolved} scores={scores}")
            else:
                resolved = "generic"
                print(f"[WARN] {device}: OS detection ambiguous (scores={scores}). Using generic parser.")

        if not resolved:
            raise SystemExit(f"Missing os_type for {device}. Provide --os-type, --os-map, or --detect-os.")

        prepared.append({
            "device": device,
            "os_type": resolved,
            "text": text,
            "path": path
        })

    return prepared
