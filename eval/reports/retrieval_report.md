# FAQ Retrieval Evaluation Report

Generated: 2026-08-05T03:45:20+00:00
Questions evaluated: 2000
top_k: 10  |  min_score: 0.55

**Overall accuracy: 47.8%**

## TL;DR

- Out of 2000 questions, retrieval put the right FAQ category on top **48%** of the time.
- Best category: **loans** (F1 0.67). Worst: **accounts** (F1 0.23) — questions in that category are the most likely to get mis-grounded or missed.
- Each search takes ~504ms, almost all of it (99%) waiting on the Ollama embedding call, not the search itself.

## Precision / Recall by category

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| accounts | 0.19 | 0.27 | 0.23 | 250 |
| cards | 0.39 | 0.58 | 0.47 | 250 |
| fundstransfer | 0.72 | 0.42 | 0.53 | 250 |
| insurance | 0.56 | 0.80 | 0.66 | 250 |
| investments | 0.47 | 0.22 | 0.30 | 250 |
| loans | 0.65 | 0.69 | 0.67 | 250 |
| none | 0.52 | 0.60 | 0.55 | 250 |
| security | 0.57 | 0.24 | 0.34 | 250 |
| **macro avg** | 0.51 | 0.48 | 0.47 | 2000 |
| **weighted avg** | 0.51 | 0.48 | 0.47 | 2000 |

## Latency breakdown

| Stage | avg | p50 | p95 |
|---|---|---|---|
| Ollama embedding call | 499.8ms | 450.7ms | 1000.0ms |
| Local cosine search | 4.24ms | 4.09ms | 8.81ms |
| **Total retrieval** | **504.0ms** | — | — |

Embedding call is 99.2% of total latency; local search is 0.8%.
