# GoCCvA Computational Complexity Analysis

Goal model: `content\test\test0e_fail.txt`

## Theoretical Bound

For one alignment of length `n`, with cached structural information, the post-processing layer is:

`O(K * L + n * (K + N + E))`

where `K` is the number of selected targets, `L` is the number of leaf tasks, `N` is the number of intentional elements, and `E` is the number of refinement, contribution, and dependency links.

For a fixed goal model and fixed target set, `K`, `L`, `N`, and `E` are constants, so the runtime is linear in `n`.

## Model Parameters

| Parameter | Value |
|---|---:|
| `K_targets` | 2 |
| `N_intentional_elements` | 9 |
| `E_links_plus_dependencies` | 9 |
| `L_leaf_tasks` | 3 |
| `Q_qualities` | 2 |
| `G_goals` | 4 |
| `T_tasks` | 3 |

Targets:

- `(Admin) adequate declaration handling`
- `(Employee) Increase employee satisfaction`

## Target-Set Computation Timing

| Metric | Seconds |
|---|---:|
| `min_s` | 0.00005930 |
| `median_s` | 0.00006320 |
| `mean_s` | 0.00007736 |
| `max_s` | 0.00013340 |

## Alignment-Length Scaling

| n moves | median seconds | median ms / move |
|---:|---:|---:|
| 5 | 0.00068300 | 0.136600 |
| 10 | 0.00059940 | 0.059940 |
| 25 | 0.00102620 | 0.041048 |
| 50 | 0.00183080 | 0.036616 |
| 100 | 0.00313140 | 0.031314 |
| 200 | 0.00388330 | 0.019416 |

## Linear Fit

- Slope: `0.0000176125` seconds per move
- Intercept: `0.00071421` seconds
- R^2: `0.922589`

A high R^2 close to 1 supports the expected linear scaling in the alignment length for this fixed model and target set.
