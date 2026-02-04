# Net Config AI (Simple + Powerful)

This project chunks network device configs by OS type. A single CLI creates chunks by default, and optional flags can dump to Mongo, build FAISS, or merge configs back.

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
python -m netconfig --config-dir configs --os-map os_map.json
```

Auto-detect OS:
```bash
python -m netconfig --config-dir configs --detect-os
```

Single config:
```bash
python -m netconfig --config configs/XR-PROD-EDGE-01.cfg --os-type iosxr
```

Chunk then merge in one run:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --merge-config
```

Note: chunking is the default behavior. It writes to `config_chunks/` unless you pass `--out-dir`.

Write chunks to Mongo (after chunking):

```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --mongo-uri "mongodb://HOST:27017"
```

Write chunks to Mongo with embeddings:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --embed --mongo-uri "mongodb://HOST:27017"
```

Dry-run preview (no writes):
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --dry-run
```

Attach raw configs when writing to Mongo:
```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-mongo --mongo-configs-dir configs --mongo-uri "mongodb://HOST:27017"
```

Build FAISS index (after chunking):

```bash
python -m netconfig --config-dir configs --os-map os_map.json --dump-vector --faiss-dir index/faiss
```

## Merge Chunks Back to Config

Merge one chunks file:
```bash
python -m netconfig.merge_chunks --chunks config_chunks/EOS-PROD-EDGE-01.json --out merged_config/EOS-PROD-EDGE-01.cfg
```

Merge all chunks in a directory:
```bash
python -m netconfig.merge_chunks --chunks-dir config_chunks --out-dir merged_config
```

Disable separators between chunks:
```bash
python -m netconfig.merge_chunks --chunks-dir config_chunks --out-dir merged_config --no-separator
```

## Project Layout

```
netconfig/
  chunker.py
  chunk_utils.py
  chunk_configs.py
  merge_chunks.py
  cli.py
  utils/
    mongo_writer.py
    faiss_index.py
  parsers/
    ios.py
    iosxr.py
    nxos.py
    eos.py
    generic.py
configs/
config_chunks/
apps/
  langgraph_app.py
```

## Notes
- Set `OPENAI_API_KEY` when using embeddings.
- Set `MONGO_URI` or pass `--mongo-uri` when pushing to Mongo.
- OS detection is heuristic-based; use `--os-map` for best accuracy.

## Documentation
- `USER.md`
- `DEVELOPER.md`
