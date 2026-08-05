# FAQ Retrieval Evaluation Report

Generated: 2026-08-05T11:22:06+00:00
Questions evaluated: 2000
top_k: 10  |  min_score: 0.55

**Overall accuracy: 31.6%**

## TL;DR

- Out of 2000 questions, retrieval put the right FAQ category on top **32%** of the time.
- Best category: **insurance** (F1 0.56). Worst: **security** (F1 0.09) — questions in that category are the most likely to get mis-grounded or missed.
- Each search takes ~293ms, almost all of it (99%) waiting on the Ollama embedding call, not the search itself.

## Precision / Recall by category

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| accounts | 0.31 | 0.17 | 0.22 | 250 |
| cards | 0.38 | 0.22 | 0.27 | 250 |
| fundstransfer | 0.70 | 0.06 | 0.12 | 250 |
| insurance | 0.58 | 0.54 | 0.56 | 250 |
| investments | 0.40 | 0.12 | 0.19 | 250 |
| loans | 0.59 | 0.41 | 0.48 | 250 |
| none | 0.20 | 0.96 | 0.33 | 250 |
| security | 0.39 | 0.05 | 0.09 | 250 |
| **macro avg** | 0.44 | 0.32 | 0.28 | 2000 |
| **weighted avg** | 0.44 | 0.32 | 0.28 | 2000 |

## Latency breakdown

| Stage | avg | p50 | p95 |
|---|---|---|---|
| Ollama embedding call | 291.0ms | 285.7ms | 341.5ms |
| Local cosine search | 1.73ms | 0.57ms | 5.68ms |
| **Total retrieval** | **292.7ms** | — | — |

Embedding call is 99.4% of total latency; local search is 0.6%.
