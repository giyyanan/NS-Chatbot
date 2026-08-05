"""
Unit tests for backend/coded_tools/faq_index.py: FAQ file discovery/parsing,
cache-manifest hashing, and embedding-cache invalidation. The embedding call
itself is mocked out everywhere here -- these tests never touch Ollama.
"""

import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "coded_tools"))

import faq_index  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Points faq_index at an isolated, empty data/ dir for the duration of a test."""
    monkeypatch.setattr(faq_index, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(faq_index, "CACHE_PATH", os.path.join(str(tmp_path), f"{faq_index.CACHE_PREFIX}.npy"))
    monkeypatch.setattr(faq_index, "META_PATH", os.path.join(str(tmp_path), f"{faq_index.CACHE_PREFIX}.meta.json"))
    return tmp_path


def write_csv(path, rows, fieldnames):
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# -- _match_key -----------------------------------------------------------

def test_match_key_case_insensitive():
    assert faq_index._match_key(["Question", "Answer"], faq_index.QUESTION_KEYS) == "Question"


def test_match_key_no_match_returns_none():
    assert faq_index._match_key(["foo", "bar"], faq_index.QUESTION_KEYS) is None


# -- _rows_from_csv / _rows_from_json --------------------------------------

def test_rows_from_csv(tmp_path):
    path = tmp_path / "faqs.csv"
    write_csv(path, [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    rows = faq_index._rows_from_csv(str(path))
    assert rows == [{"question": "Q1", "answer": "A1"}]


def test_rows_from_json_list(tmp_path):
    path = tmp_path / "faqs.json"
    path.write_text(json.dumps([{"question": "Q1", "answer": "A1"}]), encoding="utf-8")
    assert faq_index._rows_from_json(str(path)) == [{"question": "Q1", "answer": "A1"}]


def test_rows_from_json_wrapped_in_list_key(tmp_path):
    path = tmp_path / "faqs.json"
    path.write_text(json.dumps({"faqs": [{"question": "Q1", "answer": "A1"}]}), encoding="utf-8")
    assert faq_index._rows_from_json(str(path)) == [{"question": "Q1", "answer": "A1"}]


def test_rows_from_json_no_recognizable_list_key(tmp_path):
    path = tmp_path / "faqs.json"
    path.write_text(json.dumps({"unrelated": "value"}), encoding="utf-8")
    assert faq_index._rows_from_json(str(path)) == []


# -- _extract_entries -------------------------------------------------------

def test_extract_entries_maps_and_strips_fields():
    rows = [{"Q": " what is this? ", "A": " an FAQ. ", "Category": " general "}]
    entries = faq_index._extract_entries(rows, "source.csv")
    assert entries == [{"question": "what is this?", "answer": "an FAQ.", "category": "general"}]


def test_extract_entries_no_category_column():
    rows = [{"question": "Q1", "answer": "A1"}]
    entries = faq_index._extract_entries(rows, "source.csv")
    assert entries == [{"question": "Q1", "answer": "A1", "category": ""}]


def test_extract_entries_empty_rows_returns_empty():
    assert faq_index._extract_entries([], "source.csv") == []


def test_extract_entries_missing_question_or_answer_raises():
    with pytest.raises(ValueError):
        faq_index._extract_entries([{"foo": "bar"}], "source.csv")


def test_extract_entries_non_dict_rows_raises():
    with pytest.raises(ValueError):
        faq_index._extract_entries(["not a dict"], "source.csv")


# -- discover_entries ---------------------------------------------------

def test_discover_entries_combines_csv_and_json(data_dir):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    (data_dir / "b.json").write_text(
        json.dumps([{"question": "Q2", "answer": "A2"}]), encoding="utf-8"
    )

    entries = faq_index.discover_entries()
    assert {"question": "Q1", "answer": "A1", "category": ""} in entries
    assert {"question": "Q2", "answer": "A2", "category": ""} in entries
    assert len(entries) == 2


def test_discover_entries_ignores_cache_files(data_dir):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    (data_dir / f"{faq_index.CACHE_PREFIX}.meta.json").write_text("{}", encoding="utf-8")

    entries = faq_index.discover_entries()
    assert len(entries) == 1


def test_discover_entries_empty_dir(data_dir):
    assert faq_index.discover_entries() == []


# -- _data_manifest_hash -------------------------------------------------

def test_manifest_hash_stable_for_unchanged_files(data_dir):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    assert faq_index._data_manifest_hash() == faq_index._data_manifest_hash()


def test_manifest_hash_changes_when_file_content_changes(data_dir):
    path = data_dir / "a.csv"
    write_csv(path, [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    before = faq_index._data_manifest_hash()

    write_csv(path, [{"question": "Q1", "answer": "A1 updated"}], ["question", "answer"])
    after = faq_index._data_manifest_hash()

    assert before != after


def test_manifest_hash_ignores_cache_files(data_dir):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    before = faq_index._data_manifest_hash()

    (data_dir / f"{faq_index.CACHE_PREFIX}.npy").write_bytes(b"fake cache bytes")
    after = faq_index._data_manifest_hash()

    assert before == after


# -- ensure_embeddings ----------------------------------------------------

def fake_embed_entries(entries):
    """Deterministic stand-in for faq_index._embed_entries: one unit vector per entry."""
    vectors = np.eye(len(entries), dtype=np.float32)
    return vectors


def test_ensure_embeddings_no_entries(data_dir):
    entries, matrix = faq_index.ensure_embeddings()
    assert entries == []
    assert matrix.shape == (0, 0)


def test_ensure_embeddings_builds_and_caches(data_dir, monkeypatch):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    monkeypatch.setattr(faq_index, "_embed_entries", fake_embed_entries)

    entries, matrix = faq_index.ensure_embeddings()

    assert len(entries) == 1
    assert matrix.shape == (1, 1)
    assert os.path.exists(faq_index.CACHE_PATH)
    assert os.path.exists(faq_index.META_PATH)


def test_ensure_embeddings_reuses_valid_cache(data_dir, monkeypatch):
    write_csv(data_dir / "a.csv", [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    monkeypatch.setattr(faq_index, "_embed_entries", fake_embed_entries)
    faq_index.ensure_embeddings()

    def fail_if_called(entries):
        raise AssertionError("_embed_entries should not be called when the cache is still valid")

    monkeypatch.setattr(faq_index, "_embed_entries", fail_if_called)
    entries, matrix = faq_index.ensure_embeddings()

    assert len(entries) == 1
    assert matrix.shape == (1, 1)


def test_ensure_embeddings_rebuilds_when_data_changes(data_dir, monkeypatch):
    path = data_dir / "a.csv"
    write_csv(path, [{"question": "Q1", "answer": "A1"}], ["question", "answer"])
    monkeypatch.setattr(faq_index, "_embed_entries", fake_embed_entries)
    faq_index.ensure_embeddings()

    write_csv(path, [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}], ["question", "answer"])

    calls = []

    def counting_embed(entries):
        calls.append(entries)
        return fake_embed_entries(entries)

    monkeypatch.setattr(faq_index, "_embed_entries", counting_embed)
    entries, matrix = faq_index.ensure_embeddings()

    assert len(calls) == 1
    assert len(entries) == 2
    assert matrix.shape == (2, 2)
