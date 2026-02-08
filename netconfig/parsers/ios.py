from ..core.chunk_builder import build_section_regex, chunk_config

NAME = "ios"

SECTION_START_PATTERNS = [
    r"^interface\s+",
    r"^router\s+",
    r"^ip\s+access-list",
    r"^ipv6\s+access-list",
    r"^access-list",
    r"^ip\s+prefix-list",
    r"^ipv6\s+prefix-list",
    r"^ip\s+community-list",
    r"^ip\s+as-path\s+access-list",
    r"^event\s+manager\s+",
    r"^policy-map",
    r"^class-map",
    r"^route-map",
    r"^line\s+",
    r"^vlan\s+",
    r"^vrf\s+definition\s+",
    r"^ip\s+sla",
    r"^crypto\s+pki\s+",
    r"^track\s+",
    r"^control-plane$",
    r"^platform\s+",
    r"^controller\s+",
    r"^redundancy\s+",
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
