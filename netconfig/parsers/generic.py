from ..core.chunk_builder import build_section_regex, chunk_config

NAME = "generic"

SECTION_START_PATTERNS = [
    r"^interface\s+",
    r"^router\s+",
    r"^ipv4\s+access-list",
    r"^ipv6\s+access-list",
    r"^ip\s+access-list",
    r"^access-list",
    r"^ip\s+prefix-list",
    r"^ipv6\s+prefix-list",
    r"^ip\s+community-list",
    r"^ip\s+as-path\s+access-list",
    r"^policy-map",
    r"^class-map",
    r"^route-map",
    r"^route-policy",
    r"^prefix-set",
    r"^as-path-set",
    r"^community-set",
    r"^line\s+",
    r"^vlan\s+",
    r"^vrf\s+instance\s+",
    r"^vrf\s+context\s+",
    r"^vrf\s+definition\s+",
    r"^vrf\s+\S+",
]

SECTION_START_REGEX = build_section_regex(SECTION_START_PATTERNS)
COMMENT_PREFIXES = ["!"]
IGNORE_LINES = {"end"}

def chunk(device, text):
    return chunk_config(
        device,
        text,
        SECTION_START_REGEX,
        comment_prefixes=COMMENT_PREFIXES,
        ignore_lines=IGNORE_LINES
    )
