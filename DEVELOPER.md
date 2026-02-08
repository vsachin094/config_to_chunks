# Developer Guide

This doc explains the project structure, data model, and how to extend it.

## Project Structure

```
netconfig/
  netconfig_runner.py  # main CLI and orchestration
  core/
    config_prep.py     # read configs + resolve OS
    chunk_builder.py   # chunking engine + metadata + write JSON
  parsers/             # OS-specific patterns
  utils/
    mongo_writer.py    # MongoStore class (write/update/delete)
    faiss_index.py     # FaissIndex class (build/load/save/search)
    embeddings.py      # embedding helpers (no chunk logic)
test_scripts/
  merge_chunks.py      # merge chunk JSON back into configs
  langgraph_app.py     # test retrieval app
configs/               # input configs
config_chunks/         # default chunk output
merged_config/         # default merge output (test script)
```

## Chunk Data Model

Each chunk is a dict:
```
{
  "content": "<raw stanza text>",
  "metadata": {
    "device": "XR-PROD-EDGE-01",
    "chunk_type": "explicit|global",
    "section": "router bgp 65001",
    "os_type": "iosxr",
    "chunk_index": 12,
    "section_type": "router",
    "chunk_id": "XR-PROD-EDGE-01|router bgp 65001|12"
  }
}
```

## Chunking Behavior

The engine (`chunk_builder.py`) uses:
- Top-level stanza detection (no leading whitespace)
- Vendor-specific stanza starters from `parsers/*`
- A heuristic: top-level line with indented children = new stanza
- Top-level comment lines (`!`) are separators unless they are inside a stanza
- Large stanzas are split by size

Chunk order is preserved via `chunk_index` in `chunk_builder.build_chunks`.

## Adding a New OS

1. Create a parser in `netconfig/parsers/`.
2. Add stanza patterns in `SECTION_START_PATTERNS`.
3. Register the parser in `netconfig/parsers/__init__.py`:
   - add to `PARSERS`
   - add detection signatures to `DETECT_SIGNATURES`

## Extending Detection

`detect_os_type()` is heuristic. Add unique signatures with weights.
Keep weights small and include multiple signatures per OS.

## Mongo Writer

`netconfig/utils/mongo_writer.py` exposes `MongoStore`:
- generic CRUD helpers: `insert_one`, `insert_many`, `update_one`, `delete_one`, `delete_many`, `upsert`
No chunk-specific logic is inside the class; the runner prepares docs and calls these methods.

The runner stores:
- device metadata in the base collection (default `network_config`)
- chunks in `<base>_chunks`

Mongo defaults are read from `config.yaml` at repo root.


## FAISS Builder

`netconfig/utils/faiss_index.py` exposes `FaissIndex`:
`from_documents`, `load`, `save`, `add_documents`, `rebuild`, `delete_ids`, `similarity_search`
It uses `OpenAIEmbeddings`. Set `OPENAI_API_KEY`.

## Testing

Manual tests:
```
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json
python netconfig/netconfig_runner.py --config-dir configs --os-map os_map.json --dump-vector
```

Check outputs:
- `config_chunks/`
- `merged_config/` (from `test_scripts/merge_chunks.py`)
- `index/faiss/`

## Coding Conventions

- Keep parsers small and OS-specific.
- Avoid complex parsing; prefer stanza-level rules and simple heuristics.
- Keep metadata minimal and consistent across chunks.
