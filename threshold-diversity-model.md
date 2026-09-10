# Threshold Security Illustrative Model

Hypothetical illustration, not a security estimate for Fedimint or any deployed federation. Parameters and effort units illustrate the mechanism; they are not fitted to evidence.

## 7-of-10 federation

Seven signer keys are needed for unauthorized signing. A compromised implementation exposes all keys held by signers running that codebase.

| Implementations | Signer allocation | Required codebase compromises |
| --- | --- | --- |
| 1 | A: 10 | A |
| 2 | A: 5, B: 5 | A and B |
| 4 | A: 3, B: 3, C: 2, D: 2 | Any three codebases |

## Model

Within a fixed hypothetical attack window, three mutually exclusive scenarios are assumed:

- Shared failure compromises the threshold: probability **0.01%**.
- Implementation-specific attack opportunity: probability **9.9%**.
- Neither: probability **90.09%**.

Conditional on an implementation-specific attack, each codebase is independently compromised with probability:

`p(e) = 0.10 + 0.40 * exp(-e)`.

Total hardening effort E is split equally across k codebases: `e = E/k`. This decreasing, convex function models diminishing returns with residual risk. These conditional probabilities are not the plotted overall probabilities.

Conditional threshold compromise probability Q:

- 1 implementation: `Q = p(E)`.
- 2 implementations: `Q = p(E/2)^2`.
- 4 implementations: `Q = 4*p(E/4)^3 - 3*p(E/4)^4`.

Plotted risk: `R(E) = 0.0001 + 0.099 * Q(E)`.

| Implementations | Risk at E=0 | Asymptotic floor |
| --- | --- | --- |
| 1 | 4.960% | **1.000%** |
| 2 | 2.485% | 0.109% |
| 4 | 3.10375% | 0.04663% |

The plotted endpoint at E=20 is approximately 1.00%, 0.11%, and 0.05%, respectively. The chart extends above 1% because 1% is now the single-implementation floor, not its initial risk.

The attack-opportunity probability is calibrated as `(0.01 - 0.0001) / 0.10 = 0.099` to preserve the requested 1% overall single-implementation floor. Both the shared-failure event and shared attack exposure create unconditional correlation; this is not a model of fully independent 1% codebase failures.

## Why four can improve on two

With the 5+5 allocation, both codebases must fail. With 3+3+2+2, no two codebases control seven keys, while every three-codebase combination does. The latter therefore requires three independent compromises rather than two.

Splitting the same budget four ways reduces the hardening of each codebase, so four do not win at every effort level. In this illustration, two are safer initially, while four are safer at sufficiently high effort. Shared risk limits the benefit of both.

## Limits

- Independence is conditional on the implementation-specific attack. The shared-failure scenario supplies a common-mode floor.
- Implementations have equal initial quality and hardening efficiency. Startup and additional maintenance costs are excluded.
- Shared specifications, dependencies, operations, or further coupling could increase correlated risk.
- This models signing safety, not denial of service or availability.
- Diminishing returns alone do not prove diversity always wins.

## Regenerate

```sh
python threshold_diversity.py
magick -background '#f8fafb' threshold-diversity.svg threshold-diversity.png
```

The script checks exhaustive enumeration against closed-form probabilities and writes SVG and CSV alongside itself.
