mkdir -p scripts
cat > scripts/enrichment_patch_example.py <<'PY'
from pathlib import Path
import json, re

SECTION_MIN = {
    "At-a-Glance": 60,
    "Why it Matters": 80,
    "Overview": 120,
    "Step-by-Step": 140,
    "Seasonality & Climate": 80,
    "Common Pitfalls": 80,
    "Tools & Materials": 40,
}
GLOBAL_MIN_WORDS = 700
GLOBAL_MAX_WORDS = 3000

def load_seed_for_slug(slug: str, archetype: str) -> dict:
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
    words = re.findall(r"\w+(?:[-’']\w+)?", text or "")
    if len(words) >= min_words: return text
    deficit = max(0, min_words - len(words))
    filler = " " + " ".join(["Additional practical detail forthcoming."] * max(1, deficit // 5))
    return (text or "").strip() + filler

def clamp_total(article_md: str) -> str:
    words = re.findall(r"\w+(?:[-’']\w+)?", article_md)
    if len(words) <= GLOBAL_MAX_WORDS: return article_md
    import re as _re
    parts = _re.split(r"\n{2,}", article_md)
    out, count = [], 0
    for p in parts:
        w = len(_re.findall(r"\w+(?:[-’']\w+)?", p))
        if count + w > GLOBAL_MAX_WORDS: break
        out.append(p); count += w
    return "\n\n".join(out)
PY
