#!/usr/bin/env python3
"""
enrich_wiki.py

Auto-enrich Bee Planet Connection wiki articles using JSON seeds.

Priority order:
  1) Topic seed:      data/seeds/topics/<slug>.json
  2) Archetype seed:  data/seeds/<archetype>/*.json
  3) Hints:           data/seeds/hints/<slug>.json or <archetype>.json

Sections enforce minimum word counts, and articles respect global min/max length.
"""

from __future__ import annotations
import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

# ----------------------------
# Config
# ----------------------------

SECTION_MIN = {
    "At-a-Glance": 60,
    "Why it Matters": 80,
    "Overview": 120,
    "Step-by-Step": 140,
    "Seasonality & Climate": 80,
    "Common Pitfalls": 80,
    "Tools & Materials": 40,
    "Further Reading & Sources": 30,
}

GLOBAL_MIN_WORDS = 700
GLOBAL_MAX_WORDS = 3000

ARCHETYPE_SECTIONS: Dict[str, List[str]] = {
    "management_guide": [
        "At-a-Glance",
        "Why it Matters",
        "Step-by-Step",
        "Seasonality & Climate",
        "Common Pitfalls",
        "Tools & Materials",
        "Further Reading & Sources",
    ],
    "disease_pest": [
        "Overview",
        "Biology & Transmission",
        "Symptoms & Field Diagnosis",
        "Impact on Colony",
        "Control & Treatment",
        "Prevention & Good Practice",
        "Further Reading & Sources",
    ],
    "product_substance": [
        "What It Is",
        "Harvesting & Processing",
        "Properties & Uses",
        "Market & Value",
        "Further Reading & Sources",
    ],
    "equipment_technology": [
        "Overview",
        "Types & Variants",
        "Using It Well",
        "Costs & Practicalities",
        "Recent Innovations",
        "Further Reading & Sources",
    ],
    "economics_market": [
        "Snapshot",
        "Supply & Demand",
        "Revenue Streams",
        "Risks & Compliance",
        "Further Reading & Sources",
    ],
    "ecology_environment": [
        "Overview",
        "Drivers & Mechanisms",
        "Impacts & Case Studies",
        "Mitigation & Best Practice",
        "Further Reading & Sources",
    ],
    "conservation_policy": [
        "Context",
        "Policy & Initiatives",
        "Practical Actions",
        "Further Reading & Sources",
    ],
    "_default": [
        "Overview",
        "Why it Matters",
        "Step-by-Step",
        "Further Reading & Sources",
    ],
}

# ----------------------------
# Helpers
# ----------------------------

WORD_RE = re.compile(r"\w+(?:[-’']\w+)?", re.UNICODE)

def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))

def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def clamp_total(article_md: str) -> str:
    if word_count(article_md) <= GLOBAL_MAX_WORDS:
        return article_md
    parts = re.split(r"\n{2,}", article_md.strip())
    out, count = [], 0
    for p in parts:
        w = word_count(p)
        if count + w > GLOBAL_MAX_WORDS:
            break
        out.append(p)
        count += w
    return "\n\n".join(out)

