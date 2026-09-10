# Safety and Liveness vs. Implementation Count

This chart compares **one to ten implementations** at a fixed **20-unit total hardening budget**, using a very large federation and an additional Bitcoin-style majority-hashpower reference. Each codebase receives E/k effort. This is finite high effort, not the infinite-effort limit.

All plotted probabilities are hypothetical. The three lines model different outcomes; they are not interchangeable estimates of actual fund-loss risk.

## Federation and thresholds

Use `f = 1,000,000`, so:

- Federation size: `n = 3f + 1 = 3,000,001` nodes.
- Signing quorum: `q = 2f + 1 = 2,000,001` keys, approximately two thirds.
- Quorum halt: `n - q + 1 = f + 1 = 1,000,001` stalled nodes, approximately one third.

For k implementations, distribute nodes as evenly as possible: each codebase receives either `floor(n/k)` or `ceil(n/k)` nodes. A failed codebase affects its entire assigned group.

**Exact integer thresholds are retained.** Even with millions of nodes, rounding can matter when a group combination lies exactly around one third, one half or two thirds. For example, at k=3 the allocation is 1,000,001 + 1,000,000 + 1,000,000: the largest codebase alone can halt the federation, whereas either smaller one alone cannot. The chart enumerates weighted combinations, rather than rounding a fraction of k implementations to an integer.

This is one explicit near-equal allocation, not a claim that every possible large-federation allocation yields identical probabilities.

## Bitcoin reference: majority hashpower, not node count

For the orange line, reinterpret the same 3,000,001 abstract units as **hashpower units**, split nearly equally across implementations. Its threshold is strictly greater than 50%: `floor(n/2) + 1 = 1,500,001` units. A compromised mining implementation is assumed to give an adversary control of all hashpower assigned to it. That is a toy-model assumption, not a description of actual Bitcoin implementation shares or every software vulnerability.

Bitcoin's developer guide explains majority-hashpower attacks on transaction history and also notes that attacks can succeed with less than 50%. The graph therefore measures a **majority-control event**, not the full probability of a successful Bitcoin attack. [Bitcoin Developer Guide: Block Chain](https://developer.bitcoin.org/devguide/block_chain.html)

Majority hashpower does not grant private keys or let miners make arbitrary invalid transactions acceptable to correct validating nodes. The Bitcoin guide describes chain selection among valid blocks. This is not a Bitcoin key-theft curve and is not directly equivalent to unauthorized threshold signing. [Bitcoin Developer Guide: Block Chain](https://developer.bitcoin.org/devguide/block_chain.html)

## Shared probability assumptions

As in the earlier charts:

- Shared failure directly causes the relevant modeled outcome with probability **0.01%**.
- A separate shared-exposure scenario occurs with probability **9.9%**.
- Conditional on that scenario, codebases independently fail with probability `p = 0.10 + 0.40 * exp(-20/k)`.
- Overall probability is `0.0001 + 0.099 * Q`, where Q is the conditional probability of reaching the relevant weight threshold.

For each subset S of failed implementations, sum `p^|S| * (1-p)^(k-|S|)` if its total assigned weight reaches the threshold. Shared failure and shared exposure create unconditional correlation; independence only holds conditional on exposure.

Identical numerical parameters are used to isolate threshold effects, not to claim equal real-world bug rates across federation signing, consensus liveness and Bitcoin mining. The three probabilities should not be added together.

## Results at total effort E=20

| Implementations | Federation safety failure | Federation liveness failure | Bitcoin majority control |
| --- | --- | --- | --- |
| 1 | 1.000000% | 1.000000% | 1.000000% |
| 2 | 0.109036% | 1.891324% | 1.000180% |
| 3 | 0.199969% | 1.094998% | 0.289928% |
| 4 | 0.049586% | 0.553976% | 0.301781% |
| 5 | 0.016004% | 0.924729% | 0.113534% |
| 6 | 0.024289% | 0.634005% | 0.133554% |
| 7 | 0.014711% | 0.449394% | 0.068166% |
| 8 | 0.011196% | 0.785333% | 0.087150% |
| 9 | 0.013039% | 0.690366% | 0.055535% |
| 10 | 0.011592% | 0.549635% | 0.072853% |

## Reading the plot and limitations

The vertical axis is logarithmic; lower is better. Lines connect discrete implementation counts, not fractional codebase counts. Curves are not necessarily monotonic: allocations change which subsets reach thresholds, and more codebases mean less hardening per codebase.

Liveness assumes affected nodes stop participating or refuse to vote, while remaining nodes agree and can communicate. It does not model every consensus bug or arbitrary Byzantine behavior. The federation safety line models direct compromise of signing keys, not every way consensus safety can fail. Startup costs, interoperability regressions, unequal codebase quality, outage duration, mining economics, confirmation depth and actual Bitcoin deployment shares are excluded.

The original hardening-effort charts remain 7-of-10 examples. Their one-, two-, and four-implementation probabilities happen to match the corresponding federation points here because those allocations have the same successful failure-subset patterns. That equivalence does not hold for all implementation counts.

## Regenerate

```sh
python3 implementation_count.py
magick -background '#f8fafb' implementation-count.svg implementation-count.png
```

The generator checks exhaustive subset enumeration against a sparse convolution, verifies exact threshold identities and the symmetry of majority outcomes, checks bounds and balanced allocations, and confirms the unchanged one-, two-, and four-implementation federation cases against the companion CSVs. Its outputs are written alongside the script. The CSV contains exact weight allocations as well as all three outcome probabilities.
