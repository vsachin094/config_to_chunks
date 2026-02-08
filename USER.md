# User Guide

NetConfig converts raw network device configs into structured chunks for fast retrieval and optional storage in MongoDB or FAISS.

**Main CLI**
```
python netconfig/netconfig_runner.py ...
```

**Quick Start**
1. Install dependencies:
```bash
pip install -r requirements.txt
```

1. (Optional) Create an OS map:
```json
{
  "XR-PROD-EDGE-01.cfg": "iosxr",
  "IOS-PROD-EDGE-01.cfg": "ios",
  "EOS-PROD-EDGE-01.cfg": "eos"
}
```
Save it as `os_map.json`.

1. Run chunking (default output `config_chunks/`):
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json
```

**Config File**
Mongo defaults live in `config.yaml` (no env vars required):
```
mongo:
  uri: "mongodb://localhost:27017"
  db: "net_config"
  collection: "network_config"
```

**Core Usage**
Chunk all configs in a directory:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json
```

Chunk a single config:
```bash
python netconfig/netconfig_runner.py --config configs/XR-PROD-EDGE-01.cfg --os-type iosxr
```

Auto-detect OS:
```bash
python netconfig/netconfig_runner.py --config-dir configs --detect-os
```

Custom output directory:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --out-dir chunks
```

**MongoDB Output**
Write chunks to Mongo:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump
```

Collections:
- Base collection: `network_config` (device metadata)
- Chunks collection: `network_config_chunks`
Use `--collection NAME` to change the base name.

With embeddings:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump --embed
```

Dry-run (no writes):
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump --dry-run
```

**FAISS Output**
Build a FAISS index from chunks:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --dump-vector --faiss-dir index/faiss
```

**Merge Back (Test Script)**
Merge all chunks:
```bash
python test_scripts/merge_chunks.py --chunks-dir config_chunks --out-dir merged_config
```

Merge a single device:
```bash
python test_scripts/merge_chunks.py --chunks config_chunks/EOS-PROD-EDGE-01.json --out merged_config/EOS-PROD-EDGE-01.cfg
```

**LangGraph Test App**
```bash
python test_scripts/langgraph_app.py --index-dir index/faiss --k 8
```

**Environment Variables**
- `OPENAI_API_KEY`: required when creating embeddings

**Outputs**
- Chunks: `config_chunks/DEVICE.json` (default)
- Merged configs (via test script): `merged_config/DEVICE.cfg` (default)
- FAISS index: `index/faiss/`

**Notes**
- Chunk order is preserved using `chunk_index`.
- OS detection is heuristic-based; use `--os-map` for best accuracy.
- If you do not pass `--os-type` or `--os-map`, auto-detection is used by default.
