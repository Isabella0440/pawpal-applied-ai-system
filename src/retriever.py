"""Rank individual care guides by TF-IDF cosine similarity."""

from collections import Counter
from dataclasses import dataclass
import json
from math import log, sqrt
from pathlib import Path
import re


def words(text):
    return re.findall(r"[a-z]+", text.casefold())


@dataclass(frozen=True)
class CareGuide:
    id: str
    species: str
    topics: str
    activity: str
    minutes: int
    guidance: str
    source: str


class Retriever:
    def __init__(self, directory=None):
        directory = directory or Path(__file__).resolve().parents[1] / "data/knowledge_base"
        self.guides = [
            CareGuide(**record, source=path.name)
            for path in sorted(directory.glob("*.json"))
            for record in json.loads(path.read_text(encoding="utf-8"))
        ]
        document_frequency = Counter(
            word for guide in self.guides for word in set(words(guide.topics))
        )
        self.idf = {
            word: 1 + log((1 + len(self.guides)) / (1 + count))
            for word, count in document_frequency.items()
        }
        self.vectors = [self.vector(guide.topics) for guide in self.guides]

    def vector(self, text):
        weights = {
            word: count * self.idf[word]
            for word, count in Counter(words(text)).items()
            if word in self.idf
        }
        norm = sqrt(sum(weight ** 2 for weight in weights.values()))
        return {word: weight / norm for word, weight in weights.items()}

    def retrieve(self, focus, species):
        query = self.vector(focus)
        matches = []
        for guide, vector in zip(self.guides, self.vectors):
            if guide.species in (species.casefold(), "all"):
                score = sum(weight * vector.get(word, 0) for word, weight in query.items())
                if score >= 0.30:
                    matches.append((guide, score))
        return sorted(matches, key=lambda match: (-match[1], match[0].id))
