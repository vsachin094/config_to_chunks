from ..chunker import build_section_regex, chunk_config

NAME = "eos"

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
    r"^vrf\s+instance\s+",
    r"^daemon\s+",
    r"^agent\s+",
    r"^event-handler\s+",
    r"^management\s+api\s+",
    r"^transceiver\s+",
    r"^alias\s+",
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
