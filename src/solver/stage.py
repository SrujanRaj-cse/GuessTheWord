"""Subscribe to OCR patterns and publish ranked word candidates."""

from __future__ import annotations

from config.settings import SolverSettings
from core.events import EventBus, PatternChangedEvent, ResultChangedEvent
from solver.dictionary import DictionaryWordSource
from solver.ranking import rank_words


class SolverStage:
    """Match OCR patterns against a cached dictionary and rank the results."""

    def __init__(self, bus: EventBus, settings: SolverSettings) -> None:
        self._bus = bus
        self._settings = settings
        self._source = DictionaryWordSource(settings)
        bus.subscribe(PatternChangedEvent, self._on_pattern)

    def _on_pattern(self, event: PatternChangedEvent) -> None:
        candidates = []
        if event.pattern:
            words = self._source.words_matching(event.pattern)
            candidates = rank_words(words, event.pattern, self._settings.max_candidates)
        self._bus.publish(ResultChangedEvent(candidates=candidates))
