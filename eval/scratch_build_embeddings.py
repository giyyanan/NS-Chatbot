"""
Manually (re)builds the FAQ embedding cache from whatever files are in
data/. The backend also does this automatically at startup when data/ has
changed, so this script is only needed to pre-warm the cache ahead of time.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "coded_tools"))

import faq_index


def build() -> None:
    entries, _ = faq_index.ensure_embeddings()
    print(f"Indexed {len(entries)} FAQ entries into {faq_index.CACHE_PATH}")


if __name__ == "__main__":
    build()
