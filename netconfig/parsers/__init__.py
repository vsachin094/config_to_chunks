import re
from . import ios
from . import iosxr
from . import nxos
from . import eos
from . import generic

PARSERS = {
    "ios": ios,
    "iosxe": ios,
    "ios-xe": ios,
    "cisco-ios": ios,
    "cisco-ios-xe": ios,
    "iosxr": iosxr,
    "ios-xr": iosxr,
    "cisco-ios-xr": iosxr,
    "nxos": nxos,
    "nx-os": nxos,
    "cisco-nxos": nxos,
    "eos": eos,
    "arista-eos": eos,
    "generic": generic,
}

def normalize_os_type(os_type: str) -> str:
    if not os_type:
        return "generic"
    return os_type.strip().lower().replace("_", "-")

def get_parser(os_type: str):
    key = normalize_os_type(os_type)
    if key in PARSERS:
        return PARSERS[key]
    supported = ", ".join(sorted(PARSERS.keys()))
    raise ValueError(f"Unsupported os_type '{os_type}'. Supported: {supported}")

def supported_os_types():
    return sorted(PARSERS.keys())

DETECT_SIGNATURES = {
    "iosxr": [
        (r"^\s*route-policy\b", 4),
        (r"^\s*prefix-set\b", 4),
        (r"^\s*as-path-set\b", 3),
        (r"^\s*community-set\b", 3),
        (r"^\s*end-policy\b", 4),
        (r"^\s*commit\b", 2),
        (r"RP/\d+/CPU\d+", 2),
        (r"^\s*telemetry\s+model-driven\b", 2),
    ],
    "nxos": [
        (r"^\s*feature\s+\S+", 4),
        (r"^\s*vrf\s+context\b", 4),
        (r"^\s*hardware\s+\S+", 2),
        (r"^\s*vdc\s+\S+", 3),
        (r"^\s*switchname\s+\S+", 2),
        (r"^\s*interface\s+Ethernet\d+/\d+", 1),
    ],
    "eos": [
        (r"^\s*daemon\s+\S+", 4),
        (r"^\s*agent\s+\S+", 3),
        (r"^\s*management\s+api\b", 4),
        (r"^\s*event-handler\b", 4),
        (r"^\s*transceiver\s+\S+", 2),
        (r"^\s*interface\s+Ethernet\d+", 1),
    ],
    "ios": [
        (r"^\s*version\s+\d", 2),
        (r"^\s*service\s+timestamps\b", 2),
        (r"^\s*platform\s+\S+", 2),
        (r"^\s*ip\s+cef\b", 1),
        (r"^\s*line\s+vty\b", 1),
        (r"^\s*enable\s+secret\b", 2),
    ],
}

DETECT_REGEXES = {
    os_name: [
        (re.compile(pattern, re.IGNORECASE | re.MULTILINE), weight)
        for pattern, weight in patterns
    ]
    for os_name, patterns in DETECT_SIGNATURES.items()
}

def detect_os_type(text: str, min_score: int = 3):
    scores = {os_name: 0 for os_name in DETECT_SIGNATURES.keys()}
    for os_name, patterns in DETECT_REGEXES.items():
        for regex, weight in patterns:
            if regex.search(text):
                scores[os_name] += weight

    best_os = max(scores, key=scores.get)
    best_score = scores[best_os]
    tied = [os_name for os_name, score in scores.items() if score == best_score and score > 0]

    if best_score < min_score or len(tied) > 1:
        return None, scores

    return best_os, scores
