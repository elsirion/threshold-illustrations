"""Generate the illustrative chart; see consensus-liveness-model.md for assumptions."""
from pathlib import Path
from math import exp, prod, isclose
from itertools import product
from html import escape
import csv

OUT = Path(__file__).resolve().parent
QUORUM = 7
SIGNERS = 10
BLOCKING_FAILURES = SIGNERS - QUORUM + 1
INITIAL_CONDITIONAL_RISK = 0.5
RESIDUAL_CONDITIONAL_RISK = 0.1
SHARED_FAILURE_PROBABILITY = 0.0001
SINGLE_IMPLEMENTATION_FLOOR = 0.01
# Preserve the requested overall single-codebase floor when shared risk changes.
BUG_TRIGGER_PROBABILITY = (SINGLE_IMPLEMENTATION_FLOOR - SHARED_FAILURE_PROBABILITY) / RESIDUAL_CONDITIONAL_RISK
STRATEGIES = ((10,), (5, 5), (3, 3, 2, 2))
COLORS = ('#b84e34', '#326bb2', '#008371')
MAX_EFFORT = 20
SAMPLES_PER_UNIT = 20


def implementation_risk(effort):
    """Probability a codebase stalls conditional on a bug-trigger scenario."""
    return RESIDUAL_CONDITIONAL_RISK + (INITIAL_CONDITIONAL_RISK - RESIDUAL_CONDITIONAL_RISK) * exp(-effort)


def quorum_loss_risk(effort, allocation):
    """Conditional independent stalls disable every node running the affected codebase."""
    p = implementation_risk(effort / len(allocation))
    return sum(
        prod(p if stalled else 1 - p for stalled in state)
        for state in product((False, True), repeat=len(allocation))
        if sum(size for size, stalled in zip(allocation, state) if stalled) >= BLOCKING_FAILURES
    )


def system_risk(effort, allocation):
    # Shared halt and implementation-specific bug exposure are disjoint scenarios.
    return SHARED_FAILURE_PROBABILITY + BUG_TRIGGER_PROBABILITY * quorum_loss_risk(effort, allocation)


def check_model():
    for effort in (0, 1, 3, 10, 20, 100):
        p1, p2, p4 = (implementation_risk(effort / n) for n in (1, 2, 4))
        expected = (p1, 2*p2 - p2**2, 6*p4**2 - 8*p4**3 + 3*p4**4)
        for allocation, probability in zip(STRATEGIES, expected):
            assert sum(allocation) == SIGNERS, 'Every strategy must use ten nodes'
            assert isclose(quorum_loss_risk(effort, allocation), probability, abs_tol=1e-12)
            assert SHARED_FAILURE_PROBABILITY <= system_risk(effort, allocation) <= 0.08
    assert isclose(system_risk(100, STRATEGIES[0]), SINGLE_IMPLEMENTATION_FLOOR), 'Single-codebase floor is 1%'
    for allocation in STRATEGIES:
        values = [system_risk(i/SAMPLES_PER_UNIT, allocation) for i in range(MAX_EFFORT*SAMPLES_PER_UNIT+1)]
        assert all(a >= b for a, b in zip(values, values[1:])), 'Hardening must reduce risk'
    assert BLOCKING_FAILURES == 4, 'Four unavailable nodes prevent a seven-node quorum'
    assert system_risk(0, STRATEGIES[0]) < system_risk(0, STRATEGIES[2]), 'Splitting effort can initially worsen liveness'
    assert system_risk(20, STRATEGIES[2]) < system_risk(20, STRATEGIES[0]) < system_risk(20, STRATEGIES[1])


check_model()
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="1020" viewBox="0 0 1700 1020">',
       '<rect width="1700" height="1020" fill="#f8fafb"/>',
       '<g font-family="DejaVu Sans, sans-serif">']


def text(x, y, value, size=22, fill='#1b2935', weight='normal', anchor='start'):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


def line(x1, y1, x2, y2, stroke='#dce3e8', width=1, dash=''):
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}" stroke-dasharray="{dash}"/>')


def rect(x, y, w, h, fill, radius=0):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>')


