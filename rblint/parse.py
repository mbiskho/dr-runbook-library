from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

FRONT = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
HEADING = re.compile(r"^##\s+(.+?)\s*$", re.M)


@dataclass
class Runbook:
    path: Path
    meta: dict
    sections: dict[str, str]   # lowercased heading -> body


def parse(path: Path) -> Runbook:
    text = path.read_text()
    m = FRONT.match(text)
    meta, body = (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, text)
    parts = HEADING.split(body)
    sections = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    return Runbook(path, meta, sections)
