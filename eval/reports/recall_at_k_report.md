# FAQ Retrieval — Recall@k Report

Generated: 2026-08-05T04:11:26+00:00
Questions evaluated: 2000  |  min_score: 0.55

## TL;DR

- Top-1 result is correct **32%** of the time. Widening the search to the top-10 results (instead of just the best match) gets the right category in the results **34%** of the time.
- Top-1 and top-k recall are close together, so when retrieval finds the right category at all, it usually ranks it first.

## Recall@k

(Does the correct category show up anywhere in the top-k results?)

| k | Correct / Total | Recall |
|---|---|---|
| 1 | 632/2000 | 31.6% |
| 3 | 670/2000 | 33.5% |
| 5 | 676/2000 | 33.8% |
| 10 | 681/2000 | 34.1% |
