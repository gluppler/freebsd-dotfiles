import math

from draw import (Figure, Plot, current, dot, flow, ground, keyframes, line, path, rail, rect, terminal, text,
                  travel, two, wire)
from page import code, eq, fig, h3, note, ol, p

NAME = '02-dc'
TITLE = 'DC circuits and their laws'
LEDE = ("Charge, current, voltage and power; Ohm's law and Kirchhoff's two laws, watched as they happen; and the "
        'methods that solve any network of resistors: dividers, equivalent circuits, superposition and node '
        'analysis.')


def period(milliamps):
    """Dot speed is proportional to current: 10 px/s per milliampere."""
    return 1.6 / milliamps


def loop(f, x, y, w, h, source, load, amps):
    """A source on the left edge (+ at the top) driving a load on the right edge."""
    mid = y + h / 2
    two(f, source[0], (x, mid - 30), (x, mid + 30), *source[1:], side=-1)
    two(f, load[0], (x + w, mid - 30), (x + w, mid + 30), *load[1:])
    upper = [(x, mid - 30), (x, y), (x + w, y), (x + w, mid - 30)]
    lower = [(x + w, mid + 30), (x + w, y + h), (x, y + h), (x, mid + 30)]
    wire(f, *upper)
    wire(f, *lower)
    flow(f, upper, period(amps))
    flow(f, lower, period(amps))


def ohm():
    f = Figure(900, 280, "Ohm's law: the same voltage across two resistors, and their lines")
    loop(f, 50, 40, 170, 170, ('V', 'V1', '5 V'), ('R', 'R1', '1 kΩ'), 5)
    text(f, 135, 250, 'I = 5 V / 1 kΩ = 5 mA')
    loop(f, 370, 40, 170, 170, ('V', 'V2', '5 V'), ('R', 'R2', '4 kΩ'), 1.25)
    text(f, 455, 250, 'I = 5 V / 4 kΩ = 1.25 mA')
    plot = Plot(f, 640, 40, 200, 180, (0, 5), (0, 5))
    plot.axes('v (V)', 'i (mA)', [(v, str(v)) for v in range(6)], [(i, str(i)) for i in range(6)], grid=True)
    plot.curve(lambda v: v)
    plot.curve(lambda v: v / 4)
    plot.mark(5, 5, '1 kΩ', 'end', -8, -2)
    plot.mark(5, 1.25, '4 kΩ', 'end', -8, -8)
    text(f, 740, 266, 'slope = 1/R', 'middle', 't s')
    return f


def kcl():
    f = Figure(620, 270, "Kirchhoff's current law at one node")
    node = (300, 135)
    branches = [([(60, 135), node], 3), ([node, (300, 50), (560, 50)], 1), ([node, (300, 220), (560, 220)], 2)]
    for points, amps in branches:
        wire(f, *points)
        flow(f, points, period(amps))
    for x, y in ((60, 135), (560, 50), (560, 220)):
        terminal(f, x, y)
    dot(f, *node, 4.5)
    current(f, 180, 135, 'r', 'i_1 = 3 mA')
    current(f, 440, 50, 'r', 'i_2 = 1 mA')
    current(f, 440, 220, 'r', 'i_3 = 2 mA', side=-1)
    text(f, 314, 128, 'node', 'start', 't s')
    text(f, 470, 140, 'in: 3 mA = out: 1 mA + 2 mA', 'middle', 't s')
    return f


