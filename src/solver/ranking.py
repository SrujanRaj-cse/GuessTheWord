"""Frequency-based ranking for dictionary matches."""

from __future__ import annotations

from rapidfuzz import fuzz
from wordfreq import zipf_frequency


def rank_words(words: list[str], pattern: str, limit: int) -> list[dict[str, str | float]]:
    """Rank exact pattern matches by English frequency and return normalized scores."""
    if not words or limit <= 0:
        return []
    frequencies = [zipf_frequency(word, "en") for word in words]
    max_frequency = max(frequencies) or 1.0
    ranked: list[dict[str, str | float]] = []
    for word, frequency in zip(words, frequencies):
        frequency_score = frequency / max_frequency
        similarity = fuzz.ratio(pattern.replace("_", " "), word) / 100.0
        score = min(1.0, 0.9 * frequency_score + 0.1 * similarity)
        ranked.append({"word": word, "score": round(score, 4)})
    return sorted(ranked, key=lambda item: (-item["score"], item["word"]))[:limit]
