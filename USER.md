# User Guide

This project chunks network device configs by OS type and optionally:
- dumps chunks to MongoDB
- creates embeddings
- builds a FAISS index
- merges chunks back into full configs

The main CLI is the module entrypoint:
```
python -m netconfig ...
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Create an OS map:
```json
{
  "XR-PROD-EDGE-01.cfg": "iosxr",
  "IOS-PROD-EDGE-01.cfg": "ios",
  "EOS-PROD-EDGE-01.cfg": "eos"
}
```
Save it as `os_map.json`.

3. Run chunking (default output `config_chunks/`):
```bash
python -m netconfig --config-dir configs --os-map os_map.json
```

## Core Options

### Chunking
Chunk all configs in a directory:
```bash
python -m netconfig --config-dir configs --os-map os_map.json
```

Chunk a single config:
```bash
python -m netconfig --config configs/XR-PROD-EDGE-01.cfg --os-type iosxr
```

Auto-detect OS:
```bash
python -m netconfig --config-dir configs --detect-os
```

Custom output directory:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --out-dir chunks
```

### Merge back to full configs
Merge all chunks:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --merge-config
```

Merge a single device:
```bash
python -m netconfig --config configs/EOS-PROD-EDGE-01.cfg --os-type eos --merge-config
```

Output directory for merged configs:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --merge-config --merge-out-dir merged_config
```

### Dump to MongoDB
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --mongo-uri "mongodb://HOST:27017"
```

With embeddings:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --embed --mongo-uri "mongodb://HOST:27017"
```

Dry-run (no writes):
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --dry-run
```

Attach raw configs to the device document:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --mongo-configs-dir configs --mongo-uri "mongodb://HOST:27017"
```

### Dump embeddings to FAISS
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-vector --faiss-dir index/faiss
```

## Environment Variables
- `MONGO_URI`: MongoDB connection string
- `OPENAI_API_KEY`: required when creating embeddings

## Outputs
- Chunks: `config_chunks/DEVICE.json` (default)
- Merged configs: `merged_config/DEVICE.cfg` (default)
- FAISS index: `index/faiss/`

## Notes
- Chunk order is preserved using `chunk_index`.
- OS detection is heuristic-based; use `--os-map` for best accuracy.