def kvl():
    f = Figure(900, 300, "Kirchhoff's voltage law: a walk around one loop")
    two(f, 'B2', (80, 100), (80, 160), 'BT1', '9 V', side=-1)
    two(f, 'R', (200, 40), (320, 40), 'R1', '1 kΩ')
    two(f, 'R', (440, 80), (440, 180), 'R2', '2 kΩ')
    two(f, 'R', (320, 220), (200, 220), 'R3', '3 kΩ', side=-1)
    wire(f, (80, 100), (80, 40), (200, 40))
    wire(f, (320, 40), (440, 40), (440, 80))
    wire(f, (440, 180), (440, 220), (320, 220))
    wire(f, (200, 220), (80, 220), (80, 160))
    text(f, 260, 72, '−1.5 V', 'middle', 't s')
    text(f, 424, 134, '−3 V', 'end', 't s')
    text(f, 260, 198, '−4.5 V', 'middle', 't s')
    text(f, 100, 134, '+9 V', 'start', 't s')
    text(f, 260, 134, 'I = 9 V / 6 kΩ = 1.5 mA', 'middle', 't s')
    # The walker rises across the battery and falls across each resistor body.
    stops = [((80, 220), 0), ((80, 144), 0), ((80, 116), 9), ((80, 40), 9), ((242, 40), 9), ((278, 40), 7.5),
             ((440, 40), 7.5), ((440, 112), 7.5), ((440, 148), 4.5), ((440, 220), 4.5), ((278, 220), 4.5),
             ((242, 220), 0), ((80, 220), 0)]
    points = [point for point, _ in stops]
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    times, run = [0.0], 0.0
    for size in lengths:
        run += size
        times.append(run / sum(lengths))
    walk = travel(f, 'walk', points, 12, times)
    f.add(f'<g class="{walk}"><circle class="walker" r="8"/></g>')
    plot = Plot(f, 590, 40, 260, 190, (0, 1), (0, 9))
    plot.axes(None, 'potential (V)', [], [(0, '0'), (4.5, '4.5'), (7.5, '7.5'), (9, '9')], grid=True)
    plot.curve([(t, v) for t, (_, v) in zip(times, stops)], 'w curve')
    text(f, 720, 256, 'position around the loop →', 'middle', 't s')
    trace = travel(f, 'trace', [(plot.X(t), plot.Y(v)) for t, (_, v) in zip(times, stops)], 12, times)
    f.add(f'<g class="{trace}"><circle class="walker" r="6"/></g>')
    return f


def series_parallel():
    f = Figure(900, 220, 'Resistors in series and in parallel')
    terminal(f, 40, 90)
    wire(f, (40, 90), (60, 90))
    for i, name in enumerate(('R1', 'R2', 'R3')):
        two(f, 'R', (60 + 100 * i, 90), (160 + 100 * i, 90), name)
    wire(f, (360, 90), (380, 90))
    terminal(f, 380, 90)
    text(f, 210, 150, 'one path: the same current through each', 'middle', 't s')
    text(f, 210, 172, 'the voltages add', 'middle', 't s')
    terminal(f, 500, 40)
    terminal(f, 500, 160)
    wire(f, (500, 40), (800, 40))
    wire(f, (500, 160), (800, 160))
    for i, name in enumerate(('R1', 'R2', 'R3')):
        x = 600 + 100 * i
        two(f, 'R', (x, 40), (x, 160), name)
        if i < 2:
            dot(f, x, 40)
            dot(f, x, 160)
    text(f, 680, 190, 'one voltage across each: the currents add', 'middle', 't s')
    return f


