import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

SIZE_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

def build_section_regex(patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)

def is_top_level(line: str) -> bool:
    return bool(line) and not line[0].isspace()

def is_comment_line(line: str, comment_prefixes) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(p) for p in comment_prefixes)

def is_top_level_comment(line: str, comment_prefixes) -> bool:
    return is_top_level(line) and is_comment_line(line, comment_prefixes)

def should_ignore_line(line: str, ignore_lines) -> bool:
    return line.strip() in ignore_lines

def next_non_comment_non_blank(lines, idx, comment_prefixes, ignore_lines):
    j = idx + 1
    while j < len(lines):
        candidate = lines[j]
        stripped = candidate.strip()
        if not stripped:
            j += 1
            continue
        if should_ignore_line(candidate, ignore_lines):
            j += 1
            continue
        if is_comment_line(candidate, comment_prefixes):
            j += 1
            continue
        return candidate
    return None

def is_section_start(line: str, idx: int, lines, section_start_regex, comment_prefixes, ignore_lines) -> bool:
    if not is_top_level(line):
        return False
    stripped = line.strip()
    if section_start_regex.match(stripped):
        return True
    # Heuristic: any top-level line with indented children is a section
    nxt = next_non_comment_non_blank(lines, idx, comment_prefixes, ignore_lines)
    if nxt and not is_top_level(nxt):
        return True
    return False

def emit_global(device, lines, splitter):
    content = "\n".join(lines)
    if len(content) > 1200:
        return [make_global_chunk(device, sub) for sub in splitter.split_text(content)]
    return [make_global_chunk(device, content)]

def emit_section(device, header, lines, splitter):
    content = "\n".join(lines)
    if len(content) > 1200:
        return [
            make_explicit_chunk(device, header, sub)
            for sub in splitter.split_text(content)
        ]
    return [make_explicit_chunk(device, header, content)]

def make_explicit_chunk(device, header, content):
    return {
        "content": content,
        "metadata": {
            "device": device,
            "chunk_type": "explicit",
            "section": header
        }
    }

def make_global_chunk(device, content):
    return {
        "content": content,
        "metadata": {
            "device": device,
            "chunk_type": "global"
        }
    }

def chunk_config(device, text, section_start_regex, comment_prefixes=None, ignore_lines=None, splitter=None):
    if comment_prefixes is None:
        comment_prefixes = ["!"]
    if ignore_lines is None:
        ignore_lines = set()
    if splitter is None:
        splitter = SIZE_SPLITTER

    lines = text.splitlines()
    chunks = []

    current = []
    header = None
    global_buffer = []

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            continue

        if should_ignore_line(line, ignore_lines):
            continue

        # Top-level comments often separate sections, but may appear inside stanzas
        if is_top_level_comment(line, comment_prefixes):
            if current:
                nxt = next_non_comment_non_blank(lines, idx, comment_prefixes, ignore_lines)
                if nxt and not is_top_level(nxt):
                    continue
                chunks.extend(emit_section(device, header, current, splitter))
                current, header = [], None
            if global_buffer:
                chunks.extend(emit_global(device, global_buffer, splitter))
                global_buffer = []
            continue

        # Indented comments inside stanzas are ignored
        if is_comment_line(line, comment_prefixes):
            continue

        if is_top_level(line):
            if is_section_start(line, idx, lines, section_start_regex, comment_prefixes, ignore_lines):
                if global_buffer:
                    chunks.extend(emit_global(device, global_buffer, splitter))
                    global_buffer = []
                if current:
                    chunks.extend(emit_section(device, header, current, splitter))
                header = stripped
                current = [line]
            else:
                if current:
                    chunks.extend(emit_section(device, header, current, splitter))
                    current, header = [], None
                global_buffer.append(line)
        else:
            if current:
                current.append(line)
            else:
                global_buffer.append(line)

    if current:
        chunks.extend(emit_section(device, header, current, splitter))

    if global_buffer:
        chunks.extend(emit_global(device, global_buffer, splitter))

    return chunks
