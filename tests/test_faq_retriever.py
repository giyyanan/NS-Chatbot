"""
Unit tests for backend/coded_tools/faq_retriever.py: ranking/filtering logic
in retrieve()/retrieve_with_timing(), and FaqRetriever's tool-output
formatting. faqs/_normed_matrix and the Ollama embed call are all mocked --
these tests never touch Ollama or the real FAQ dataset.
"""

import asyncio
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "coded_tools"))

import faq_index  # noqa: E402  pylint: disable=wrong-import-position
import faq_retriever  # noqa: E402  pylint: disable=wrong-import-position


class FakeEmbedClient:
    """Stand-in for the Ollama client: always returns the same query vector."""

    def __init__(self, vector):
        self.vector = vector
        self.calls = []

    def embed(self, model, input):  # noqa: A002 (matches ollama.Client.embed's signature)
        self.calls.append(input)
        return {"embeddings": [self.vector]}


def make_faqs(n):
    return [
        {"question": f"Q{i}", "answer": f"A{i}", "category": f"cat{i}"}
        for i in range(n)
    ]


@pytest.fixture
def three_faqs(monkeypatch):
    monkeypatch.setattr(faq_retriever, "faqs", make_faqs(3))
    monkeypatch.setattr(faq_retriever, "_normed_matrix", np.eye(3, dtype=np.float32))


def test_retrieve_with_timing_no_faqs(monkeypatch):
    monkeypatch.setattr(faq_retriever, "faqs", [])
    monkeypatch.setattr(faq_retriever, "_normed_matrix", np.zeros((0, 0), dtype=np.float32))
    fake_client = FakeEmbedClient([1.0])
    monkeypatch.setattr(faq_index, "_client", fake_client)

    results, timing = faq_retriever.retrieve_with_timing("anything")

    assert results == []
    assert timing == {"embed_seconds": 0.0, "search_seconds": 0.0}
    assert fake_client.calls == []


def test_retrieve_with_timing_ranks_exact_match_first(three_faqs, monkeypatch):
    monkeypatch.setattr(faq_index, "_client", FakeEmbedClient([0.0, 1.0, 0.0]))

    results, timing = faq_retriever.retrieve_with_timing("question about topic 1")

    assert [r["question"] for r in results] == ["Q1"]
    assert results[0]["score"] == pytest.approx(1.0)
    assert "embed_seconds" in timing and "search_seconds" in timing


def test_retrieve_with_timing_min_score_filters_low_matches(three_faqs, monkeypatch):
    # Halfway between faq0 and faq1: cosine similarity ~0.707 to each, well
    # above the 0.55 default threshold, so both should come back.
    vec = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    vec = vec / np.linalg.norm(vec)
    monkeypatch.setattr(faq_index, "_client", FakeEmbedClient(vec.tolist()))

    results, _ = faq_retriever.retrieve_with_timing("ambiguous question", min_score=0.55)

    assert {r["question"] for r in results} == {"Q0", "Q1"}


def test_retrieve_with_timing_respects_min_score_threshold(three_faqs, monkeypatch):
    vec = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    vec = vec / np.linalg.norm(vec)
    monkeypatch.setattr(faq_index, "_client", FakeEmbedClient(vec.tolist()))

    results, _ = faq_retriever.retrieve_with_timing("ambiguous question", min_score=0.9)

    assert results == []


def test_retrieve_with_timing_respects_top_k(monkeypatch):
    monkeypatch.setattr(faq_retriever, "faqs", make_faqs(5))
    monkeypatch.setattr(faq_retriever, "_normed_matrix", np.eye(5, dtype=np.float32))
    # Query matching faq index 2 most, 3 second-most, rest below threshold.
    vec = [0.0, 0.0, 0.9, 0.6, 0.0]
    monkeypatch.setattr(faq_index, "_client", FakeEmbedClient(vec))

    results, _ = faq_retriever.retrieve_with_timing("q", top_k=1, min_score=0.0)

    assert [r["question"] for r in results] == ["Q2"]


def test_retrieve_drops_timing_info(three_faqs, monkeypatch):
    monkeypatch.setattr(faq_index, "_client", FakeEmbedClient([0.0, 1.0, 0.0]))

    results = faq_retriever.retrieve("question about topic 1")

    assert [r["question"] for r in results] == ["Q1"]


def test_faq_retriever_invoke_empty_query_short_circuits():
    tool = faq_retriever.FaqRetriever()
    assert tool.invoke({"query": "  "}, {}) == "No search query was provided."


def test_faq_retriever_invoke_no_matches(monkeypatch):
    monkeypatch.setattr(faq_retriever, "retrieve", lambda query: [])
    tool = faq_retriever.FaqRetriever()

    result = tool.invoke({"query": "how do penguins fly"}, {})

    assert "how do penguins fly" in result
    assert "contact human customer support" in result


def test_faq_retriever_invoke_formats_matches_with_category(monkeypatch):
    monkeypatch.setattr(
        faq_retriever,
        "retrieve",
        lambda query: [{"question": "Q1", "answer": "A1", "category": "accounts", "score": 0.9}],
    )
    tool = faq_retriever.FaqRetriever()

    result = tool.invoke({"query": "test"}, {})

    assert result == "Category: accounts\nQ: Q1\nA: A1"


def test_faq_retriever_invoke_formats_matches_without_category(monkeypatch):
    monkeypatch.setattr(
        faq_retriever,
        "retrieve",
        lambda query: [{"question": "Q1", "answer": "A1", "category": "", "score": 0.9}],
    )
    tool = faq_retriever.FaqRetriever()

    result = tool.invoke({"query": "test"}, {})

    assert result == "Q: Q1\nA: A1"


def test_faq_retriever_invoke_joins_multiple_matches(monkeypatch):
    monkeypatch.setattr(
        faq_retriever,
        "retrieve",
        lambda query: [
            {"question": "Q1", "answer": "A1", "category": "", "score": 0.9},
            {"question": "Q2", "answer": "A2", "category": "", "score": 0.8},
        ],
    )
    tool = faq_retriever.FaqRetriever()

    result = tool.invoke({"query": "test"}, {})

    assert result == "Q: Q1\nA: A1\n\nQ: Q2\nA: A2"


def test_faq_retriever_async_invoke_matches_invoke(monkeypatch):
    monkeypatch.setattr(
        faq_retriever,
        "retrieve",
        lambda query: [{"question": "Q1", "answer": "A1", "category": "", "score": 0.9}],
    )
    tool = faq_retriever.FaqRetriever()

    result = asyncio.run(tool.async_invoke({"query": "test"}, {}))

    assert result == "Q: Q1\nA: A1"