def divider():
    f = Figure(900, 280, 'A voltage divider and a potentiometer sweeping one')
    two(f, 'V', (60, 105), (60, 175), 'V_in', side=-1)
    wire(f, (60, 105), (60, 40), (200, 40), (200, 55))
    two(f, 'R', (200, 55), (200, 115), 'R1')
    two(f, 'R', (200, 145), (200, 205), 'R2')
    wire(f, (200, 115), (200, 145))
    wire(f, (200, 130), (300, 130))
    dot(f, 200, 130)
    terminal(f, 300, 130)
    text(f, 312, 134, 'V_out', 'start')
    wire(f, (200, 205), (200, 230), (60, 230), (60, 175))
    ground(f, 130, 230)
    # The sweep: a long track, a wiper that slides, and a gauge of its voltage.
    rail(f, 567, 50, '+5 V')
    wire(f, (567, 50), (567, 60))
    rect(f, 560, 60, 14, 150)
    wire(f, (567, 210), (567, 226))
    ground(f, 567, 226)
    timing = [(0, 'transform:translateY(0px)'), (50, 'transform:translateY(150px)'), (100, 'transform:translateY(0px)')]
    wiper = keyframes(f, 'wiper', timing, 8, 'ease-in-out', 'transform:translateY(0px)')
    f.add(f'<g class="{wiper}">')
    line(f, 640, 60, 588, 60)
    f.add('<path class="fill" d="M 578 60 L 589 55 L 589 65 Z"/>')
    terminal(f, 640, 60)
    text(f, 652, 64, 'V_out', 'start')
    f.add('</g>')
    rect(f, 760, 60, 22, 150)
    scale = [(0, 'transform:scaleY(1)'), (50, 'transform:scaleY(0)'), (100, 'transform:scaleY(1)')]
    gauge = keyframes(f, 'gauge', scale, 8, 'ease-in-out', 'transform-box:fill-box;transform-origin:50% 100%')
    f.add(f'<rect class="fill {gauge}" x="763" y="63" width="16" height="144"/>')
    for value, y in (('5 V', 64), ('2.5 V', 139), ('0 V', 214)):
        text(f, 792, y, value, 'start', 't s')
    text(f, 771, 44, 'V_out', 'middle', 't s')
    return f


def current_divider():
    f = Figure(560, 270, 'A current divider')
    two(f, 'I', (70, 170), (70, 90), 'I', '3 mA', side=-1)
    two(f, 'R', (220, 100), (220, 160), 'R1', '1 kΩ')
    two(f, 'R', (380, 100), (380, 160), 'R2', '2 kΩ')
    segments = [([(70, 90), (70, 40), (220, 40)], 3), ([(220, 40), (380, 40), (380, 100)], 1),
                ([(220, 40), (220, 100)], 2), ([(220, 160), (220, 220)], 2),
                ([(380, 160), (380, 220), (220, 220)], 1), ([(220, 220), (70, 220), (70, 170)], 3)]
    for points, amps in segments:
        wire(f, *points)
        flow(f, points, period(amps))
    dot(f, 220, 40)
    dot(f, 220, 220)
    text(f, 232, 196, 'I_1 = 2 mA', 'start', 't s')
    text(f, 392, 196, 'I_2 = 1 mA', 'start', 't s')
    return f


def thevenin():
    f = Figure(900, 262, 'A network, its Thévenin equivalent and its Norton equivalent')
    text(f, 150, 256, 'network', 'middle', 't head')
    two(f, 'V', (56, 95), (56, 155), '12 V', side=-1)
    wire(f, (56, 95), (56, 50), (80, 50))
    two(f, 'R', (80, 50), (170, 50), 'R1', '6 kΩ')
    wire(f, (170, 50), (260, 50))
    two(f, 'R', (200, 90), (200, 160), 'R2', '3 kΩ')
    wire(f, (200, 50), (200, 90))
    wire(f, (200, 160), (200, 200))
    wire(f, (56, 155), (56, 200), (260, 200))
    for x, y in ((200, 50), (200, 200)):
        dot(f, x, y)
    text(f, 300, 128, '=', 'middle', 't b')
    text(f, 470, 256, 'Thévenin', 'middle', 't head')
    two(f, 'V', (370, 95), (370, 155), 'V_th', '4 V', side=-1)
    wire(f, (370, 95), (370, 50), (400, 50))
    two(f, 'R', (400, 50), (500, 50), 'R_th', '2 kΩ')
    wire(f, (500, 50), (580, 50))
    wire(f, (370, 155), (370, 200), (580, 200))
    text(f, 615, 128, '=', 'middle', 't b')
    text(f, 770, 256, 'Norton', 'middle', 't head')
    two(f, 'I', (680, 160), (680, 90), 'I_N', '2 mA', side=-1)
    wire(f, (680, 90), (680, 50), (870, 50))
    wire(f, (780, 50), (780, 90))
    two(f, 'R', (780, 90), (780, 160), 'R_N', '2 kΩ')
    wire(f, (780, 160), (780, 200))
    wire(f, (680, 160), (680, 200), (870, 200))
    for x, y in ((780, 50), (780, 200)):
        dot(f, x, y)
    for x in (260, 580, 870):
        terminal(f, x, 50)
        terminal(f, x, 200)
        text(f, x, 34, 'A', 'middle', 't s')
        text(f, x, 224, 'B', 'middle', 't s')
    return f


