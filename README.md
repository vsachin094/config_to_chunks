# Net Config AI (Simple + Powerful)

This project chunks network device configs by OS type. A single CLI creates chunks by default, and optional flags can dump to Mongo or build FAISS.

## Quick Start

Install dependencies:
```bash
pip install -r requirements.txt
```

Create an OS map (optional but recommended):
```json
{
  "XR-PROD-EDGE-01.cfg": "iosxr",
  "IOS-PROD-EDGE-01.cfg": "ios",
  "EOS-PROD-EDGE-01.cfg": "eos"
}
```

Save it as `os_map.json`.

## Main Entry Point (One CLI)

Create chunks (default output: `config_chunks/`):
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json
```

Auto-detect OS:
```bash
python netconfig/netconfig_runner.py --config-dir configs --detect-os
```

Single config:
```bash
python netconfig/netconfig_runner.py --config configs/XR-PROD-EDGE-01.cfg --os-type iosxr
```

Note: chunking is the default behavior. It writes to `config_chunks/` unless you pass `--out-dir`.

Write chunks to Mongo (after chunking):

```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump
```

Mongo collections:
- Base collection: `network_config` (device metadata)
- Chunks collection: `network_config_chunks`
Use `--collection NAME` to change the base name.

Mongo connection defaults live in `config.yaml`:
```
mongo:
  uri: "mongodb://localhost:27017"
  db: "net_config"
  collection: "network_config"
```

Write chunks to Mongo with embeddings:
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump --embed
```

Dry-run preview (no writes):
```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --mongo-dump --dry-run
```

Build FAISS index (after chunking):

```bash
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --dump-vector --faiss-dir index/faiss
```

## Merge Chunks Back to Config

Merge one chunks file:
```bash
python test_scripts/merge_chunks.py --chunks config_chunks/EOS-PROD-EDGE-01.json --out merged_config/EOS-PROD-EDGE-01.cfg
```

Merge all chunks in a directory:
```bash
python test_scripts/merge_chunks.py --chunks-dir config_chunks --out-dir merged_config
```

Disable separators between chunks:
```bash
python test_scripts/merge_chunks.py --chunks-dir config_chunks --out-dir merged_config --no-separator
```

## Project Layout

```
netconfig/
  core/
    config_prep.py
    chunk_builder.py
  netconfig_runner.py
  utils/
    mongo_writer.py
    faiss_index.py
    embeddings.py
  parsers/
    ios.py
    iosxr.py
    nxos.py
    eos.py
    generic.py
configs/
config_chunks/
test_scripts/
  merge_chunks.py
  langgraph_app.py
```

## Notes
- Set `OPENAI_API_KEY` when using embeddings.
- Edit `config.yaml` to change Mongo defaults (no env vars required).
- OS detection is heuristic-based; use `--os-map` for best accuracy.
- If you do not pass `--os-type` or `--os-map`, auto-detection is used by default.

## Documentation
- `USER.md`
- `DEVELOPER.md`
