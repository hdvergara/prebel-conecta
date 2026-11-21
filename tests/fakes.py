"""Deterministic, fast stand-ins for the real ML models, used only in unit tests.

See CONSTITUTION.md "Harness": unit tests must not load real model weights or
hit the network. Both fakes below are drop-in replacements for
sentence_transformers.SentenceTransformer and transformers.pipeline.
"""
import hashlib

import torch


class FakeSentenceTransformer:
    """Same text -> same vector (cos_sim 1.0); different text -> near-orthogonal
    vectors (cos_sim close to 0), via a stable hash. No real embeddings involved,
    so RRHHBot's own threshold/matching logic can be tested deterministically."""

    def __init__(self, *_args, dim=64, **_kwargs):
        self.dim = dim

    def _vector(self, text):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = [digest[i % len(digest)] / 127.5 - 1.0 for i in range(self.dim)]
        values[0] += 1e-6  # guard against an all-zero vector (cos_sim would be NaN)
        vector = torch.tensor(values, dtype=torch.float32)
        return vector / vector.norm()

    def encode(self, texts, convert_to_tensor=True):
        single = isinstance(texts, str)
        items = [texts] if single else list(texts)
        stacked = torch.stack([self._vector(t) for t in items])
        return stacked[0] if single else stacked


class FakeSentimentPipeline:
    """Returns a canned (label, score) per exact input text; a neutral default
    for anything not explicitly configured by the test."""

    def __init__(self, responses=None, default=("3 stars", 0.5)):
        self.responses = responses or {}
        self.default = default

    def __call__(self, text, *_args, **_kwargs):
        label, score = self.responses.get(text, self.default)
        return [{"label": label, "score": score}]