def terminal_line():
    f = Figure(600, 280, 'The straight-line characteristic of a linear two-terminal network')
    plot = Plot(f, 80, 40, 400, 190, (0, 2.2), (0, 4.5))
    plot.axes('i (mA)', 'v (V)', [(i / 2, f'{i / 2:g}') for i in range(5)], [(v, str(v)) for v in range(5)],
              grid=True)
    plot.curve(lambda i: 4 - 2 * i)
    plot.curve([(0, 0), (2.2, 4.4)], 'w thin dash')
    plot.curve([(0, 0), (0.75, 4.5)], 'w thin dash')
    plot.mark(0, 4, 'V_oc = 4 V', 'start', 8, -6)
    plot.mark(2, 0, 'I_sc = 2 mA', 'start', 8, -14)
    plot.mark(1, 2)
    plot.mark(0.5, 3)
    text(f, plot.X(2.2) + 6, plot.Y(4.4) + 4, 'R_L = 2 kΩ', 'start', 't s')
    text(f, plot.X(0.75) + 6, plot.Y(4.5) + 4, 'R_L = 6 kΩ', 'start', 't s')
    return f


def superposition_panel(f, ox, left, right, title, value):
    text(f, ox + 150, 20, title, 'middle', 't head')
    if left:
        two(f, 'V', (ox + 40, 95), (ox + 40, 155), 'V1', '10 V', side=-1)
    else:
        wire(f, (ox + 40, 95), (ox + 40, 155))
    if right:
        two(f, 'V', (ox + 260, 95), (ox + 260, 155), 'V2', '5 V', side=-1)
    else:
        wire(f, (ox + 260, 95), (ox + 260, 155))
    wire(f, (ox + 40, 95), (ox + 40, 50), (ox + 60, 50))
    two(f, 'R', (ox + 60, 50), (ox + 140, 50), 'R1')
    wire(f, (ox + 140, 50), (ox + 160, 50))
    two(f, 'R', (ox + 160, 50), (ox + 240, 50), 'R2')
    wire(f, (ox + 240, 50), (ox + 260, 50), (ox + 260, 95))
    wire(f, (ox + 150, 50), (ox + 150, 95))
    two(f, 'R', (ox + 150, 95), (ox + 150, 165), 'R3')
    wire(f, (ox + 150, 165), (ox + 150, 200))
    wire(f, (ox + 40, 155), (ox + 40, 200), (ox + 260, 200), (ox + 260, 155))
    dot(f, ox + 150, 50)
    dot(f, ox + 150, 200)
    text(f, ox + 150, 236, f'v = {value}', 'middle')


def superposition():
    f = Figure(900, 250, 'Superposition: each source alone, then added')
    superposition_panel(f, 16, True, True, 'both sources', '5 V')
    superposition_panel(f, 316, True, False, 'V1 alone', '3.33 V')
    superposition_panel(f, 616, False, True, 'V2 alone', '1.67 V')
    return f


def nodal_circuit():
    f = Figure(560, 250, 'A circuit for node analysis')
    two(f, 'I', (60, 170), (60, 90), 'I_S', '1 mA', side=-1)
    wire(f, (60, 90), (60, 50), (230, 50))
    two(f, 'R', (230, 50), (310, 50), 'R2', '1 kΩ')
    wire(f, (310, 50), (380, 50), (380, 90))
    wire(f, (200, 50), (200, 90))
    two(f, 'R', (200, 90), (200, 160), 'R1', '1 kΩ')
    two(f, 'R', (380, 90), (380, 160), 'R3', '2 kΩ')
    wire(f, (200, 160), (200, 210))
    wire(f, (380, 160), (380, 210), (60, 210), (60, 170))
    dot(f, 200, 50, 4)
    dot(f, 380, 50, 4)
    dot(f, 200, 210)
    text(f, 200, 32, 'v_1', 'middle', 't b')
    text(f, 380, 32, 'v_2', 'middle', 't b')
    ground(f, 290, 210)
    return f


