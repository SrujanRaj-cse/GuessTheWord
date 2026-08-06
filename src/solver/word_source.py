"""Dictionary / word list plug-in interface (Phase 5+)."""

from __future__ import annotations

from typing import Protocol


class WordSource(Protocol):
    """English, game-specific, custom, or remote word lists."""

    def words_matching(self, pattern: str) -> list[str]:
        """Return dictionary words matching the pattern (``_`` = wildcard)."""
        ...
