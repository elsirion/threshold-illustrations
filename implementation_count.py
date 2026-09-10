"""Plot fixed-budget risk across codebase counts; see implementation-count-model.md."""
from dataclasses import dataclass
from pathlib import Path
from itertools import product
from math import exp, isclose, log10, prod
from html import escape
import csv

OUT = Path(__file__).resolve().parent
FAULT_BUDGET = 1_000_000
NODES = 3 * FAULT_BUDGET + 1
QUORUM = 2 * FAULT_BUDGET + 1
MAX_IMPLEMENTATIONS = 10
BLOCKING_FAILURES = NODES - QUORUM + 1
TOTAL_EFFORT = 20
INITIAL_CONDITIONAL_RISK = 0.5
RESIDUAL_CONDITIONAL_RISK = 0.1
SHARED_FAILURE_PROBABILITY = 0.0001
SINGLE_IMPLEMENTATION_FLOOR = 0.01
EXPOSURE_PROBABILITY = (SINGLE_IMPLEMENTATION_FLOOR - SHARED_FAILURE_PROBABILITY) / RESIDUAL_CONDITIONAL_RISK
SAFETY_COLOR = '#b84e34'
LIVENESS_COLOR = '#326bb2'
BITCOIN_COLOR = '#a96b08'
BITCOIN_ALTERNATIVE_COLOR = '#7953a6'
USER_SHARE_SAMPLES = 100


@dataclass(frozen=True)
class Result:
    allocation: tuple[int, ...]
    conditional_codebase_risk: float
    safety_failure: float
    liveness_failure: float


def balanced_allocation(count):
    if not 1 <= count <= MAX_IMPLEMENTATIONS:
        raise ValueError(f'Implementation count must be between 1 and {MAX_IMPLEMENTATIONS}')
    size, extra = divmod(NODES, count)
    return (size + 1,) * extra + (size,) * (count - extra)


def failure_probability(allocation, probability, threshold):
    """Exact conditional probability that failed codebases control enough nodes."""
    return sum(
        prod(probability if failed else 1 - probability for failed in state)
        for state in product((False, True), repeat=len(allocation))
        if sum(size for size, failed in zip(allocation, state) if failed) >= threshold
    )


def calculate(count):
    allocation = balanced_allocation(count)
    probability = RESIDUAL_CONDITIONAL_RISK + (INITIAL_CONDITIONAL_RISK - RESIDUAL_CONDITIONAL_RISK) * exp(-TOTAL_EFFORT / count)
    def overall(threshold):
        return SHARED_FAILURE_PROBABILITY + EXPOSURE_PROBABILITY * failure_probability(allocation, probability, threshold)
    return Result(allocation, probability, overall(QUORUM), overall(BLOCKING_FAILURES))


def check_model(results):
    assert NODES == 3 * FAULT_BUDGET + 1 and QUORUM == 2 * FAULT_BUDGET + 1
    assert BLOCKING_FAILURES == FAULT_BUDGET + 1
    for row in results:
        allocation = row.allocation
        assert sum(allocation) == NODES, 'Node count must stay fixed'
        assert max(allocation) - min(allocation) <= 1, 'Allocation must be balanced'
        assert SHARED_FAILURE_PROBABILITY <= row.safety_failure <= row.liveness_failure <= 1
        # Independently convolve each group's node count to check enumeration.
        for probability in (0, row.conditional_codebase_risk, 0.5, 1):
            distribution = {0: 1.0}
            for size in allocation:
                updated = {}
                for failed_nodes, mass in distribution.items():
                    updated[failed_nodes] = updated.get(failed_nodes, 0.0) + mass * (1 - probability)
                    if failed_nodes + size <= NODES:
                        updated[failed_nodes + size] = updated.get(failed_nodes + size, 0.0) + mass * probability
                distribution = updated
            assert isclose(sum(distribution.values()), 1, abs_tol=1e-12), 'Probability mass must be preserved'
            for threshold in (QUORUM, BLOCKING_FAILURES):
                assert isclose(failure_probability(allocation, probability, threshold), sum(mass for failed_nodes, mass in distribution.items() if failed_nodes >= threshold), abs_tol=1e-12)
    assert isclose(results[0].safety_failure, results[0].liveness_failure, abs_tol=1e-12)
    # Cross-check against the existing charts without importing their generators,
    # whose module-level execution would regenerate files as a side effect.
    for filename, field in (('threshold-diversity.csv', 'safety_failure'), ('consensus-liveness.csv', 'liveness_failure')):
        with (OUT / filename).open(newline='') as handle:
            endpoint = next(row for row in csv.DictReader(handle) if float(row['total_hardening_effort']) == TOTAL_EFFORT)
        for count, column in ((1, 'one_implementation'), (2, 'two_implementations'), (4, 'four_implementations')):
            assert isclose(getattr(results[count - 1], field), float(endpoint[column]), abs_tol=1e-12), 'Existing chart endpoint must match'


