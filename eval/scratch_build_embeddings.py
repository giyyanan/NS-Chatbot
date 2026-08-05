"""
(Re)builds the FAQ embedding cache from whatever files are in data/. Run
this after changing data/'s contents -- the backend assumes the cache
already exists and doesn't rebuild it automatically at startup (see
faq_index.ensure_embeddings()).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "coded_tools"))

import faq_index


def build() -> None:
    entries = faq_index.discover_entries()
    faq_index.build_embeddings(entries)
    print(f"Indexed {len(entries)} FAQ entries into {faq_index.CACHE_PATH}")


if __name__ == "__main__":
    build()
