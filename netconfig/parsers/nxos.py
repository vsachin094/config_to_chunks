from ..core.chunk_builder import build_section_regex, chunk_config

NAME = "nxos"

SECTION_START_PATTERNS = [
    r"^interface\s+",
    r"^router\s+",
    r"^ip\s+access-list",
    r"^ipv6\s+access-list",
    r"^access-list",
    r"^ip\s+prefix-list",
    r"^ipv6\s+prefix-list",
    r"^ip\s+community-list",
    r"^policy-map",
    r"^class-map",
    r"^route-map",
    r"^line\s+",
    r"^vlan\s+",
    r"^vrf\s+context\s+",
    r"^feature\s+",
    r"^hardware\s+",
    r"^system\s+",
    r"^vpc\s+",
    r"^evpn\s+",
    r"^fabricpath\s+",
    r"^monitor\s+session\s+",
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
