"""HtmlExtractor — a deterministic extractor for HTML artifacts.

Uses only the standard library (``html.parser``) to extract a useful, deterministic
set of candidates from an HTML payload: the page title/``h1`` as a Brand and Section,
headings as Sections, buttons and CTA-classed links as CTAs, ``<nav>`` as Navigation,
and ``<footer>`` as a Footer — with a piece of evidence for each. It is intentionally
conservative; richer extraction (vision/LLM) is a *different* adapter behind the same
port, so this can be swapped without touching the pipeline.
"""

from __future__ import annotations

from html.parser import HTMLParser

from research.domain.collection.artifact import RawArtifact
from research.domain.collection.extraction import (
    CandidateEntity,
    CandidateEvidence,
    CandidateRelationship,
    RawExtraction,
)
from research.domain.shared.value_objects import (
    ArtifactKind,
    Confidence,
    EntityType,
    RelationshipType,
    ResearchCategory,
)

__all__ = ["HtmlExtractor"]

_HEADING_TAGS = {"h1", "h2", "h3"}
_CTA_TAGS = {"button"}


class _Collector(HTMLParser):
    """Collects notable elements from an HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._current_attrs: dict[str, str] = {}
        self.title = ""
        self.headings: list[tuple[str, str]] = []  # (tag, text)
        self.ctas: list[str] = []
        self.has_nav = False
        self.has_footer = False
        self._capture = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        self._stack.append(tag)
        self._current_attrs = {k: (v or "") for k, v in attrs}
        if tag == "nav":
            self.has_nav = True
        if tag == "footer":
            self.has_footer = True
        if tag in _HEADING_TAGS or tag == "title" or tag in _CTA_TAGS or tag == "a":
            self._capture = ""

    def handle_data(self, data: str) -> None:
        if self._stack and self._stack[-1] in (_HEADING_TAGS | _CTA_TAGS | {"title", "a"}):
            self._capture += data

    def handle_endtag(self, tag: str) -> None:
        text = " ".join(self._capture.split()).strip()
        if tag == "title" and text:
            self.title = text
        elif tag in _HEADING_TAGS and text:
            self.headings.append((tag, text))
        elif tag == "button" and text:
            self.ctas.append(text)
        elif tag == "a" and "cta" in self._current_attrs.get("class", "").lower() and text:
            self.ctas.append(text)
        self._capture = ""
        if self._stack:
            self._stack.pop()


class HtmlExtractor:
    """Extracts a deterministic candidate set from HTML artifacts."""

    def supports(self, kind: ArtifactKind) -> bool:
        return kind is ArtifactKind.HTML

    async def extract(self, artifact: RawArtifact) -> RawExtraction:
        collector = _Collector()
        collector.feed(artifact.payload)

        entities: list[CandidateEntity] = []
        evidence: list[CandidateEvidence] = []
        relationships: list[CandidateRelationship] = []

        brand_label = collector.title
        if brand_label:
            entities.append(CandidateEntity(type=EntityType.BRAND, label=brand_label, confidence=Confidence.of(0.7)))
            evidence.append(CandidateEvidence(claim=f"Brand/title is {brand_label!r}", confidence=Confidence.of(0.7),
                                              category=ResearchCategory.WEBSITE, snippet=brand_label))

        for _tag, text in collector.headings:
            entities.append(CandidateEntity(type=EntityType.SECTION, label=text, confidence=Confidence.of(0.6)))
            evidence.append(CandidateEvidence(claim=f"Section heading: {text!r}", confidence=Confidence.of(0.6),
                                              category=ResearchCategory.WEBSITE, snippet=text))

        for cta_text in collector.ctas:
            entities.append(CandidateEntity(type=EntityType.CTA, label=cta_text, confidence=Confidence.of(0.7)))
            evidence.append(CandidateEvidence(claim=f"CTA present: {cta_text!r}", confidence=Confidence.of(0.7),
                                              category=ResearchCategory.WEBSITE, snippet=cta_text))
            if brand_label:
                relationships.append(CandidateRelationship(type=RelationshipType.HAS_CTA,
                    source_label=brand_label, target_label=cta_text, confidence=Confidence.of(0.6)))

        if collector.has_nav:
            entities.append(CandidateEntity(type=EntityType.NAVIGATION, label="navigation", confidence=Confidence.of(0.6)))
            evidence.append(CandidateEvidence(claim="A primary navigation is present.", confidence=Confidence.of(0.6),
                                              category=ResearchCategory.WEBSITE))
        if collector.has_footer:
            entities.append(CandidateEntity(type=EntityType.FOOTER, label="footer", confidence=Confidence.of(0.6)))
            evidence.append(CandidateEvidence(claim="A footer is present.", confidence=Confidence.of(0.6),
                                              category=ResearchCategory.WEBSITE))

        return RawExtraction(artifact_id=artifact.id, entities=tuple(entities),
                             evidence=tuple(evidence), relationships=tuple(relationships))
