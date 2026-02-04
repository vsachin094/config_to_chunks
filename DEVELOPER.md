# Developer Guide

This doc explains the project structure, data model, and how to extend it.

## Project Structure

```
netconfig/
  __main__.py          # module entrypoint -> cli.py
  cli.py               # main CLI and orchestration
  chunk_configs.py     # read configs and write chunk JSON
  chunker.py           # chunking engine
  chunk_utils.py       # shared helpers (metadata, embeddings)
  merge_chunks.py      # merge chunk JSON back into configs
  parsers/             # OS-specific patterns
  utils/
    mongo_writer.py    # optional Mongo writer
    faiss_index.py     # optional FAISS builder
configs/               # input configs
config_chunks/         # default chunk output
merged_config/         # default merge output
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

The engine (`chunker.py`) uses:
- Top-level stanza detection (no leading whitespace)
- Vendor-specific stanza starters from `parsers/*`
- A heuristic: top-level line with indented children = new stanza
- Top-level comment lines (`!`) are separators unless they are inside a stanza
- Large stanzas are split by size

Chunk order is preserved via `chunk_index` in `chunk_utils.build_chunks`.

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

`netconfig/utils/mongo_writer.py` expects chunk JSON files.
It:
- normalizes metadata
- optionally generates embeddings
- writes `devices` and `chunks` collections

You can attach raw configs via `--mongo-configs-dir`.

## FAISS Builder

`netconfig/utils/faiss_index.py` builds an index from chunk JSON files.
It uses `OpenAIEmbeddings`. Set `OPENAI_API_KEY`.

## Testing

Manual tests:
```
python -m netconfig --config-dir configs --os-map os_map.json
python -m netconfig --config-dir configs --os-map os_map.json --merge-config
python -m netconfig --config-dir configs --os-map os_map.json --dump-vector
```

Check outputs:
- `config_chunks/`
- `merged_config/`
- `index/faiss/`

## Coding Conventions

- Keep parsers small and OS-specific.
- Avoid complex parsing; prefer stanza-level rules and simple heuristics.
- Keep metadata minimal and consistent across chunks.