text(72, 93, 'Consensus Liveness Illustrative Model', 47, weight='bold')
text(72, 140, 'Independent implementations can keep a federation running when one codebase stalls.', 23, '#576875')
text(130, 214, 'Likelihood of a bug-induced quorum halt', 25, weight='bold')
text(130, 246, '7-of-10 federation · lower is better', 20, '#576875')
x0, x1, y0, y1 = 130, 1000, 722, 287
px = lambda effort: x0 + (x1-x0)*effort/MAX_EFFORT
py = lambda probability: y0 - (y0-y1)*probability/0.08
for tick in range(5):
    percent = tick*2
    y = py(percent/100)
    line(x0, y, x1, y)
    text(x0-20, y+7, f'{percent:.1f}%', 20, '#576875', anchor='end')
for effort in range(0, MAX_EFFORT+1, 5):
    x = px(effort)
    line(x, y0, x, y0+7, '#9aaab5')
    text(x, y0+34, str(effort), 20, '#576875', anchor='middle')
line(x0, y0, x1, y0, '#9aaab5', 1.5)
text((x0+x1)/2, 800, 'Total hardening effort (arbitrary units)', 23, anchor='middle')
for allocation, color in zip(STRATEGIES, COLORS):
    points = ' '.join(f'{px(i/SAMPLES_PER_UNIT):.2f},{py(system_risk(i/SAMPLES_PER_UNIT, allocation)):.2f}' for i in range(MAX_EFFORT*SAMPLES_PER_UNIT+1))
    svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linejoin="round"/>')
for allocation, color, y in zip(STRATEGIES, COLORS, (668, 615, 701)):
    p = system_risk(MAX_EFFORT, allocation)
    line(x1, py(p), x1+22, y-6, color, 1.5)
    text(x1+29, y, f'{100*p:.2f}%', 22, color, 'bold')

rect(1174, 192, 454, 614, '#edf2f5', 18)
text(1204, 235, '10 NODES · 7 REQUIRED', 22, '#576875', 'bold')
labels = ('1 implementation', '2 implementations', '4 implementations')
requirements = ('Halts if A stalls', 'Halts if either A or B stalls', 'Halts if any 2 codebases stall')
assignments = ('AAAAAAAAAA', 'AAAAABBBBB', 'AAABBBCCDD')
for index, (label, requirement, assignment, color) in enumerate(zip(labels, requirements, assignments, COLORS)):
    y = 299 + index*167
    line(1204, y-7, 1236, y-7, color, 5)
    text(1250, y, label, 24, color, 'bold')
    for j, codebase in enumerate(assignment):
        x = 1205+j*39
        rect(x, y+23, 33, 45, '#ffffff', 7)
        text(x+16.5, y+54, codebase, 21, color, 'bold', 'middle')
    text(1204, y+102, requirement, 19)
text(1204, 777, 'Same letter = same codebase', 18, '#576875')

rect(72, 844, 1556, 76, '#e4f1ed', 14)
text(101, 893, 'Keep a quorum running—not necessarily every node.', 31, '#075e50', 'bold')
text(72, 961, 'Toy model: stalled nodes, not all consensus bugs. Common-failure floor: 0.01%; shared-trigger correlation retained.', 20, '#576875')
text(72, 992, 'Equal hardening budget. Remaining nodes agree; interoperability bugs, recovery and startup costs are excluded.', 20, '#576875')
svg.extend(('</g>', '</svg>'))
(OUT/'consensus-liveness.svg').write_text('\n'.join(svg))
with (OUT/'consensus-liveness.csv').open('w', newline='') as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(('total_hardening_effort', 'one_implementation', 'two_implementations', 'four_implementations'))
    for step in range(MAX_EFFORT*SAMPLES_PER_UNIT+1):
        effort = step/SAMPLES_PER_UNIT
        writer.writerow((effort, *(system_risk(effort, allocation) for allocation in STRATEGIES)))
print('Model checks passed. SVG and CSV written.')
for allocation in STRATEGIES:
    print(f'{len(allocation)} implementations: risk at E=20 is {100*system_risk(20, allocation):.3f}%')
