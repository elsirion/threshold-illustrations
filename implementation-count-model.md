# Safety and Liveness vs. Implementation Count

This chart takes a **fixed-total-effort slice at E=20** of the existing illustrative models, extending balanced deployments from one to ten implementations in a 7-of-10 federation. E=20 is the right-hand endpoint of the existing charts, not the infinite-effort limit. Each codebase gets E/k effort, so increasing implementation count reduces effort per codebase.

The plot shows **failure probabilities**, not success probabilities. Fund-safety failure means unauthorized signing; liveness failure means a bug-induced quorum halt. A logarithmic vertical axis makes small probabilities visible. Connecting lines guide the eye between discrete implementation counts; fractional codebase counts are not modeled.

## Allocation and failure conditions

Ten nodes are distributed as evenly as possible: for k implementations, each receives either `floor(10/k)` or `ceil(10/k)` nodes.

- **Fund safety fails** when compromised codebases collectively control at least **seven keys**.
- **Liveness fails** when stalled codebases collectively disable at least **four nodes**, leaving fewer than seven compatible, responsive nodes.

Safety and liveness are evaluated as separate scenarios with the same illustrative parameters, not as joint real-world events. The probabilities are not meant to be added together.

## Probability model

As in the existing charts:

- Shared failure directly causes the relevant system failure with probability **0.01%**.
- A separate shared-exposure scenario occurs with probability **9.9%**.
- Conditional on that scenario, each codebase independently fails with probability `p = 0.10 + 0.40 * exp(-20/k)`.
- Overall failure probability is `0.0001 + 0.099 * Q`, where Q is the conditional probability of reaching the relevant failed-node threshold.

For allocation `a[1], ..., a[k]`, the model enumerates every subset S of failed codebases and sums

`p^|S| * (1-p)^(k-|S|)`

over subsets whose total node count reaches seven (safety) or four (liveness). Shared failure and shared exposure create **unconditional correlation**; codebase failures are independent only conditional on exposure.

## Results at total effort E=20

| Implementations | Node allocation | Fund-safety failure | Liveness failure |
| --- | --- | --- | --- |
| 1 | 10 | 1.000000% | 1.000000% |
| 2 | 5+5 | 0.109036% | 1.891324% |
| 3 | 4+3+3 | 0.199969% | 1.094998% |
| 4 | 3+3+2+2 | 0.049586% | 0.553976% |
| 5 | 2+2+2+2+2 | 0.016004% | 0.924729% |
| 6 | 2+2+2+2+1+1 | 0.022965% | 0.713566% |
| 7 | 2+2+2+1+1+1+1 | 0.020178% | 0.638870% |
| 8 | 2+2+1+1+1+1+1+1 | 0.016495% | 0.632048% |
| 9 | 2+1+1+1+1+1+1+1+1 | 0.013363% | 0.621218% |
| 10 | 1+1+1+1+1+1+1+1+1+1 | 0.011592% | 0.549635% |

## Interpretation and limits

The curves need not decrease monotonically. Integer node allocations change which failure combinations cross the threshold, while the fixed budget gives each codebase less hardening as k grows. For example, going from four to five implementations changes the allocation from 3+3+2+2 to 2+2+2+2+2. A liveness halt still requires two stalled codebases, but there are more possible pairs and less hardening per codebase.

All numbers are hypothetical. Equal starting quality and hardening efficiency are assumed. Startup costs, interoperability regressions, recovery time and non-codebase failures are excluded. Liveness assumes affected nodes stop or refuse to vote, while remaining nodes agree and can communicate; it does not model every consensus bug. See the existing safety and liveness model notes for further limitations.

## Regenerate

```sh
python3 implementation_count.py
magick -background '#f8fafb' implementation-count.svg implementation-count.png
```

The generator verifies subset enumeration against an independent failed-node-count convolution, checks balanced allocations and probability bounds, and cross-checks the one-, two-, and four-codebase values against the existing CSVs at E=20. Run it with the companion CSVs present. Its outputs are written alongside the script.
