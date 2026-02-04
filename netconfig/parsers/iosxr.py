from ..chunker import build_section_regex, chunk_config

NAME = "iosxr"

SECTION_START_PATTERNS = [
    r"^interface\s+",
    r"^router\s+",
    r"^ipv4\s+access-list",
    r"^ipv6\s+access-list",
    r"^ip\s+access-list",
    r"^access-list",
    r"^prefix-set",
    r"^as-path-set",
    r"^community-set",
    r"^route-policy",
    r"^policy-map",
    r"^class-map",
    r"^line\s+",
    r"^vrf\s+\S+",
    r"^telemetry\s+",
    r"^l2vpn\s+",
    r"^mpls\s+",
    r"^segment-routing\s+",
]

SECTION_START_REGEX = build_section_regex(SECTION_START_PATTERNS)
COMMENT_PREFIXES = ["!"]
IGNORE_LINES = set()

def chunk(device, text):
    return chunk_config(
        device,
        text,
        SECTION_START_REGEX,
        comment_prefixes=COMMENT_PREFIXES,
        ignore_lines=IGNORE_LINES
    )