NODAL = '''
def solve(A, b):
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    M = [row[:] + [b[r]] for r, row in enumerate(A)]
    for c in range(n):
        top = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[top] = M[top], M[c]
        for r in range(c + 1, n):
            k = M[r][c] / M[c][c]
            for j in range(c, n + 1):
                M[r][j] -= k * M[c][j]
    x = [0.0] * n
    for r in reversed(range(n)):
        x[r] = (M[r][n] - sum(M[r][j] * x[j] for j in range(r + 1, n))) / M[r][r]
    return x


def nodal(nodes, resistors, sources):
    """Node voltages. Resistors are (a, b, ohms); current sources are
    (a, b, amps) pushing current from node a to node b. Node 0 is ground."""
    G = [[0.0] * nodes for _ in range(nodes)]
    i = [0.0] * nodes
    for a, b, ohms in resistors:
        g = 1 / ohms
        for n in (a, b):
            if n:
                G[n - 1][n - 1] += g
        if a and b:
            G[a - 1][b - 1] -= g
            G[b - 1][a - 1] -= g
    for a, b, amps in sources:
        if a:
            i[a - 1] -= amps
        if b:
            i[b - 1] += amps
    return solve(G, i)


print(nodal(2, [(1, 0, 1e3), (1, 2, 1e3), (2, 0, 2e3)], [(0, 1, 1e-3)]))
'''


def nodal_result():
    """Run the listing so the page shows what it really prints."""
    lines = []
    exec(NODAL.replace('print(', 'lines.append('), {'lines': lines})
    v1, v2 = lines[0]
    assert abs(v1 - 0.75) < 1e-12 and abs(v2 - 0.5) < 1e-12, lines
    return f'[{v1:g}, {v2:g}]'


def maximum_power():
    f = Figure(600, 280, 'Load power and efficiency against load resistance')
    plot = Plot(f, 80, 40, 400, 190, (0.1, 10), (0, 1.05), xlog=True)
    plot.axes('R_L / R_th', None, [(0.1, '0.1'), (0.3, '0.3'), (1, '1'), (3, '3'), (10, '10')],
              [(0, '0'), (0.5, '0.5'), (1, '1')], grid=True)
    plot.curve(lambda x: 4 * x / (1 + x) ** 2)
    plot.curve(lambda x: x / (1 + x), 'w curve dash')
    plot.mark(1, 1, 'R_L = R_th: P_max, 50% efficient', 'start', 8, -8)
    text(f, plot.X(0.105), plot.Y(0.62), 'P / P_max', 'start', 't s')
    text(f, plot.X(5), plot.Y(0.64), 'efficiency', 'start', 't s')
    return f


def real_source():
    f = Figure(600, 240, 'A real source: an ideal source behind an internal resistance')
    path(f, 'M 30 30 H 210 V 210 H 30 Z', 'w thin dash')
    text(f, 120, 228, 'battery', 'middle', 't s')
    two(f, 'V', (70, 95), (70, 165), 'V_oc')
    wire(f, (70, 95), (70, 60), (100, 60))
    two(f, 'R', (100, 60), (180, 60), 'R_int')
    wire(f, (180, 60), (330, 60), (330, 95))
    two(f, 'R', (330, 95), (330, 165), 'R_L', 'load')
    wire(f, (330, 165), (330, 190), (70, 190), (70, 165))
    for points in ([(70, 95), (70, 60), (100, 60)], [(180, 60), (330, 60), (330, 95)],
                   [(330, 165), (330, 190), (70, 190), (70, 165)]):
        flow(f, points, 0.8)
    terminal(f, 210, 60)
    terminal(f, 210, 190)
    text(f, 420, 124, 'V = V_oc − I R_int', 'start')
    text(f, 420, 148, 'more current,', 'start', 't s')
    text(f, 420, 164, 'lower terminal voltage', 'start', 't s')
    return f


