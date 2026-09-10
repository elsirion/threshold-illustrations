# Implementation Diversity: Safety and Liveness

This figure has **two different panels and quantities**:

1. **Federation:** hypothetical failure probability versus discrete implementation count, at fixed high total hardening effort.
2. **Bitcoin:** continuous affected-user share versus implementation A's user share, **conditional on a disagreement that makes one implementation reject the dominant chain**.

The second panel replaces the earlier Bitcoin majority-hashpower reference. It is not a bug-probability curve and must not be compared numerically to the first panel as though both axes measured the same thing.

## Federation model

Use `f = 1,000,000`:

- `n = 3f + 1 = 3,000,001` nodes.
- Signing quorum `q = 2f + 1 = 2,000,001` keys, approximately two thirds.
- Liveness halt at `n - q + 1 = f + 1 = 1,000,001` stalled nodes, approximately one third.

For k implementations, distribute nodes as evenly as possible. Each codebase receives `floor(n/k)` or `ceil(n/k)` nodes. Exact integer thresholds are retained: rounding can matter for combinations near one third or two thirds. For example, at k=3 the largest group has 1,000,001 nodes and can halt the federation by itself; either smaller group alone cannot.

The fixed total hardening budget is **E=20**, divided equally, so each implementation gets E/k. This is the right-hand effort value of the earlier charts, not infinite effort.

- A shared failure directly causes the modeled outcome with probability **0.01%**.
- A separate shared-exposure scenario occurs with probability **9.9%**.
- Conditional on exposure, each codebase independently fails with probability `p = 0.10 + 0.40 * exp(-20/k)`.
- Overall probability is `0.0001 + 0.099 * Q`, where Q sums `p^|S| * (1-p)^(k-|S|)` over failed-codebase subsets S whose node weight reaches the relevant threshold.

Failures are independent only conditional on exposure. This model retains unconditional correlation from both shared failure and shared exposure. All probability parameters are illustrative, not empirical estimates.

### Federation results

| Implementations | Fund-safety failure | Liveness failure |
| --- | --- | --- |
| 1 | 1.000000% | 1.000000% |
| 2 | 0.109036% | 1.891324% |
| 3 | 0.199969% | 1.094998% |
| 4 | 0.049586% | 0.553976% |
| 5 | 0.016004% | 0.924729% |
| 6 | 0.024289% | 0.634005% |
| 7 | 0.014711% | 0.449394% |
| 8 | 0.011196% | 0.785333% |
| 9 | 0.013039% | 0.690366% |
| 10 | 0.011592% | 0.549635% |

## Bitcoin: continuous affected-user share

Let **x** be the fraction of users relying on implementation A, with the remaining **1−x** relying on implementation B. These are user shares, **not hashpower shares or raw node counts**. Each user is assigned to one implementation for this illustration.

Condition on a disagreement in which one implementation rejects a chain that continues to progress and is accepted by the other:

- If **A rejects the dominant chain**, affected users = **x**.
- If **B rejects the dominant chain**, affected users = **1−x**.

These are exact continuous functions. The figure draws straight lines; `bitcoin-user-impact.csv` samples them in one-percentage-point increments. At a **20/80 split**, rejection by A affects **20%** of users; rejection by B affects **80%**. No discontinuity or special rule occurs at a 50/50 user split. The endpoints are limiting cases where one implementation has no users.

“Affected” means **unable to follow that dominant chain's progress using the rejecting implementation**. It does not necessarily mean the users have no advancing chain at all: an incompatible fork may continue, and the situation may be resolved by a software change. Full nodes apply their own validation rules; incompatible rules can produce divergent chains. [Bitcoin Developer Guide: Consensus Rule Changes](https://developer.bitcoin.org/devguide/block_chain.html#consensus-rule-changes)

The chart does not assume that a majority of users decides which chain progresses. It also does not assert which implementation is correct. Mining support, validation rules and the particular disagreement determine the outcome. The two lines are **alternative scenarios**, not outcomes to add together.

### Why there is no probability parameter in the Bitcoin panel

Affected-user share is conditional impact. Turning it into expected harm would require the probability of each disagreement scenario, outage duration, recovery behavior and possibly user-specific stakes. Those quantities are not supplied and are not invented here. The federation's 0.01% common-failure floor and shared-exposure probabilities therefore apply **only to the federation panel**.

## Limits and verification

Federation liveness assumes buggy nodes stop participating or refuse to vote while remaining nodes agree and can communicate. Federation safety models direct signing-key compromise, not every consensus safety failure. Startup costs, interoperability regressions, unequal quality and recovery time are excluded from the federation probability model.

The original hardening-effort charts remain 7-of-10 examples. Their one-, two-, and four-implementation probabilities match the corresponding large-federation cases because the successful failure-subset patterns are unchanged; other counts need not match.

The generator checks federation subset enumeration against a sparse convolution and against the companion CSVs at those counts. Bitcoin checks cover endpoints, complements, the 20/80 example and invalid share inputs.

## Regenerate

```sh
python3 implementation_count.py
magick -background '#f8fafb' implementation-count.svg implementation-count.png
```

The generator writes the figure, `implementation-count.csv` (federation probabilities), and `bitcoin-user-impact.csv` (conditional affected-user shares) alongside itself.
