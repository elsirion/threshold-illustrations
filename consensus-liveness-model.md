# Consensus Liveness Illustrative Model

A hypothetical model of **bug-induced loss of quorum**, not a measurement of Fedimint reliability or a model of every consensus bug. It uses the previous security chart's illustrative parameters, but changes the failure condition from unauthorized signing to inability to assemble a quorum. Reusing parameters is for comparison, not a claim that real safety and liveness bug rates are equal.

## 7-of-10 federation

Seven compatible, responsive nodes are required to make progress. A triggered implementation bug makes every node running that codebase stop participating or refuse to vote. Remaining nodes are assumed correct, mutually compatible and able to communicate. **Four unavailable nodes therefore cause a halt.**

| Implementations | Node allocation | Codebase stalls that halt the federation |
| --- | --- | --- |
| 1 | A: 10 | A |
| 2 | A: 5, B: 5 | Either A or B |
| 4 | A: 3, B: 3, C: 2, D: 2 | Any two codebases |

With four implementations, no single codebase has four nodes, but every pair has at least four. Thus one implementation can stall without losing quorum. This would not necessarily hold for arbitrary Byzantine behavior or incompatible protocol interpretations.

## Probabilities

Within a fixed hypothetical observation window, assume three mutually exclusive scenarios:

- A shared failure halts the federation: **0.01%**.
- An implementation-specific bug-trigger scenario occurs: **9.9%**.
- Neither occurs: **90.09%**.

Conditional on the bug-trigger scenario, each implementation independently stalls with probability:

`p(e) = 0.10 + 0.40 * exp(-e)`.

Total hardening effort E is divided equally among k implementations, giving `e = E/k`. The decreasing, convex function models diminishing returns. Its probabilities are conditional, not the overall failure probabilities plotted.

Conditional probability Q of losing at least four nodes:

- 1 implementation: `Q = p(E)`.
- 2 implementations: `Q = 2*p(E/2) - p(E/2)^2`.
- 4 implementations: `Q = 6*p(E/4)^2 - 8*p(E/4)^3 + 3*p(E/4)^4`.

The four-implementation expression is the probability that at least two of four independent codebases stall.

Overall plotted risk: `R(E) = 0.0001 + 0.099 * Q(E)`.

| Implementations | Risk at E=0 | Risk at E=20 | Asymptotic floor |
| --- | --- | --- | --- |
| 1 | 4.960% | 1.000% | 1.000% |
| 2 | 7.435% | 1.891% | 1.891% |
| 4 | 6.81625% | 0.554% | 0.52777% |

Shared failure and shared exposure both create unconditional correlation. The 9.9% exposure parameter preserves a 1% single-codebase floor: `0.0001 + 0.099 * 0.1 = 0.01`.

## Interpretation

Two implementations improve signing safety in the companion chart, but worsen this liveness model: either five-node codebase can independently prevent progress. Four implementations allow a single codebase to stall without stopping the federation. At small hardening budgets, however, splitting effort among four codebases can still be worse than focusing on one.

## Limits

- This is the probability of a **quorum halt**, not the probability that any consensus bug exists.
- Consensus bugs can cause inconsistent state transitions, divergent validation, equivocation or broken safety without matching this fail-stop model. These effects require a protocol-specific model.
- Interoperability bugs introduced by diversity are excluded, as are build costs, unequal codebase quality, hardware/network failures and recovery behavior.
- The graph measures occurrence over a fixed window, not outage duration or percentage uptime.
- Correct remaining nodes are assumed mutually compatible, with communication and scheduling sufficient for progress; possessing seven live nodes alone does not guarantee liveness in an arbitrary consensus protocol or network.
- All numerical assumptions are illustrative, not evidence-based estimates.

## Regenerate

```sh
python consensus_liveness.py
magick -background '#f8fafb' consensus-liveness.svg consensus-liveness.png
```

The script verifies exhaustive enumeration against closed-form probabilities and checks monotonicity and threshold invariants. Outputs are written alongside the script. The existing security graph is preserved.
