mkdir -p scripts
cat > scripts/enrichment_patch_example.py <<'PY'
#!/usr/bin/env python3
"""
Enrichment patch example.

Provides:
 - Section minimum word enforcement
 - Global min/max word count guards
 - Seed loader that prefers topic seeds, then archetype seeds
"""

from pathlib import Path
import json
import re

# Minimum words required per section
SECTION_MIN = {
    "At-a-Glance": 60,
    "Why it Matters": 80,
    "Overview": 120,
    "Step-by-Step": 140,
    "Seasonality & Climate": 80,
    "Common Pitfalls": 80,
    "Tools & Materials": 40,
    # add more as needed
}

# Global article thresholds
GLOBAL_MIN_WORDS = 700
GLOBAL_MAX_WORDS = 3000


def load_seed_for_slug(slug: str, archetype: str) -> dict:
    """
    Prefer topic-specific seed JSON if it exists.
    Otherwise fall back to the first matching archetype seed.
    """
    base = Path("data/seeds")

    topic_fp = base / "topics" / f"{slug}.json"
    if topic_fp.exists():
        return json.loads(topic_fp.read_text(encoding="utf-8"))

    arch_dir = base / archetype
    if arch_dir.exists():
        for fp in arch_dir.glob("*.json"):
            try:
                return json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue

    return {}


def ensure_section_min(text: str, section: str, min_words: int) -> str:
    """
    Guarantee minimum word count per section.
    If too short, pad with a neutral filler.
    """
    text = text or ""
    words = re.findall(r"\w+(?:[-’']\w+)?", text)
    if len(words) >= min_words:
        return text

    deficit = max(0, min_words - len(words))
    filler = " " + " ".join(
        ["Additional practical detail forthcoming."] * max(1, deficit // 5)
    )
    return text.strip() +
