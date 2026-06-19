"""ManifoldGuard v11 guarded candidate-selection tools.

This module implements the public, package-level version of the mechanisms
recorded in the EXP01-EXP20 technical ledger: semantic shock, literal drift
protection, relation clamps, guarded relation-recall patches, reference-member
geometry override, negation/overclaim checks, and abstention when every
candidate is unsafe.

The implementation is intentionally transparent and reference-bound.  It does
not fact-check against an external knowledge base; it only regulates candidates
against the reference text and optional relation tuples supplied by the caller.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import numpy as np

from .embeddings import embed_texts
from .geometry import geometric_median, shock

THRESHOLD_K = 3.0
THRESHOLD_FLOOR = 0.02
LITERAL_SCORE_WEIGHT = 0.15
LITERAL_BLOCK_THRESHOLD = 1.0

_UNIT_WORDS = {
    "celsius",
    "fahrenheit",
    "kelvin",
    "degree",
    "degrees",
    "meter",
    "meters",
    "metre",
    "metres",
    "kilometer",
    "kilometers",
    "mile",
    "miles",
    "second",
    "seconds",
    "minute",
    "minutes",
    "hour",
    "hours",
    "year",
    "years",
    "kg",
    "g",
    "cm",
    "mm",
    "km",
    "mph",
    "m/s",
    "percent",
    "%",
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "based",
    "be",
    "but",
    "by",
    "called",
    "can",
    "city",
    "commonly",
    "described",
    "does",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "like",
    "mostly",
    "natural",
    "not",
    "of",
    "on",
    "or",
    "roughly",
    "slightly",
    "the",
    "to",
    "use",
    "with",
    "without",
}

_NEGATORS = {
    "not",
    "no",
    "never",
    "doesnt",
    "dont",
    "didnt",
    "isnt",
    "arent",
    "wasnt",
    "werent",
    "cant",
    "cannot",
}
_NEGATION_NORMALIZATIONS = {
    "doesn't": "does not",
    "don't": "do not",
    "didn't": "did not",
    "wasn't": "was not",
    "weren't": "were not",
    "isn't": "is not",
    "aren't": "are not",
    "doesnt": "does not",
    "dont": "do not",
    "didnt": "did not",
    "wasnt": "was not",
    "werent": "were not",
    "isnt": "is not",
    "arent": "are not",
    "cant": "can not",
    "can't": "can not",
    "cannot": "can not",
    "won't": "will not",
    "wont": "will not",
    "wouldn't": "would not",
    "wouldnt": "would not",
    "couldn't": "could not",
    "couldnt": "could not",
    "shouldn't": "should not",
    "shouldnt": "should not",
    "hasn't": "has not",
    "hasnt": "has not",
    "haven't": "have not",
    "havent": "have not",
    "mustn't": "must not",
    "mustnt": "must not",
    "mightn't": "might not",
    "mightnt": "might not",
    "ain't": "are not",
    "aint": "are not",
}
_NEGATION_PREFIX = (
    r"(?:does not|do not|did not|cannot|can not|will not|would not|should not|"
    r"could not|must not|may not|might not|has not|have not|had not|is not|"
    r"are not|was not|were not|doesnt|dont|didnt|arent|isnt|wasnt|werent|cant|wont|"
    r"wouldnt|couldnt|shouldnt|hasnt|havent|mustnt|mightnt|not|never|aint)"
)
_AUXILIARY_SUBJECTS = {
    "does",
    "do",
    "did",
    "can",
    "will",
    "would",
    "should",
    "could",
    "must",
    "may",
    "might",
    "has",
    "have",
    "had",
    "is",
    "are",
    "was",
    "were",
}
_CAPITAL_OF_PREFIXES = (
    "capital of ",
    "capital city of ",
)
_OVERCLAIM_PATTERNS = (
    "fully solved",
    "complete and experimentally verified",
    "final truth",
    "automatically the final",
    "proves gravity has no connection",
    "proves there is no connection",
)
_MONTH_PATTERN = (
    r"(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)"
)
_CHAIN_VERB_LEMMAS = {
    "absorb",
    "exchange",
    "lend",
    "preserve",
    "provide",
    "release",
    "request",
    "store",
    "turn",
    "use",
}

Predicate = str
Relation = Tuple[str, Predicate, str]


@dataclass(frozen=True)
class LiteralDrift:
    """Literal differences between a candidate and its reference manifold."""

    novel_numbers: Tuple[str, ...] = ()
    novel_units: Tuple[str, ...] = ()
    novel_entities: Tuple[str, ...] = ()
    novel_content: Tuple[str, ...] = ()

    @property
    def score(self) -> float:
        return float(
            len(self.novel_numbers)
            + len(self.novel_units)
            + len(self.novel_entities)
            + 0.5 * len(self.novel_content)
        )

    @property
    def has_protected_drift(self) -> bool:
        return bool(self.novel_numbers or self.novel_units or self.novel_entities)


@dataclass
class CandidateEvaluation:
    """Full ManifoldGuard v11 decision record for one candidate."""

    text: str
    pred_hallucinated: bool
    safe_to_emit: bool
    regulator_score: float
    mbt5_shock: float
    threshold: float
    literal_score: float
    clamp_summary: Tuple[str, ...] = ()
    relations: Tuple[Relation, ...] = ()
    literal_drift: LiteralDrift = field(default_factory=LiteralDrift)
    exact_reference_member: bool = False
    negated_relations: Tuple[Relation, ...] = ()


@dataclass
class RegulationResult:
    """Result of regulating a candidate pool."""

    action: str
    emitted_text: Optional[str]
    emitted: Optional[CandidateEvaluation]
    evaluations: List[CandidateEvaluation]


@dataclass
class ReferenceManifold:
    """Reference text, derived literals, relation map, and geometry anchors."""

    references: List[str]
    relations: Set[Relation] = field(default_factory=set)
    negated_relations: Set[Relation] = field(default_factory=set)
    center: Optional[np.ndarray] = None
    threshold: float = THRESHOLD_FLOOR
    normalized_reference_members: Set[str] = field(default_factory=set)
    numbers: Set[str] = field(default_factory=set)
    units: Set[str] = field(default_factory=set)
    entities: Set[str] = field(default_factory=set)
    content_tokens: Set[str] = field(default_factory=set)

    @classmethod
    def from_texts(
        cls,
        references: Iterable[str],
        *,
        relations: Optional[Iterable[Relation]] = None,
        threshold_k: float = THRESHOLD_K,
        threshold_floor: float = THRESHOLD_FLOOR,
        use_embeddings: bool = True,
    ) -> "ReferenceManifold":
        refs = [r.strip() for r in references if r and r.strip()]
        supplied_relations = {_normalize_relation(r) for r in (relations or [])}
        extracted_relations = (
            set().union(*(extract_relations(r) for r in refs)) if refs else set()
        )
        extracted_negated_relations = (
            set().union(*(_extract_negated_relations(r) for r in refs)) if refs else set()
        )
        relation_set = supplied_relations | extracted_relations

        center: Optional[np.ndarray] = None
        threshold = threshold_floor
        if use_embeddings and refs:
            embeddings = embed_texts(refs)
            center = embeddings[0] if len(embeddings) == 1 else geometric_median(embeddings)
            distances = np.asarray([shock(e, center) for e in embeddings])
            median = float(np.median(distances))
            mad = float(np.median(np.abs(distances - median)))
            threshold = max(threshold_floor, median + threshold_k * mad)

        joined = "\n".join(refs)
        return cls(
            references=refs,
            relations=relation_set,
            negated_relations=extracted_negated_relations,
            center=center,
            threshold=threshold,
            normalized_reference_members={normalize_text(r) for r in refs},
            numbers=set(_numbers(joined)),
            units=set(_units(joined)),
            entities=set(_entities(joined)),
            content_tokens=set(_content_tokens(joined)),
        )


def normalize_text(text: str) -> str:
    """Normalize text for exact reference-member comparisons."""

    return " ".join(text.lower().translate(str.maketrans("", "", string.punctuation)).split())


def extract_relations(text: str) -> Set[Relation]:
    """Extract simple copular and non-copular relation claims from text.

    The parser is deliberately small and auditable.  It targets the relation
    shapes recorded in EXP09-EXP20: capitals/classifications, orbits,
    contains, produces/releases/stores/converts, has-count, and historical-date
    assertions such as signed/occurred/adopted/landed in a year.
    """

    normalized = normalize_text(text)
    if not normalized:
        return set()

    relations: Set[Relation] = set()
    relations.update(_extract_temporal_binding_relations(normalized))
    relations.update(_extract_shared_subject_verb_chain(normalized))
    for segment in _split_relation_segments(normalized):
        relations.update(_extract_relations_from_segment(segment))
    return {_normalize_relation(r) for r in relations if r[0] and r[2]}


def _extract_negated_relations(text: str) -> Set[Relation]:
    """Extract explicit negated relation claims with normalized polarity."""

    normalized = _normalize_negation_text(text)
    if not normalized:
        return set()

    negated: Set[Relation] = set()
    negated.update(_extract_negated_relations_from_segment(normalized))
    for segment in _split_relation_segments(normalized):
        negated.update(_extract_negated_relations_from_segment(segment))
    return {_normalize_relation(r) for r in negated if r[0] and r[2]}


def _split_relation_segments(text: str) -> List[str]:
    raw_segments = re.split(r"\b(?: and | but |, )\b", text)
    return [segment.strip() for segment in raw_segments if segment.strip()]


def _extract_relations_from_segment(segment: str) -> Set[Relation]:
    relations: Set[Relation] = set()
    relations.update(_extract_temporal_binding_relations(segment))
    shared_subject_relations = _extract_shared_subject_verb_chain(segment)
    relations.update(shared_subject_relations)

    m = re.search(r"\bcapital of ([a-z][a-z ]+?) is ([a-z][a-z ]+?)(?:$| and | but )", segment)
    if m:
        relations.add((_clean_span(m.group(1)), "capital", _clean_span(m.group(2))))
    m = re.search(r"\b([a-z][a-z ]+?)s capital (?:city )?is ([a-z][a-z ]+?)(?:$| and | but )", segment)
    if m:
        relations.add((_clean_span(m.group(1)), "capital", _clean_span(m.group(2))))
    m = re.search(r"\b([a-z][a-z ]+?) is (?:the )?capital (?:city )?of ([a-z][a-z ]+?)(?:$| and | but )", segment)
    if m:
        relations.add((_clean_span(m.group(2)), "capital", _clean_span(m.group(1))))

    copular_pattern = (
        r"\b([a-z][a-z ]+?) (?:is|are|was|were) (?:a |an |the )?"
        r"([a-z0-9][a-z0-9 ]+?)(?:$| and | but )"
    )
    for m in re.finditer(copular_pattern, segment):
        subj, obj = _clean_span(m.group(1)), _clean_span(m.group(2))
        if (
            subj
            and obj
            and "capital of" not in subj
            and not obj.startswith(("capital of", "capital city of"))
            and subj != "it"
            and not _looks_like_temporal_value(obj)
            and len(subj.split()) <= 5
            and len(obj.split()) <= 8
        ):
            relations.add((subj, "is", obj))

    verbs = (
        "orbits|orbit|contains|contain|contain|produces|produce|"
        "releases|release|stores|store|converts|convert|improves|improve|"
        "uses|use|needs|need|has|have|is|are|was|were|needs|improved|produces|produced|"
        "contains|contained|released|using|lends|lend|preserves|preserve|"
        "absorbs|absorb|exchanges|exchange|provides|provide|requests|request|"
        "turns|turn"
    )
    pattern = rf"\b([a-z][a-z ]+?) ({verbs}) ([a-z][a-z0-9 ]+?)(?=$| and (?:{verbs}) )"
    for m in re.finditer(pattern, segment):
        subj = _clean_span(m.group(1))
        pred = _lemma_predicate(m.group(2))
        obj = _clean_span(m.group(3))
        if (
            subj
            and obj
            and subj not in {"and", "or"}
            and not (pred == "is" and _is_capital_of_predicate(obj))
            and not (shared_subject_relations and _contains_chain_verb(obj))
        ):
            relations.add((subj, pred, obj))

    coord = rf"\b([a-z][a-z ]+?) ({verbs}) ([a-z][a-z0-9 ]+?) and ({verbs}) ([a-z][a-z0-9 ]+?)(?:$| and | but )"
    for m in re.finditer(coord, segment):
        subj = _clean_span(m.group(1))
        relations.add((subj, _lemma_predicate(m.group(2)), _clean_span(m.group(3))))
        relations.add((subj, _lemma_predicate(m.group(4)), _clean_span(m.group(5))))

    for m in re.finditer(
        r"\b([a-z][a-z ]+?) has ([a-z0-9]+) ([a-z][a-z ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add(
            (_clean_span(m.group(1)), f"has_count:{m.group(3).strip()}", _clean_span(m.group(2)))
        )

    for m in re.finditer(
        r"\b([a-z][a-z ]+?) "
        r"(was signed|occurred|was adopted|landed [a-z ]*moon) in (\d{3,4})",
        segment,
    ):
        relations.add((_clean_span(m.group(1)), _lemma_predicate(m.group(2)), m.group(3)))

    return relations


def _contains_chain_verb(span: str) -> bool:
    return any(_lemma_predicate(token) in _CHAIN_VERB_LEMMAS for token in span.split())


def _extract_shared_subject_verb_chain(text: str) -> Set[Relation]:
    tokens = normalize_text(text).split()
    verb_indexes = [
        index
        for index, token in enumerate(tokens)
        if _lemma_predicate(token) in _CHAIN_VERB_LEMMAS
    ]
    if len(verb_indexes) < 2 or verb_indexes[0] == 0:
        return set()

    subject = _clean_span(" ".join(tokens[: verb_indexes[0]]))
    if not subject or len(subject.split()) > 5:
        return set()

    relations: Set[Relation] = set()
    for position, verb_index in enumerate(verb_indexes):
        next_verb_index = (
            verb_indexes[position + 1]
            if position + 1 < len(verb_indexes)
            else len(tokens)
        )
        object_tokens = tokens[verb_index + 1 : next_verb_index]
        if object_tokens and object_tokens[-1] == "and":
            object_tokens = object_tokens[:-1]
        if "and" in object_tokens or "but" in object_tokens:
            return set()
        obj = _clean_span(" ".join(object_tokens))
        if obj:
            relations.add((subject, _lemma_predicate(tokens[verb_index]), obj))
    return relations


def _extract_temporal_binding_relations(text: str) -> Set[Relation]:
    relations: Set[Relation] = set()

    last_subject = ""
    for m in re.finditer(
        r"\bin (\d{4}) ([a-z][a-z ]+?) (?:was|were) "
        r"([a-z0-9]+(?: [a-z]+)?)(?=$| and in \d{4}\b| in \d{4}\b| and | but )",
        text,
    ):
        year = m.group(1)
        subject = _clean_span(m.group(2))
        if subject == "it" and last_subject:
            subject = last_subject
        elif subject != "it":
            last_subject = subject
        value = _clean_span(m.group(3))
        if subject and value:
            relations.add((f"{subject} in {year}", "temporal_value", value))

    reverse_subjects: List[Tuple[int, str]] = []
    for m in re.finditer(
        r"\b([a-z][a-z ]+?) (?:was|were) ([a-z0-9]+(?: [a-z]+)?) in (\d{4})",
        text,
    ):
        subject = _clean_span(m.group(1))
        value = _clean_span(m.group(2))
        year = m.group(3)
        if subject and value:
            relations.add((f"{subject} in {year}", "temporal_value", value))
            reverse_subjects.append((m.end(), subject))
    for offset, subject in reverse_subjects:
        trailing = text[offset:]
        for m in re.finditer(r"\band ([a-z0-9]+(?: [a-z]+)?) in (\d{4})", trailing):
            value = _clean_span(m.group(1))
            year = m.group(2)
            if value:
                relations.add((f"{subject} in {year}", "temporal_value", value))

    for m in re.finditer(r"\b([a-z][a-z ]+? office) opened in (\d{4})", text):
        relations.add((_clean_span(m.group(1)), "opened_in", m.group(2)))

    for m in re.finditer(
        r"\bversion ([0-9]+) added ([a-z][a-z ]+? support)(?=$| version [0-9]+| and | but )",
        text,
    ):
        relations.add((f"version {m.group(1)}", "added", _clean_span(m.group(2))))

    for m in re.finditer(
        r"\b(q[0-9]+ [a-z][a-z ]+?) (?:was|were) ([0-9]+ [a-z]+)(?=$| q[0-9]+ | and | but )",
        text,
    ):
        relations.add((_clean_span(m.group(1)), "temporal_value", _clean_span(m.group(2))))

    date = rf"{_MONTH_PATTERN} [0-9]+"
    for m in re.finditer(rf"\b([a-z][a-z ]+?) starts on ({date})", text):
        subject = _clean_span(m.group(1))
        relations.add((subject, "starts_on", _clean_span(m.group(2))))
        trailing = text[m.end():]
        end = re.search(rf"\b(?:and )?ends on ({date})", trailing)
        if end:
            relations.add((subject, "ends_on", _clean_span(end.group(1))))
    for m in re.finditer(rf"\b([a-z][a-z ]+?) ends on ({date})", text):
        relations.add((_clean_span(m.group(1)), "ends_on", _clean_span(m.group(2))))

    return relations


def _extract_negated_relations_from_segment(segment: str) -> Set[Relation]:
    """Extract explicit negated relation claims."""

    relations: Set[Relation] = set()
    verbs = (
        "orbits|orbit|contains|contain|produces|produce|releases|release|stores|store|"
        "converts|convert|improves|improve|uses|use|needs|need|has|have|included|"
        "includes|include|allows|allow|approved|approves|approve|is|are|was|were|"
        "stored|release|produce|released|using|adopted|signed|occurred|landed"
    )
    shared_subject_intro = (
        "orbits|orbit|contains|contain|produces|produce|releases|release|stores|store|"
        "converts|convert|improves|improve|uses|use|needs|need|has|have|included|"
        "includes|include|allows|allow|approved|approves|approve|is|are|was|were"
    )

    for m in re.finditer(
        rf"\b([a-z][a-z ]+?) (?:{shared_subject_intro}) [a-z0-9 ]+? "
        rf"(?:and|but|,) (?:{_NEGATION_PREFIX}) ({verbs}) ([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add(
            (
                _clean_span(m.group(1)),
                _lemma_predicate(m.group(2)),
                _clean_span(m.group(3)),
            )
        )

    for m in re.finditer(
        rf"\b([a-z][a-z ]+?) (?:{shared_subject_intro}) [a-z0-9 ]+? "
        r"(?:and|but|,) no ([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add((_clean_span(m.group(1)), "has", _clean_span(m.group(2))))

    for m in re.finditer(
        r"\b([a-z][a-z ]+?) (?:included|includes|include) [a-z0-9 ]+? "
        r"(?:and|but|,) excluded ([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add((_clean_span(m.group(1)), "include", _clean_span(m.group(2))))

    for m in re.finditer(
        r"\b([a-z][a-z0-9 ]+?) (?:was|were|is|are) excluded from ([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add((_clean_span(m.group(2)), "include", _clean_span(m.group(1))))

    for m in re.finditer(
        r"\b([a-z][a-z ]+?) lacks? (?:a |an |the )?([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add((_clean_span(m.group(1)), "has", _clean_span(m.group(2))))

    copular_pattern = (
        rf"\b([a-z][a-z ]+?) (?:{_NEGATION_PREFIX}) (?:a |an |the )?"
        r"([a-z0-9][a-z0-9 ]+?)(?:$| and | but )"
    )
    for m in re.finditer(copular_pattern, segment):
        subj, obj = _clean_span(m.group(1)), _clean_span(m.group(2))
        if (
            subj
            and obj
            and subj not in _AUXILIARY_SUBJECTS
            and len(subj.split()) <= 5
            and len(obj.split()) <= 8
        ):
            relations.add((subj, "is", obj))

    pattern = (
        r"\b([a-z][a-z ]+?) "
        rf"(?:{_NEGATION_PREFIX}) "
        rf"({verbs}) ([a-z][a-z0-9 ]+?)(?=$| and (?:{verbs}) )"
    )
    for m in re.finditer(pattern, segment):
        subj = _clean_span(m.group(1))
        pred = _lemma_predicate(m.group(2))
        obj = _clean_span(m.group(3))
        if (
            subj
            and obj
            and subj not in {"and", "or"}
            and not (pred == "is" and _is_capital_of_predicate(obj))
        ):
            relations.add((subj, pred, obj))

    for m in re.finditer(
        r"\b([a-z][a-z ]+?) has no ([a-z][a-z0-9 ]+?)(?:$| and | but |,)",
        segment,
    ):
        relations.add((_clean_span(m.group(1)), "has", _clean_span(m.group(2))))

    return relations


def evaluate_candidate(
    candidate: str,
    reference: Union[ReferenceManifold, Iterable[str]],
    *,
    use_embeddings: bool = True,
) -> CandidateEvaluation:
    """Evaluate one candidate against a supplied reference manifold."""

    manifold = (
        reference
        if isinstance(reference, ReferenceManifold)
        else ReferenceManifold.from_texts(reference, use_embeddings=use_embeddings)
    )
    exact_member = normalize_text(candidate) in manifold.normalized_reference_members
    candidate_relations = extract_relations(candidate)
    candidate_negations = _extract_negated_relations(candidate)
    literal = literal_drift(candidate, manifold)

    mbt5_shock = 0.0
    if use_embeddings and manifold.center is not None:
        mbt5_shock = shock(embed_texts([candidate])[0], manifold.center)

    clamps: List[str] = []
    if literal.novel_numbers:
        clamps.append("protected_number")
    if literal.novel_units:
        clamps.append("protected_unit")
    if literal.novel_entities:
        clamps.append("protected_entity")
    if literal.has_protected_drift:
        clamps.append("protected_literal_drift")
    if literal.score >= LITERAL_BLOCK_THRESHOLD:
        clamps.append("final_literal_block")
    if _has_unsupported_content(candidate, manifold, literal):
        clamps.append("content_clamp_flag")
    if _has_overclaim(candidate):
        clamps.append("overclaim_flag")
    if _has_unsupported_negation(candidate, manifold, candidate_negations):
        clamps.append("negated_positive_support_clamp")
    if _has_negated_reference_assertion(
        candidate,
        candidate_relations,
        candidate_negations,
        manifold.negated_relations,
    ):
        clamps.append("negated_reference_relation_clamp")

    relation_clamps = _relation_clamps(candidate_relations, manifold.relations)
    clamps.extend(relation_clamps)

    geometric_block = mbt5_shock > manifold.threshold
    if geometric_block:
        clamps.append("final_geometric_block")

    if exact_member:
        clamps.append("exact_reference_member")
        if geometric_block and not _hard_clamps_without_geometry(clamps):
            clamps.remove("final_geometric_block")
            clamps.append("reference_member_geometry_override")
            geometric_block = False

    hard_block = _hard_clamps_without_geometry(clamps)
    pred_hallucinated = hard_block or geometric_block
    regulator_score = mbt5_shock + LITERAL_SCORE_WEIGHT * literal.score

    return CandidateEvaluation(
        text=candidate,
        pred_hallucinated=pred_hallucinated,
        safe_to_emit=not pred_hallucinated,
        regulator_score=regulator_score,
        mbt5_shock=mbt5_shock,
        threshold=manifold.threshold,
        literal_score=literal.score,
        clamp_summary=tuple(dict.fromkeys(clamps)) or ("none",),
        relations=tuple(sorted(candidate_relations)),
        literal_drift=literal,
        exact_reference_member=exact_member,
        negated_relations=tuple(sorted(candidate_negations)),
    )


def regulate_candidates(
    candidates: Sequence[str],
    references: Iterable[str],
    *,
    relations: Optional[Iterable[Relation]] = None,
    use_embeddings: bool = True,
) -> RegulationResult:
    """Emit the safest supported candidate, or block if every candidate is unsafe."""

    manifold = ReferenceManifold.from_texts(
        references, relations=relations, use_embeddings=use_embeddings
    )
    evaluations = [
        evaluate_candidate(c, manifold, use_embeddings=use_embeddings) for c in candidates
    ]
    safe = [e for e in evaluations if e.safe_to_emit]
    if not safe:
        return RegulationResult("block", None, None, evaluations)
    emitted = min(safe, key=lambda e: e.regulator_score)
    return RegulationResult("emit", emitted.text, emitted, evaluations)


def literal_drift(candidate: str, manifold: ReferenceManifold) -> LiteralDrift:
    """Compute number/unit/entity/content novelty against reference text."""

    cand_numbers = set(_numbers(candidate))
    cand_units = set(_units(candidate))
    cand_entities = {
        entity
        for entity in _entities(candidate)
        if not _is_sentence_initial_content_entity(
            candidate,
            entity,
            manifold.content_tokens,
        )
    }
    cand_content = set(_content_tokens(candidate))
    return LiteralDrift(
        novel_numbers=tuple(sorted(cand_numbers - manifold.numbers)),
        novel_units=tuple(sorted(cand_units - manifold.units)),
        novel_entities=tuple(sorted(cand_entities - manifold.entities)),
        novel_content=tuple(sorted(cand_content - manifold.content_tokens)),
    )


def _relation_clamps(
    candidate_relations: Set[Relation], reference_relations: Set[Relation]
) -> List[str]:
    clamps: List[str] = []
    if not candidate_relations or not reference_relations:
        return clamps

    ref_subjects = {r[0] for r in reference_relations}
    ref_objects = {r[2] for r in reference_relations}
    ref_participants = ref_subjects | ref_objects
    ref_predicates = {r[1] for r in reference_relations}

    for rel in candidate_relations:
        if rel in reference_relations:
            continue
        subj, pred, obj = rel
        if (obj, pred, subj) in reference_relations:
            clamps.extend(
                ["role_swapped_relation_clamp", "known_participant_unsupported_relation_clamp"]
            )
        elif pred in ref_predicates and (subj in ref_participants or obj in ref_participants):
            clamps.append("known_participant_unsupported_relation_clamp")
        elif subj in ref_participants and pred not in ref_predicates:
            clamps.extend(
                ["missed_predicate_relation_clamp", "known_participant_unsupported_relation_clamp"]
            )
        if pred.startswith(("was signed", "occurred", "was adopted", "landed")) or obj.isdigit():
            matching_events = [
                r for r in reference_relations if r[0] == subj and r[1] == pred
            ]
            if matching_events and rel not in reference_relations:
                clamps.append("historical_date_relation_clamp")

    if clamps:
        clamps.extend(
            ["guarded_known_participant_unsupported_relation_clamp", "exp19b_guarded_patch_clamp"]
        )
    return clamps


def _hard_clamps_without_geometry(clamps: Sequence[str]) -> bool:
    non_hard = {
        "none",
        "final_geometric_block",
        "exact_reference_member",
        "reference_member_geometry_override",
    }
    return any(c not in non_hard for c in clamps)


def _has_overclaim(text: str) -> bool:
    normalized = normalize_text(text)
    return any(pattern in normalized for pattern in _OVERCLAIM_PATTERNS)


def _normalize_negation_text(text: str) -> str:
    normalized = text.lower()
    for source, replacement in _NEGATION_NORMALIZATIONS.items():
        normalized = re.sub(rf"\\b{re.escape(source)}\\b", replacement, normalized)
    return normalize_text(normalized)


def _has_unsupported_negation(
    text: str,
    manifold: ReferenceManifold,
    candidate_negations: Optional[Set[Relation]] = None,
) -> bool:
    if not manifold.relations and not manifold.negated_relations:
        return False

    negations = candidate_negations or _extract_negated_relations(text)
    if not negations:
        return False

    ref_relations = manifold.relations
    ref_negated_relations = manifold.negated_relations
    ref_subjects = {r[0] for r in ref_relations}
    ref_objects = {r[2] for r in ref_relations}
    ref_predicates = {r[1] for r in ref_relations}
    for negation in negations:
        if _negation_supported_by_reference(text, negation, ref_negated_relations):
            continue
        subj, pred, obj = negation
        if (subj, pred, obj) in ref_relations:
            return True
        if (obj, pred, subj) in ref_relations:
            return True
        if pred in ref_predicates and (subj in ref_subjects or obj in ref_objects):
            return True
    return False


def _has_negated_reference_assertion(
    text: str,
    candidate_relations: Set[Relation],
    candidate_negations: Set[Relation],
    reference_negated_relations: Set[Relation],
) -> bool:
    if not reference_negated_relations:
        return False

    for reference_negation in reference_negated_relations:
        if _negation_supported_by_reference(text, reference_negation, candidate_negations):
            continue
        if any(
            _relations_match(candidate_relation, reference_negation, text)
            for candidate_relation in candidate_relations
        ):
            return True
        obj = reference_negation[2]
        if _mentions_object(text, obj) and not _object_has_negation_nearby(text, obj):
            return True
    return False


def _negation_supported_by_reference(
    text: str,
    negation: Relation,
    reference_negated_relations: Set[Relation],
) -> bool:
    return any(
        _relations_match(negation, reference_negation, text)
        for reference_negation in reference_negated_relations
    )


def _relations_match(left: Relation, right: Relation, text: str = "") -> bool:
    left_subj, left_pred, left_obj = left
    right_subj, right_pred, right_obj = right
    if left == right:
        return True
    if left_pred != right_pred or left_obj != right_obj:
        return False
    if left_subj == right_subj:
        return True
    if left_subj in _AUXILIARY_SUBJECTS and right_subj in normalize_text(text).split():
        return True
    return False


def _mentions_object(text: str, obj: str) -> bool:
    normalized = normalize_text(text)
    return bool(obj and re.search(rf"\b{re.escape(obj)}\b", normalized))


def _looks_like_temporal_value(value: str) -> bool:
    return bool(
        re.search(r"\b\d{3,4}\b", value)
        or re.search(r"\b\d+(?: mm| cm| m| km| units?| hours?| minutes?| seconds?)\b", value)
    )


def _is_sentence_initial_content_entity(
    text: str,
    entity: str,
    reference_content_tokens: Set[str],
) -> bool:
    normalized_entity = normalize_text(entity)
    if " " in normalized_entity or normalized_entity not in reference_content_tokens:
        return False
    tokens = normalize_text(text).split()
    return bool(tokens and tokens[0] == normalized_entity)


def _object_has_negation_nearby(text: str, obj: str) -> bool:
    normalized = _normalize_negation_text(text)
    if not obj or not _mentions_object(normalized, obj):
        return False
    escaped = re.escape(obj)
    patterns = (
        rf"\bno {escaped}\b",
        rf"\bwithout {escaped}\b",
        rf"\blacks? (?:a |an |the )?{escaped}\b",
        rf"\bomits? {escaped}\b",
        rf"\b(?:{_NEGATION_PREFIX}) (?:[a-z]+ ){{0,4}}{escaped}\b",
        rf"\b{escaped} (?:was |were |is |are )?excluded\b",
        rf"\bexcluded {escaped}\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _contains_negation(text: str) -> bool:
    normalized = _normalize_negation_text(text)
    tokens = set(normalized.split())
    return bool(tokens & _NEGATORS) or " not " in f" {normalized} "


def _has_unsupported_content(candidate: str, manifold: ReferenceManifold, literal: LiteralDrift) -> bool:
    if not literal.novel_content:
        return False
    # Keep the content clamp guarded to avoid blocking ordinary paraphrase words.
    return len(literal.novel_content) >= 3 or bool(literal.has_protected_drift)


def _numbers(text: str) -> List[str]:
    return [n.lower() for n in re.findall(r"\b\d+(?:\.\d+)?\b|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|ninety|hundred|thousand)\b", text.lower())]


def _units(text: str) -> List[str]:
    tokens = normalize_text(text).split()
    return [t for t in tokens if t in _UNIT_WORDS]


def _entities(text: str) -> List[str]:
    entities = []
    for match in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text):
        value = _clean_span(match.group(0).lower())
        if value and value not in {"the", "a", "an"}:
            entities.append(value)
    return entities


def _content_tokens(text: str) -> List[str]:
    tokens = normalize_text(text).split()
    return [t for t in tokens if len(t) > 3 and t not in _STOPWORDS and not t.isdigit()]


def _clean_span(value: str) -> str:
    tokens = [t for t in value.strip().split() if t not in {"the", "a", "an"}]
    return " ".join(tokens[-5:]).strip()


def _lemma_predicate(predicate: str) -> str:
    p = predicate.strip().lower()
    mapping: Dict[str, str] = {
        "is": "is",
        "are": "is",
        "was": "is",
        "were": "is",
        "orbits": "orbit",
        "orbit": "orbit",
        "orbiting": "orbit",
        "contains": "contain",
        "contain": "contain",
        "contained": "contain",
        "includes": "include",
        "include": "include",
        "included": "include",
        "allows": "allow",
        "allow": "allow",
        "approved": "approve",
        "approves": "approve",
        "approve": "approve",
        "produces": "produce",
        "produce": "produce",
        "produced": "produce",
        "releases": "release",
        "release": "release",
        "released": "release",
        "lends": "lend",
        "lend": "lend",
        "preserves": "preserve",
        "preserve": "preserve",
        "absorbs": "absorb",
        "absorb": "absorb",
        "exchanges": "exchange",
        "exchange": "exchange",
        "provides": "provide",
        "provide": "provide",
        "requests": "request",
        "request": "request",
        "turns": "turn",
        "turn": "turn",
        "stores": "store",
        "store": "store",
        "stored": "store",
        "converts": "convert",
        "convert": "convert",
        "converted": "convert",
        "improves": "improve",
        "improve": "improve",
        "improved": "improve",
        "uses": "use",
        "use": "use",
        "used": "use",
        "needs": "need",
        "need": "need",
        "needed": "need",
        "has": "has",
        "have": "has",
        "signed": "signed",
        "occurred": "occurred",
        "adopted": "adopted",
    }
    return mapping.get(p, p)


def _normalize_relation(relation: Relation) -> Relation:
    subj, pred, obj = relation
    return (_clean_span(normalize_text(subj)), _lemma_predicate(normalize_text(pred)), _clean_span(normalize_text(obj)))


def _is_capital_of_predicate(value: str) -> bool:
    return value.startswith(_CAPITAL_OF_PREFIXES)
