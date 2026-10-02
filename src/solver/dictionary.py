"""Indexed local word source used by the solver."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from config.settings import SolverSettings

_VALID_WORD = re.compile(r"^[a-z]+$")


class DictionaryWordSource:
    """Load words once and match letters plus ``_`` / ``?`` wildcards."""

    def __init__(self, settings: SolverSettings) -> None:
        self._by_length: dict[int, list[str]] = defaultdict(list)
        words = self._load_words(settings.dictionary_path)
        for word in words:
            if settings.min_word_length <= len(word) <= settings.max_word_length:
                self._by_length[len(word)].append(word)

    def _load_words(self, path: Path | None) -> set[str]:
        if path is not None:
            if not path.is_file():
                raise FileNotFoundError(f"Dictionary file not found: {path}")
            return {
                value.strip().lower()
                for value in path.read_text(encoding="utf-8").splitlines()
                if _VALID_WORD.fullmatch(value.strip().lower())
            }
        try:
            from wordfreq import iter_wordlist
        except ImportError as error:
            raise RuntimeError(
                "wordfreq is not installed. Install the solver dependencies from requirements.txt."
            ) from error
        return {
            word.lower()
            for word in iter_wordlist("en", wordlist="best")
            if _VALID_WORD.fullmatch(word.lower())
        }

    def words_matching(self, pattern: str) -> list[str]:
        """Return matching candidates ordered alphabetically before ranking."""
        normalized = pattern.strip().lower().replace("?", "_")
        if not normalized or not _VALID_WORD.fullmatch(normalized.replace("_", "a")):
            return []
        expression = "^" + "".join(
            "." if char == "_" else re.escape(char) for char in normalized
        ) + "$"
        matcher = re.compile(expression)
        return [word for word in self._by_length[len(normalized)] if matcher.fullmatch(word)]