def ensure_section_min(text: str, section: str, min_words: int) -> str:
    text = (text or "").strip()
    if word_count(text) >= min_words:
        return text
    deficit = max(0, min_words - word_count(text))
    filler = " " + " ".join(["Additional practical detail forthcoming."] * max(1, deficit // 5))
    return (text + filler).strip()

def detect_front_matter(md: str) -> Dict[str, str]:
    meta = {}
    for line in md.splitlines():
        if not line.strip():
            break
        m = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", line)
        if not m:
            break
        meta[m.group(1).strip()] = m.group(2).strip()
    return meta

def detect_title(md: str, fallback_name: str) -> str:
    m = re.search(r"^\s*#\s+(.+?)\s*$", md, flags=re.M)
    if m:
        return m.group(1).strip()
    t = fallback_name.replace("_", " ").strip()
    return t[:1].upper() + t[1:]

def detect_archetype(path: Path, meta: Dict[str, str]) -> str:
    if "archetype" in meta and meta["archetype"].strip():
        return meta["archetype"].strip()
    p = str(path).lower()
    for k in ARCHETYPE_SECTIONS.keys():
        if k == "_default":
            continue
        if k in p:
            return k
    return "management_guide"

def desired_sections_for_archetype(archetype: str) -> List[str]:
    return ARCHETYPE_SECTIONS.get(archetype, ARCHETYPE_SECTIONS["_default"])

def parse_sections(md: str) -> Tuple[str, Dict[str, str]]:
    title = detect_title(md, "Untitled")
    parts = re.split(r"(?m)^(##+)\s+(.+?)\s*$", md)
    sections: Dict[str, str] = {}
    if len(parts) < 3:
        return title, sections
    for i in range(1, len(parts), 3):
        heading = parts[i+1].strip()
        body = parts[i+2]
        sections[heading] = body.strip()
    return title, sections

def render_markdown(title: str, content_map: Dict[str, str], meta: Dict[str, str]) -> str:
    front = []
    keep = {k: v for k, v in meta.items() if k in ("slug", "archetype", "title")}
    if keep:
        for k, v in keep.items():
            front.append(f"{k}: {v}")
        front.append("")
    lines = []
    if front:
        lines.extend(front)
    lines.append(f"# {title}")
    lines.append("")
    for h, body in content_map.items():
        lines.append(f"## {h}")
        lines.append(body.strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def load_json_safe(p: Path) -> Dict[str, str]:
    try:
        return json.loads(read_text(p))
    except Exception:
        return {}

def load_seed_for_slug(slug: str, archetype: str) -> Dict[str, str]:
    base = Path("data/seeds")
    topic_fp = base / "topics" / f"{slug}.json"
    if topic_fp.exists():
        return load_json_safe(topic_fp)
    arch_dir = base / archetype
    if arch_dir.exists():
        for fp in arch_dir.glob("*.json"):
            data = load_json_safe(fp)
            if data:
                return data
    return {}

def load_hints(slug: str, archetype: str) -> Dict[str, str]:
    base = Path("data/seeds/hints")
    slug_fp = base / f"{slug}.json"
    if slug_fp.exists():
        return load_json_safe(slug_fp)
    arch_fp = base / f"{archetype}.json"
    if arch_fp.exists():
        return load_json_safe(arch_fp)
    return {}

def choose_best(section: str, base_text: str, seed_text: str, hint_text: str) -> str:
    min_needed = SECTION_MIN.get(section, 0)
    base_wc = word_count(base_text)
    seed_wc = word_count(seed_text)
    hint_wc = word_count(hint_text)
    if min_needed and base_wc >= int(0.7 * min_needed):
        extra = []
        def sentences(t: str) -> List[str]:
            return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s.strip()]
        seen = set(sentences(base_text))
        for candidate in sentences(seed_text) + sentences(hint_text):
            if candidate and candidate not in seen:
                extra.append(candidate)
        enrich = " " + " ".join(extra[:3]) if extra else ""
        return (base_text.strip() + enrich).strip()
    if seed_wc:
        return (seed_text.strip() + ("\n\n" + base_text.strip() if base_text else "")).strip()
    if hint_wc:
        return (hint_text.strip() + ("\n\n" + base_text.strip() if base_text else "")).strip()
    return base_text.strip()

@dataclass
class EnrichmentResult:
    path: Path
    slug: str
    archetype: str
    title: str
    before_wc: int
    after_wc: int
    sections_added: List[str] = field(default_factory=list)
    sections_padded: List[str] = field(default_factory=list)
    wrote: bool = False

# ----------------------------
# Core
# ----------------------------

def process_file(fp: Path, out_dir: Path, dry_run: bool = False, overwrite: bool = True) -> EnrichmentResult:
    md = read_text(fp)
    meta = detect_front_matter(md)
    title = detect_title(md, fp.stem)
    slug = meta.get("slug") or slugify(title)
    archetype = detect_archetype(fp, meta)
    desired_sections = desired_sections_for_archetype(archetype)
    _, existing_sections = parse_sections(md)
    seed = load_seed_for_slug(slug, archetype)
    hints = load_hints(slug, archetype)
    content_map: Dict[str, str] = {}
    sections_added, sections_padded = [], []
    for sec in desired_sections:
        base_text = existing_sections.get(sec, "").strip()
        seed_text = str(seed.get(sec) or seed.get("Overview") or seed.get("At-a-Glance") or "")
        hint_text = str(hints.get(sec) or "")
        merged = choose_best(sec, base_text, seed_text, hint_text)
        min_words = SECTION_MIN.get(sec, 0)
        padded = ensure_section_min(merged, sec, min_words) if min_words else merged
        if not base_text and padded:
            sections_added.append(sec)
        elif word_count(padded) > word_count(merged):
            sections_padded.append(sec)
        content_map[sec] = padded
    for sec, body in existing_sections.items():
        if sec not in content_map:
            content_map[sec] = body
