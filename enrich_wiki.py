#!/usr/bin/env python3
"""
enrich_wiki.py

Auto-enrich Bee Planet Connection wiki articles using JSON seeds.

Priority order for enrichment content:
  1) Topic seed:      data/seeds/topics/<slug>.json
  2) Archetype seed:  data/seeds/<archetype>/*.json  (first readable file)
  3) Hints:           data/seeds/hints/<slug>.json or data/seeds/hints/<archetype>.json

Section minimums are enforced, and articles are clamped to a global max word count.
A dry-run mode prints a summary without writing.

Typical usage:
  python enrich_wiki.py --input "content/wiki/**/*.md" --out content/wiki --dry-run
  python enrich_wiki.py --input "content/wiki/**/*.md" --out content/wiki

Assumptions:
- Markdown headings use # / ## / ### for sections
- (Optional) Front matter at top with 'slug:' and/or 'archetype:' (YAML-like, not strictly parsed)
- If no archetype is found, inferred from the file path or defaulted to 'management_guide'

Author: Bee Planet Connection helpers
"""

from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ----------------------------
# Configuration
# ----------------------------

SECTION_MIN = {
    "At-a-Glance": 60,
    "Why it Matters": 80,
    "Overview": 120,
    "Step-by-Step": 140,
    "Seasonality & Climate": 80,
    "Common Pitfalls": 80,
    "Tools & Materials": 40,
    "Further Reading & Sources": 30,  # optional but nice to have
}

GLOBAL_MIN_WORDS = 700
GLOBAL_MAX_WORDS = 3000

# For archetype planning: which sections should a page ideally have?
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
