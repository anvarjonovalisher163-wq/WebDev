import re
from pathlib import Path

SEED_PATTERNS_PATH = Path(__file__).resolve().parent.parent.parent / "patterns" / "seed_patterns.txt"


def _load_seed_patterns(path: Path) -> list[str]:
    if not path.exists():
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


class PatternService:
    """Bepul, tez qatlam: standart va guruhga xos kalit so'z/regex'lar bo'yicha tekshiradi."""

    def __init__(self, seed_patterns: list[str] | None = None) -> None:
        raw = seed_patterns if seed_patterns is not None else _load_seed_patterns(SEED_PATTERNS_PATH)
        self._seed_compiled = self._compile_all(raw)

    @staticmethod
    def _compile_all(raw_patterns: list[str]) -> list[re.Pattern]:
        compiled = []
        for raw in raw_patterns:
            try:
                compiled.append(re.compile(raw, re.IGNORECASE | re.UNICODE))
            except re.error:
                # Noto'g'ri regex kiritilgan bo'lsa, uni literal so'z sifatida ishlatamiz.
                compiled.append(re.compile(re.escape(raw), re.IGNORECASE | re.UNICODE))
        return compiled

    def match(self, text: str, group_patterns: list[str] | None = None) -> str | None:
        """Mos kelgan birinchi pattern matnini qaytaradi, aks holda None."""
        if not text:
            return None
        for pattern in self._seed_compiled:
            if pattern.search(text):
                return pattern.pattern
        for raw in group_patterns or []:
            try:
                compiled = re.compile(raw, re.IGNORECASE | re.UNICODE)
            except re.error:
                compiled = re.compile(re.escape(raw), re.IGNORECASE | re.UNICODE)
            if compiled.search(text):
                return raw
        return None
