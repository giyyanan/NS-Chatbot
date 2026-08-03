import csv
import time

import numpy as np
import ollama

CSV_PATH = "BankFAQs.csv"
CACHE_PATH = "faq_embeddings_embeddinggemma.npy"
MODEL = "embeddinggemma"

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    faqs = list(csv.DictReader(f))

print(f"Embedding {len(faqs)} rows with {MODEL}...")
start = time.time()
embeddings = []
for i, faq in enumerate(faqs):
    r = ollama.embed(model=MODEL, input=faq["Question"])
    embeddings.append(r["embeddings"][0])
    if (i + 1) % 100 == 0:
        elapsed = time.time() - start
        print(f"  {i + 1}/{len(faqs)} done ({elapsed:.0f}s elapsed)")

matrix = np.array(embeddings, dtype=np.float32)
np.save(CACHE_PATH, matrix)
print(f"Saved {matrix.shape} to {CACHE_PATH} in {time.time() - start:.0f}s total")