def write_csv(results):
    with (OUT / 'implementation-count.csv').open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(('implementations', 'node_allocation', 'total_effort', 'effort_per_implementation', 'conditional_codebase_failure_probability', 'fund_safety_failure_probability', 'liveness_failure_probability'))
        for row in results:
            count = len(row.allocation)
            writer.writerow((count, '+'.join(map(str, row.allocation)), TOTAL_EFFORT, TOTAL_EFFORT / count, row.conditional_codebase_risk, row.safety_failure, row.liveness_failure))


def affected_user_shares(share_a):
    """Conditional impact: A rejects the dominant chain, or B rejects it."""
    if not 0 <= share_a <= 1:
        raise ValueError('Implementation A user share must be between zero and one')
    return share_a, 1 - share_a


def check_user_impact():
    assert affected_user_shares(0) == (0, 1)
    assert affected_user_shares(1) == (1, 0)
    assert affected_user_shares(0.5) == (0.5, 0.5)
    assert affected_user_shares(0.2) == (0.2, 0.8), '20/80 split must expose the rejecting group only'
    for index in range(USER_SHARE_SAMPLES + 1):
        share = index / USER_SHARE_SAMPLES
        affected_a, affected_b = affected_user_shares(share)
        assert isclose(affected_a + affected_b, 1, abs_tol=1e-12)
        assert isclose(affected_a, affected_user_shares(1 - share)[1], abs_tol=1e-12)
    for invalid in (-0.1, 1.1, float('nan')):
        try:
            affected_user_shares(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid user shares must be rejected')


def write_user_impact_csv():
    with (OUT / 'bitcoin-user-impact.csv').open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(('implementation_a_user_share', 'implementation_b_user_share', 'affected_share_if_a_rejects_dominant_chain', 'affected_share_if_b_rejects_dominant_chain'))
        for index in range(USER_SHARE_SAMPLES + 1):
            share = index / USER_SHARE_SAMPLES
            affected_a, affected_b = affected_user_shares(share)
            writer.writerow((share, 1 - share, affected_a, affected_b))


def write_svg(results):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="1020" viewBox="0 0 1700 1020">', '<rect width="1700" height="1020" fill="#f8fafb"/>', '<g font-family="DejaVu Sans, sans-serif">']
    def text(x, y, value, size=22, fill='#1b2935', weight='normal', anchor='start'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')
    def line(x1, y1, x2, y2, color='#dce3e8', width=1, dash=''):
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
    def rect(x, y, width, height, fill, radius=0):
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"/>')
    def dot(x, y, color, radius=6):
        svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" stroke="#f8fafb" stroke-width="2"/>')

    text(72, 93, 'Implementation Diversity: Safety & Liveness', 47, weight='bold')
    text(72, 140, 'Large federation: quorum ≈ ⅔ · Bitcoin: user impact when implementations disagree.', 23, '#576875')
    text(130, 211, 'Federation failure probability · log scale', 24, weight='bold')
    line(130, 250, 165, 250, SAFETY_COLOR, 4)
    text(180, 257, 'Federation: fund safety', 20, SAFETY_COLOR)
    line(130, 285, 165, 285, LIVENESS_COLOR, 4)
    text(180, 292, 'Federation: liveness', 20, LIVENESS_COLOR)
    text(640, 257, 'Fixed total effort: 20 units', 20, '#576875')
    text(640, 292, 'Near-equal node shares', 20, '#576875')

    x0, x1, y0, y1 = 130, 1020, 738, 325
    lower, upper = SHARED_FAILURE_PROBABILITY, 0.02
    px = lambda count: x0 + (x1 - x0) * (count - 1) / (MAX_IMPLEMENTATIONS - 1)
    py = lambda probability: y0 - (y0 - y1) * (log10(probability) - log10(lower)) / (log10(upper) - log10(lower))
    for percent in (0.01, 0.03, 0.1, 0.3, 1, 2):
        y = py(percent / 100)
        line(x0, y, x1, y)
        text(x0 - 18, y + 7, f'{percent:g}%', 20, '#576875', anchor='end')
    line(x0, y0, x1, y0, '#8796a0', 1.5, '5 5')
    for count in range(1, MAX_IMPLEMENTATIONS + 1):
        x = px(count)
        line(x, y0, x, y0 + 7, '#9aaab5')
        text(x, y0 + 35, str(count), 20, '#576875', anchor='middle')
    text((x0 + x1) / 2, 813, 'Number of implementations', 23, anchor='middle')

    for field, color in (('safety_failure', SAFETY_COLOR), ('liveness_failure', LIVENESS_COLOR)):
        points = ' '.join(f'{px(len(row.allocation)):.2f},{py(getattr(row, field)):.2f}' for row in results)
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>')
        for row in results:
            dot(px(len(row.allocation)), py(getattr(row, field)), color)
        risk = getattr(results[-1], field)
        line(x1, py(risk), x1 + 16, py(risk), color, 1.5)
        text(x1 + 23, py(risk) + 7, f'{risk * 100:.3f}%', 21, color, 'bold')
    # Both federation metrics coincide at one codebase.
    dot(px(1), py(results[0].safety_failure), SAFETY_COLOR, 8)
    dot(px(1), py(results[0].liveness_failure), LIVENESS_COLOR, 4)

    rect(1174, 192, 454, 636, '#edf2f5', 18)
    text(1204, 235, 'Bitcoin: affected users', 26, weight='bold')
    text(1204, 267, 'Conditional impact—not bug probability', 18, '#576875')
    line(1204, 302, 1236, 302, BITCOIN_COLOR, 4)
    text(1248, 309, 'A rejects the dominant chain', 18, BITCOIN_COLOR)
    line(1204, 332, 1236, 332, BITCOIN_ALTERNATIVE_COLOR, 4, '6 4')
    text(1248, 339, 'B rejects the dominant chain', 18, BITCOIN_ALTERNATIVE_COLOR)
    text(1204, 382, 'Users unable to follow that chain (%)', 18, '#576875')
    bx0, bx1, by0, by1 = 1250, 1584, 625, 416
    bx = lambda share: bx0 + (bx1 - bx0) * share
    by = lambda share: by0 - (by0 - by1) * share
    for share in (0, 0.2, 0.5, 0.8, 1):
        line(bx0, by(share), bx1, by(share), '#d5dfe5')
        text(bx0 - 14, by(share) + 6, f'{100 * share:g}', 17, '#576875', anchor='end')
        line(bx(share), by0, bx(share), by0 + 6, '#8796a0')
        text(bx(share), by0 + 29, f'{100 * share:g}', 17, '#576875', anchor='middle')
    # Straight segments represent the exact continuous functions y=x and y=1-x.
    for outcome, color, dash in ((0, BITCOIN_COLOR, ''), (1, BITCOIN_ALTERNATIVE_COLOR, '7 5')):
        start = affected_user_shares(0)[outcome]
        end = affected_user_shares(1)[outcome]
        line(bx(0), by(start), bx(1), by(end), color, 3.5, dash)
    line(bx(0.2), by0, bx(0.2), by(0.8), '#8796a0', 1.2, '4 4')
    dot(bx(0.2), by(0.2), BITCOIN_COLOR, 6)
    dot(bx(0.2), by(0.8), BITCOIN_ALTERNATIVE_COLOR, 6)
    text((bx0 + bx1) / 2, 690, 'Users on implementation A (%)', 18, anchor='middle')
    text(1204, 735, '20% use A · 80% use B', 22, weight='bold')
    text(1204, 769, 'A rejects → 20% affected', 21, BITCOIN_COLOR)
    text(1204, 802, 'B rejects → 80% affected', 21, BITCOIN_ALTERNATIVE_COLOR)

    rect(72, 852, 1556, 76, '#e4f1ed', 14)
    text(101, 901, 'Network progress does not guarantee progress for every user.', 30, '#075e50', 'bold')
    text(72, 964, 'Federation: toy probabilities; common-failure floor 0.01%, shared exposure retained. Bitcoin: impact given disagreement.', 20, '#576875')
    text(72, 995, 'User share does not choose the dominant chain. A rejecting group may follow a separate fork rather than stop entirely.', 20, '#576875')
    svg.extend(('</g>', '</svg>'))
    (OUT / 'implementation-count.svg').write_text('\n'.join(svg), encoding='utf-8')


def main():
    results = [calculate(count) for count in range(1, MAX_IMPLEMENTATIONS + 1)]
    check_model(results)
    check_user_impact()
    write_csv(results)
    write_user_impact_csv()
    write_svg(results)
    print('Model checks passed: federation probabilities and continuous Bitcoin affected-user shares.')
    for row in results:
        print(f'{len(row.allocation):2} implementations: safety failure {100 * row.safety_failure:.6f}%; liveness failure {100 * row.liveness_failure:.6f}%')


if __name__ == '__main__':
    main()
