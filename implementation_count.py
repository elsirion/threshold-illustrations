"""Plot fixed-budget risk across codebase counts; see implementation-count-model.md."""
from dataclasses import dataclass
from pathlib import Path
from itertools import product
from math import exp, isclose, log10, prod
from html import escape
import csv

OUT = Path(__file__).resolve().parent
NODES = 10
QUORUM = 7
BLOCKING_FAILURES = NODES - QUORUM + 1
TOTAL_EFFORT = 20
INITIAL_CONDITIONAL_RISK = 0.5
RESIDUAL_CONDITIONAL_RISK = 0.1
SHARED_FAILURE_PROBABILITY = 0.0001
SINGLE_IMPLEMENTATION_FLOOR = 0.01
EXPOSURE_PROBABILITY = (SINGLE_IMPLEMENTATION_FLOOR - SHARED_FAILURE_PROBABILITY) / RESIDUAL_CONDITIONAL_RISK
SAFETY_COLOR = '#b84e34'
LIVENESS_COLOR = '#326bb2'


@dataclass(frozen=True)
class Result:
    allocation: tuple[int, ...]
    conditional_codebase_risk: float
    safety_failure: float
    liveness_failure: float


def balanced_allocation(count):
    if not 1 <= count <= NODES:
        raise ValueError(f'Implementation count must be between 1 and {NODES}')
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
    for row in results:
        allocation = row.allocation
        assert sum(allocation) == NODES, 'Node count must stay fixed'
        assert max(allocation) - min(allocation) <= 1, 'Allocation must be balanced'
        assert SHARED_FAILURE_PROBABILITY <= row.safety_failure <= row.liveness_failure <= 1
        # Independently convolve each group's node count to check enumeration.
        for probability in (0, row.conditional_codebase_risk, 0.5, 1):
            distribution = [1.0] + [0.0] * NODES
            for size in allocation:
                updated = [0.0] * (NODES + 1)
                for failed_nodes, mass in enumerate(distribution):
                    updated[failed_nodes] += mass * (1 - probability)
                    if failed_nodes + size <= NODES:
                        updated[failed_nodes + size] += mass * probability
                distribution = updated
            assert isclose(sum(distribution), 1, abs_tol=1e-12), 'Probability mass must be preserved'
            for threshold in (QUORUM, BLOCKING_FAILURES):
                assert isclose(failure_probability(allocation, probability, threshold), sum(distribution[threshold:]), abs_tol=1e-12)
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

    text(72, 93, 'Safety & Liveness vs. Implementation Count', 47, weight='bold')
    text(72, 140, '7-of-10 federation · high total effort fixed at 20 units, split equally across codebases.', 23, '#576875')
    text(130, 211, 'Failure probability · log scale · lower is better', 24, weight='bold')
    line(130, 250, 165, 250, SAFETY_COLOR, 4)
    text(180, 257, 'Fund safety: unauthorized signing', 20, SAFETY_COLOR)
    line(650, 250, 685, 250, LIVENESS_COLOR, 4)
    text(700, 257, 'Liveness: quorum halt', 20, LIVENESS_COLOR)

    x0, x1, y0, y1 = 130, 1020, 738, 300
    lower, upper = SHARED_FAILURE_PROBABILITY, 0.02
    px = lambda count: x0 + (x1 - x0) * (count - 1) / (NODES - 1)
    py = lambda probability: y0 - (y0 - y1) * (log10(probability) - log10(lower)) / (log10(upper) - log10(lower))
    for percent in (0.01, 0.03, 0.1, 0.3, 1, 2):
        y = py(percent / 100)
        line(x0, y, x1, y)
        text(x0 - 18, y + 7, f'{percent:g}%', 20, '#576875', anchor='end')
    line(x0, y0, x1, y0, '#8796a0', 1.5, '5 5')
    for count in range(1, NODES + 1):
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
    # Both metrics coincide at one codebase; concentric markers keep both visible.
    dot(px(1), py(results[0].safety_failure), SAFETY_COLOR, 8)
    dot(px(1), py(results[0].liveness_failure), LIVENESS_COLOR, 4)

    rect(1174, 192, 454, 636, '#edf2f5', 18)
    text(1204, 235, 'BALANCED NODE ALLOCATIONS', 20, '#576875', 'bold')
    text(1204, 274, 'Impls', 18, '#576875')
    text(1300, 274, 'Nodes per codebase', 18, '#576875')
    for index, row in enumerate(results):
        y = 315 + index * 44
        text(1226, y, str(len(row.allocation)), 22, weight='bold', anchor='middle')
        text(1300, y, '+'.join(map(str, row.allocation)), 21)
        if index < NODES - 1:
            line(1204, y + 15, 1598, y + 15, '#dce3e8')
    text(1204, 792, 'Same 10 nodes at every point.', 19, '#576875')

    rect(72, 852, 1556, 76, '#e4f1ed', 14)
    text(101, 901, 'The quorum and allocation matter—not just implementation count.', 30, '#075e50', 'bold')
    text(72, 964, 'Toy probabilities, not estimates. Common-failure floor: 0.01%; shared-exposure correlation retained.', 20, '#576875')
    text(72, 995, 'Finite effort, not the infinite-effort limit. Liveness assumes stalled nodes; interoperability and startup costs excluded.', 20, '#576875')
    svg.extend(('</g>', '</svg>'))
    (OUT / 'implementation-count.svg').write_text('\n'.join(svg), encoding='utf-8')


def main():
    results = [calculate(count) for count in range(1, NODES + 1)]
    check_model(results)
    write_csv(results)
    write_svg(results)
    print('Model checks passed, including agreement with existing charts at E=20.')
    for row in results:
        print(f'{len(row.allocation):2} implementations: safety failure {100 * row.safety_failure:.6f}%; liveness failure {100 * row.liveness_failure:.6f}%')


if __name__ == '__main__':
    main()