def sections():
    return [
        ('quantities', 'Charge, current, voltage and power', [
            p('Charge $q$ is measured in coulombs; an electron carries $1.602 \\times 10^{-19}$ C. Current is the '
              'rate at which charge passes a point, so one ampere is one coulomb each second:'),
            eq(r'i = \frac{dq}{dt}', 'Current'),
            p('Voltage is the energy each unit of charge gains or loses between two points, one joule per coulomb '
              'being one volt. A source raises charge to a higher potential; a resistor lets it fall and gives the '
              'energy off as heat.'),
            eq(r'v = \frac{dw}{dq}', 'Voltage'),
            p('Power, the rate of energy transfer, is their product, and energy is power over time:'),
            eq(r'p = v\,i \qquad w = \int p\,dt', 'Power and energy'),
            p('A battery\'s capacity is given as charge, in milliampere-hours. Multiplying by its voltage gives '
              'energy: a 2000 mAh cell at 3.7 V holds 7.4 Wh. At a steady 50 mA it lasts about 40 hours.'),
            eq(r't \approx \frac{Q}{I_{avg}} \qquad E = Q\,V', 'Battery runtime and energy'),
        ]),
        ('ohm', "Ohm's law", [
            p('In a resistor the current is proportional to the voltage across it. The constant is the resistance; '
              'its inverse is the conductance $G$, in siemens.'),
            eq(r'v = i\,R \qquad G = \frac{1}{R}', "Ohm's law"),
            fig(ohm(), 'Two loops with the same 5 V. Four times the resistance gives a quarter of the current, so '
                'the dots move a quarter as fast. On the right each resistor is a straight line through the '
                'origin; a steeper line is a smaller resistance.'),
            p('All the power a resistor takes becomes heat, and its rating, often 1/8 or 1/4 W for small parts, '
              'must exceed it. 5 V across 220 Ω drives 22.7 mA and dissipates 114 mW.'),
            eq(r'P = V I = I^2 R = \frac{V^2}{R}', 'Power in a resistor'),
            p('A conductor\'s resistance grows with its length $L$ and shrinks with its cross-section $A$; '
              'copper\'s resistivity $\\rho$ is $1.68 \\times 10^{-8}$ Ω·m, which matters for long wires and '
              'thin board traces.'),
            eq(r'R = \rho\,\frac{L}{A}', 'Resistance of a conductor'),
        ]),
        ('kcl', "Kirchhoff's current law", [
            p('Charge is conserved and cannot pile up in a wire, so whatever flows into a node flows out. Counting '
              'currents into the node as positive and out as negative, they sum to zero.'),
            eq(r'\sum_k i_k = 0', "Kirchhoff's current law"),
            fig(kcl(), 'Three milliamperes arrive; one leaves by the upper branch and two by the lower. Dot speed '
                'shows each current, and the dots arriving each second equal the dots leaving.'),
        ]),
        ('kvl', "Kirchhoff's voltage law", [
            p('Potential is like height. Walk any closed loop and you come back to where you started, so the rises '
              'and drops met on the way sum to zero.'),
            eq(r'\sum_k v_k = 0', "Kirchhoff's voltage law"),
            fig(kvl(), 'The ring walks the loop clockwise from the bottom left; the graph follows its potential. '
                'The battery lifts it 9 V; R1, R2 and R3 drop 1.5, 3 and 4.5 V, each $v = IR$ with the one loop '
                r'current $I = 1.5\,\mathrm{mA}$, and the walk ends back at 0 V: $9 - 1.5 - 3 - 4.5 = 0$.'),
            p('The wires are flat on the graph: an ideal wire has no resistance, so no voltage across it, and every '
              'point of one node sits at one potential.'),
        ]),
        ('combining', 'Series and parallel', [
            fig(series_parallel(), 'Series parts share one current; parallel parts share one voltage.'),
            p('Resistances in series add. In parallel their conductances add, so the result is always smaller than '
              'the smallest resistor.'),
            eq(r'R_s = R_1 + R_2 + \cdots + R_n', 'Series resistors'),
            eq(r'\frac{1}{R_p} = \frac{1}{R_1} + \frac{1}{R_2} + \cdots + \frac{1}{R_n} \qquad '
               r'R_1 \parallel R_2 = \frac{R_1 R_2}{R_1 + R_2}', 'Parallel resistors'),
            p('Two equal resistors in parallel make half the value; 10 kΩ in parallel with 1 kΩ is 909 Ω, close to '
              'the smaller one.'),
        ]),
        ('dividers', 'Voltage and current dividers', [
            p('Two resistors in series across a voltage share it in proportion to their resistance. This is the '
              'most common circuit there is: it scales a voltage down for an ADC, sets a bias point or a '
              'regulator\'s output, and is what a potentiometer is.'),
            eq(r'V_{out} = V_{in}\,\frac{R_2}{R_1 + R_2}', 'Voltage divider'),
            fig(divider(), 'Left, a fixed divider. Right, a potentiometer is a divider whose ratio you set: as the '
                'wiper slides from the top of the track to the bottom, its voltage falls from 5 V to 0.'),
            p('The formula assumes nothing draws current from the output. A load $R_L$ sits in parallel with '
              '$R_2$ and pulls the output down; keep the load at least ten times $R_2$, or buffer it. To read a '
              'lithium cell, up to 4.2 V, with a 3.3 V ADC, two 100 kΩ resistors halve it to 2.1 V.'),
            p('Current divides between parallel paths in inverse proportion to their resistance; more of it takes '
              'the easier path.'),
            eq(r'I_1 = I\,\frac{R_2}{R_1 + R_2} \qquad I_2 = I\,\frac{R_1}{R_1 + R_2}', 'Current divider'),
            fig(current_divider(), 'Three milliamperes split: two through the 1 kΩ branch, one through the 2 kΩ '
                'branch, and they join again below.'),
        ]),
        ('equivalents', 'Thévenin and Norton equivalents', [
            p('Seen from two terminals, any network of resistors and sources behaves exactly like one voltage '
              'source in series with one resistor (Thévenin), or one current source in parallel with one resistor '
              '(Norton). To find them:'),
            ol('Measure or compute the open-circuit voltage at the terminals: that is $V_{th}$.',
               'Zero every independent source, a voltage source becoming a wire and a current source a gap, and '
               'find the resistance looking into the terminals: that is $R_{th}$. Or short the terminals, find the '
               'current $I_{sc}$, and divide.',
               'The Norton source is the short-circuit current, with the same resistance in parallel.'),
            eq(r'V_{th} = V_{oc} \qquad R_{th} = \frac{V_{oc}}{I_{sc}} \qquad I_N = I_{sc} = \frac{V_{th}}{R_{th}}',
               'Thévenin and Norton'),
            fig(thevenin(), r'The divider gives $V_{oc} = 12 \cdot 3/9 = 4\,\mathrm{V}$; with the source shorted, '
                r'$R_{th} = 6\,\mathrm{k\Omega} \parallel 3\,\mathrm{k\Omega} = 2\,\mathrm{k\Omega}$. Any load '
                'sees the same voltage and current from all three.'),
            fig(terminal_line(), 'Every linear two-terminal network has a straight-line characteristic from '
                '$V_{oc}$ to $I_{sc}$. A load resistor is a line through the origin, and the circuit runs where '
                'the two lines cross.'),
        ]),
        ('superposition', 'Superposition', [
            p('In a linear circuit, one with only resistors, linear dependent sources and independent sources, '
              'the response to several sources is the sum of the responses to each alone, with the others zeroed.'),
            fig(superposition(), r'All resistors are 1 kΩ. Alone, V1 gives $10 \cdot \frac{0.5}{1.5} = 3.33\,'
                r'\mathrm{V}$ and V2 gives $5 \cdot \frac{0.5}{1.5} = 1.67\,\mathrm{V}$ at the middle node; '
                'together, 5 V.'),
            p('Superposition holds for voltages and currents but not for power, which is a product of the two.'),
        ]),
        ('nodal', 'Node analysis: the general method', [
            p('Dividers and equivalents solve small circuits; node analysis solves any of them, and is what circuit '
              'simulators do.'),
            ol('Choose one node as ground.',
               'Name the voltage of every other node: $v_1, v_2, \\ldots$',
               'At each of those nodes, write Kirchhoff\'s current law, with every resistor current written by '
               'Ohm\'s law as $(v_a - v_b)/R$.',
               'Solve the linear equations, $G\\mathbf{v} = \\mathbf{i}$.'),
            fig(nodal_circuit(), 'Two unknown node voltages.'),
            p('The current leaving node 1 through its resistors equals the source current, and at node 2 the '
              'currents balance:'),
            eq(r'\frac{v_1}{R_1} + \frac{v_1 - v_2}{R_2} = I_S \qquad \frac{v_2 - v_1}{R_2} + \frac{v_2}{R_3} = 0'),
            p('In matrix form each resistor appears as its conductance:'),
            eq(r'\begin{bmatrix} \frac{1}{R_1} + \frac{1}{R_2} & -\frac{1}{R_2} \\ -\frac{1}{R_2} & '
               r'\frac{1}{R_2} + \frac{1}{R_3} \end{bmatrix} \begin{bmatrix} v_1 \\ v_2 \end{bmatrix} = '
               r'\begin{bmatrix} I_S \\ 0 \end{bmatrix}', 'Node analysis'),
            p('With the values shown, $v_1 = 0.75$ V and $v_2 = 0.5$ V. Check: 0.75 mA leaves through R1 and '
              '0.25 mA through R2, which is the 0.25 mA that R3 carries to ground.'),
            h3('The algorithm'),
            p('A program builds $G$ by <em>stamping</em> each part into it: a resistor between nodes $a$ and $b$ '
              'adds its conductance to two diagonal entries and subtracts it from the two entries that join them. '
              'Gaussian elimination then solves the system.'),
            code(NODAL),
            p(f'Run, it prints <code>{nodal_result()}</code>. Voltage sources need one extra unknown each, their '
              'current, which gives <em>modified</em> node analysis: the form inside SPICE.'),
        ]),
        ('power', 'Maximum power transfer', [
            p('A source with internal resistance $R_{th}$ delivers the most power to a load of equal resistance. '
              'Half the power is then lost inside the source, so this matters for weak signals, antennas and '
              'audio, not for batteries or supplies, which should feed loads far larger than their own '
              'resistance.'),
            eq(r'P_L = \frac{V_{th}^2\,R_L}{(R_{th} + R_L)^2} \qquad P_{max} = \frac{V_{th}^2}{4 R_{th}}',
               'Maximum power transfer'),
            fig(maximum_power(), 'Load power peaks when $R_L = R_{th}$, at 50% efficiency; efficiency keeps '
                'rising with larger loads while the power falls.'),
        ]),
        ('sources', 'Real sources', [
            fig(real_source(), 'A battery is an ideal source behind its internal resistance. The more current '
                'drawn, the more voltage is lost inside.'),
            eq(r'V = V_{oc} - I\,R_{int}', 'Terminal voltage of a real source'),
            p('Measure $V_{oc}$ with no load, then the voltage $V$ at a known current: '
              '$R_{int} = (V_{oc} - V)/I$. Coin cells have high internal resistance, so a radio burst of tens of '
              'milliamperes sags their voltage; a capacitor across the cell supplies the burst instead.'),
            note('Read more: ' + "MIT 6.002 lectures 2 and 3 (KVL, KCL, node analysis, superposition, Thévenin and "
                 'Norton) and <em>Lessons in Electric Circuits I: DC</em>, in DOCS → CIRCUITS LIBRARY.'),
        ]),
    ]
