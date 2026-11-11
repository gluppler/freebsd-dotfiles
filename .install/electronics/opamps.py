import math
import random

from draw import (Figure, Plot, arrow, circle, dot, flow, flow_by, ground, head, line, opamp, path, rail, rect,
                  steps, sweep, terminal, text, travel, two, wire)
from page import eq, fig, note, ol, p, table

NAME = '05-opamps'
TITLE = 'Op-amps and comparators'
LEDE = ('The amplifier with two inputs and enormous gain, tamed by negative feedback into precise gains, sums, '
        'differences, integrals and filters; comparators and the Schmitt trigger; and the limits of real parts.')


def open_loop():
    f = Figure(900, 270, 'An op-amp and its open-loop transfer curve')
    pins = opamp(f, 170, 140, plus_top=True, supplies=True)
    for name, y, label in (('+', 128, 'v_+'), ('-', 152, 'v_−')):
        wire(f, (100, y), pins[name])
        terminal(f, 100, y)
        text(f, 90, y + 4, label, 'end')
    wire(f, pins['out'], (250, 140))
    terminal(f, 250, 140)
    text(f, 260, 144, 'v_out', 'start')
    rail(f, 170, 110, '+V_S')
    path(f, 'M 170 170 V 180 M 161 180 H 179')
    text(f, 170, 197, '−V_S')
    plot = Plot(f, 420, 30, 400, 210, (-200, 200), (-15, 15))
    plot.axes(None, 'v_out (V)', [(-200, '−200'), (-100, '−100'), (100, '100'), (200, '200')],
              [(-12, '−12'), (12, '12')], grid=True, xzero=0, yzero=0)
    plot.curve([(-200, -12), (-120, -12), (120, 12), (200, 12)])
    text(f, plot.X(100), plot.Y(-7), 'v_+ − v_− (µV)', 'middle', 't s')
    text(f, plot.X(160), plot.Y(12) - 8, '+V_sat', 'middle', 't s')
    text(f, plot.X(-160), plot.Y(-12) + 18, '−V_sat', 'middle', 't s')
    text(f, plot.X(-14), plot.Y(6), 'gain A ≈ 100 000 →', 'end', 't s')
    return f


def feedback():
    f = Figure(900, 210, 'Negative feedback: the output subtracts a fraction of itself from the input')
    circle(f, 200, 80, 14)
    path(f, 'M 190 70 L 210 90 M 190 90 L 210 70', 'w thin')
    arrow(f, 70, 80, 186, 80, 'w', 8)
    arrow(f, 214, 80, 320, 80, 'w', 8)
    rect(f, 320, 55, 100, 50)
    text(f, 370, 85, 'A', 'middle', 't b')
    arrow(f, 420, 80, 640, 80, 'w', 8)
    dot(f, 540, 80)
    wire(f, (540, 80), (540, 160))
    arrow(f, 540, 160, 420, 160, 'w', 8)
    rect(f, 320, 135, 100, 50)
    text(f, 370, 165, 'β', 'middle', 't b')
    wire(f, (320, 160), (200, 160))
    arrow(f, 200, 160, 200, 94, 'w', 8)
    text(f, 60, 84, 'x', 'end', 't b')
    text(f, 180, 70, '+', 'end')
    text(f, 190, 120, '−', 'end')
    text(f, 267, 70, 'e = x − βy', 'middle', 't s')
    text(f, 650, 84, 'y = A e', 'start', 't b')
    text(f, 650, 140, 'y = x A / (1 + Aβ)', 'start', 't s')
    text(f, 650, 158, '≈ x / β when Aβ ≫ 1', 'start', 't s')
    return f


def inverting():
    f = Figure(900, 270, 'An inverting amplifier: one current through both resistors, none into the input')
    period = 4
    pins = opamp(f, 330, 150)
    terminal(f, 80, 138)
    text(f, 70, 142, 'v_in', 'end')
    wire(f, (80, 138), (110, 138))
    two(f, 'R', (110, 138), (190, 138), 'R_in', '10 kΩ')
    wire(f, (190, 138), pins['-'])
    dot(f, 240, 138)
    wire(f, (240, 138), (240, 70), (300, 70))
    two(f, 'R', (300, 70), (380, 70), 'R_f', '20 kΩ')
    wire(f, (380, 70), (400, 70), (400, 150))
    wire(f, pins['out'], (440, 150))
    dot(f, 400, 150)
    terminal(f, 440, 150)
    text(f, 450, 154, 'v_out', 'start')
    wire(f, pins['+'], (280, 162), (280, 196))
    ground(f, 280, 196)
    text(f, 236, 186, 'virtual ground, 0 V', 'end', 't s')
    swing = lambda t: 22 * (1 - math.cos(2 * math.pi * t / period))
    for k, points in enumerate(([(80, 138), (110, 138)], [(190, 138), (240, 138), (240, 70), (300, 70)],
                                [(380, 70), (400, 70), (400, 150), (366, 150)])):
        flow_by(f, points, f'i{k}', swing, period)
    plot = Plot(f, 530, 40, 330, 190, (0, 2), (-2.4, 2.4))
    plot.axes('t', None, [(1, ''), (2, '')], [(2, '2'), (1, '1'), (-1, '−1'), (-2, '−2')], grid=True, yzero=0)
    plot.curve(lambda x: math.sin(2 * math.pi * x), 'w curve dash')
    plot.curve(lambda x: -2 * math.sin(2 * math.pi * x))
    text(f, 695, 22, 'dashed: v_in   solid: v_out', 'middle', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(2), plot.y, plot.y + plot.h, 2 * period)
    return f


def non_inverting():
    f = Figure(900, 290, 'A non-inverting amplifier and a voltage follower')
    pins = opamp(f, 230, 120, plus_top=True)
    terminal(f, 90, 108)
    text(f, 80, 112, 'v_in', 'end')
    wire(f, (90, 108), pins['+'])
    wire(f, pins['out'], (330, 120))
    terminal(f, 330, 120)
    text(f, 340, 124, 'v_out', 'start')
    dot(f, 300, 120)
    wire(f, pins['-'], (170, 132), (170, 200))
    dot(f, 170, 190)
    wire(f, (170, 190), (190, 190))
    two(f, 'R', (190, 190), (270, 190), 'R_f')
    wire(f, (270, 190), (300, 190), (300, 120))
    two(f, 'R', (170, 200), (170, 250), 'R_g', side=-1)
    ground(f, 170, 250)
    text(f, 230, 285, 'non-inverting: gain 1 + R_f / R_g', 'middle', 't s')
    pins = opamp(f, 640, 120, plus_top=True)
    terminal(f, 520, 108)
    text(f, 510, 112, 'v_in', 'end')
    wire(f, (520, 108), pins['+'])
    wire(f, pins['out'], (750, 120))
    terminal(f, 750, 120)
    text(f, 760, 124, 'v_out', 'start')
    dot(f, 710, 120)
    wire(f, pins['-'], (590, 132), (590, 180), (710, 180), (710, 120))
    text(f, 640, 285, 'follower: gain 1, a buffer for weak sources', 'middle', 't s')
    return f


def arithmetic():
    f = Figure(900, 300, 'A summing amplifier and a difference amplifier')
    pins = opamp(f, 300, 150)
    for k, y in enumerate((80, 138, 196)):
        terminal(f, 40, y)
        text(f, 40, y - 10, f'v_{k + 1}')
        wire(f, (40, y), (60, y))
        two(f, 'R', (60, y), (140, y), f'R_{k + 1}')
        wire(f, (140, y), (200, y))
    wire(f, (200, 80), (200, 196))
    wire(f, (200, 138), pins['-'])
    dot(f, 200, 138)
    dot(f, 230, 138)
    wire(f, (230, 138), (230, 40), (270, 40))
    two(f, 'R', (270, 40), (350, 40), 'R_f')
    wire(f, (350, 40), (370, 40), (370, 150))
    wire(f, pins['out'], (400, 150))
    dot(f, 370, 150)
    terminal(f, 400, 150)
    text(f, 410, 154, 'v_out', 'start')
    wire(f, pins['+'], (250, 162), (250, 200))
    ground(f, 250, 200)
    text(f, 220, 292, 'summing: v_out = −R_f (v_1/R_1 + v_2/R_2 + v_3/R_3)', 'middle', 't s')
    pins = opamp(f, 720, 150)
    terminal(f, 500, 138)
    text(f, 490, 142, 'v_1', 'end')
    wire(f, (500, 138), (520, 138))
    two(f, 'R', (520, 138), (600, 138), 'R_1')
    wire(f, (600, 138), pins['-'])
    dot(f, 640, 138)
    wire(f, (640, 138), (640, 70), (660, 70))
    two(f, 'R', (660, 70), (740, 70), 'R_2')
    wire(f, (740, 70), (790, 70), (790, 150))
    wire(f, pins['out'], (830, 150))
    dot(f, 790, 150)
    terminal(f, 830, 150)
    text(f, 830, 172, 'v_out')
    terminal(f, 500, 220)
    text(f, 490, 224, 'v_2', 'end')
    wire(f, (500, 220), (520, 220))
    two(f, 'R', (520, 220), (600, 220), 'R_1', side=-1)
    wire(f, (600, 220), (660, 220), (660, 162), pins['+'])
    dot(f, 660, 220)
    two(f, 'R', (660, 220), (660, 256), 'R_2')
    ground(f, 660, 256)
    text(f, 690, 292, 'difference: v_out = (R_2/R_1)(v_2 − v_1)', 'middle', 't s')
    return f


def integrator():
    f = Figure(900, 270, 'An integrator turning a square wave into a triangle wave')
    period = 4
    pins = opamp(f, 300, 150)
    terminal(f, 80, 138)
    text(f, 70, 142, 'v_in', 'end')
    wire(f, (80, 138), (110, 138))
    two(f, 'R', (110, 138), (190, 138), 'R')
    wire(f, (190, 138), pins['-'])
    dot(f, 230, 138)
    wire(f, (230, 138), (230, 70), (276, 70))
    two(f, 'C', (276, 70), (300, 70), 'C')
    wire(f, (300, 70), (370, 70), (370, 150))
    wire(f, pins['out'], (410, 150))
    dot(f, 370, 150)
    terminal(f, 410, 150)
    text(f, 420, 154, 'v_out', 'start')
    wire(f, pins['+'], (250, 162), (250, 200))
    ground(f, 250, 200)
    passed = lambda t: 12 * (t if t < period / 2 else period - t)
    for k, points in enumerate(([(80, 138), (110, 138)], [(190, 138), (230, 138), (230, 70), (276, 70)],
                                [(300, 70), (370, 70), (370, 150), (336, 150)])):
        flow_by(f, points, f'i{k}', passed, period)
    plot = Plot(f, 520, 40, 340, 190, (0, 2), (-1.3, 1.3))
    plot.axes('t', None, [(1, ''), (2, '')], [], grid=True, yzero=0)
    plot.curve([(0, 1), (0.5, 1), (0.5, -1), (1, -1), (1, 1), (1.5, 1), (1.5, -1), (2, -1)], 'w curve dash')
    plot.curve([(0, 1), (0.5, -1), (1, 1), (1.5, -1), (2, 1)])
    text(f, 690, 22, 'dashed: v_in   solid: v_out', 'middle', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(2), plot.y, plot.y + plot.h, 2 * period)
    return f


def sallen_key():
    f = Figure(900, 270, 'A unity-gain Sallen–Key low-pass filter and its response')
    pins = opamp(f, 420, 150, plus_top=True)
    terminal(f, 50, 138)
    text(f, 40, 142, 'v_in', 'end')
    wire(f, (50, 138), (70, 138))
    two(f, 'R', (70, 138), (150, 138), 'R_1')
    wire(f, (150, 138), (210, 138))
    dot(f, 190, 138)
    two(f, 'R', (210, 138), (290, 138), 'R_2')
    wire(f, (290, 138), pins['+'])
    dot(f, 330, 138)
    wire(f, (330, 138), (330, 176))
    two(f, 'C', (330, 176), (330, 210), 'C_2', side=-1)
    ground(f, 330, 210)
    wire(f, (190, 138), (190, 60), (290, 60))
    two(f, 'C', (290, 60), (314, 60), 'C_1')
    wire(f, (314, 60), (490, 60), (490, 230))
    wire(f, pins['-'], (370, 162), (370, 230), (490, 230))
    wire(f, pins['out'], (530, 150))
    dot(f, 490, 150)
    terminal(f, 530, 150)
    text(f, 530, 172, 'v_out')
    plot = Plot(f, 590, 40, 230, 190, (0.1, 10), (-40, 5), xlog=True)
    plot.axes('f / f_c', 'gain (dB)', [(0.1, '0.1'), (1, '1'), (10, '10')], [(0, '0'), (-20, '−20'), (-40, '−40')],
              grid=True)
    plot.curve(lambda x: -10 * math.log10(1 + x * x), 'w curve dash')
    plot.curve(lambda x: -10 * math.log10(1 + x ** 4))
    text(f, plot.X(0.12), plot.Y(-28), 'dashed: 1st order', 'start', 't s')
    text(f, plot.X(0.12), plot.Y(-28) + 15, 'solid: 2nd order', 'start', 't s')
    return f


def noisy():
    """Two cycles of a sine with smoothed noise, 200 samples a cycle, the same on every build."""
    rng, level, out = random.Random(7), 0.0, []
    for k in range(401):
        level = 0.6 * level + 0.4 * rng.uniform(-1, 1)
        out.append((k / 200, math.sin(2 * math.pi * k / 200) + 0.5 * level))
    return out


def comparators():
    f = Figure(900, 320, 'A comparator and a Schmitt trigger fed the same noisy signal')
    data = noisy()
    plain = [(t, 1 if v > 0 else -1) for t, v in data]
    state, schmitt = -1, []
    for t, v in data:
        state = 1 if v > 0.5 else -1 if v < -0.5 else state
        schmitt.append((t, state))
    edges = lambda trace: sum(a[1] != b[1] for a, b in zip(trace, trace[1:]))
    assert edges(schmitt) == 4 and edges(plain) > 8, (edges(schmitt), edges(plain))
    top = Plot(f, 120, 20, 720, 120, (0, 2), (-1.5, 1.5))
    top.axes(None, None, [], [], yzero=0)
    top.curve(data, 'w thin')
    for level, name in ((0.5, '+V_T'), (-0.5, '−V_T')):
        line(f, top.X(0), top.Y(level), top.X(2), top.Y(level), 'w thin dash')
        text(f, top.X(2) + 8, top.Y(level) + 4, name, 'start', 't s')
    text(f, 108, 84, 'input', 'end', 't s')
    for y, name, trace in ((170, 'comparator', plain), (250, 'Schmitt', schmitt)):
        plot = Plot(f, 120, y, 720, 50, (0, 2), (-1.3, 1.3))
        plot.axes(None, None, [], [], yzero=0)
        plot.curve(steps(trace))
        text(f, 108, y + 29, name, 'end', 't s')
    sweep(f, 'cursor', top.X(0), top.X(2), 14, 306, 8)
    return f


def hysteresis():
    f = Figure(900, 280, 'A Schmitt trigger and its hysteresis loop')
    pins = opamp(f, 260, 140, plus_top=True)
    terminal(f, 60, 128)
    text(f, 50, 132, 'v_in', 'end')
    wire(f, (60, 128), (80, 128))
    two(f, 'R', (80, 128), (160, 128), 'R_1', '10 kΩ', side=-1)
    wire(f, (160, 128), pins['+'])
    dot(f, 190, 128)
    wire(f, (190, 128), (190, 60), (220, 60))
    two(f, 'R', (220, 60), (300, 60), 'R_2', '100 kΩ')
    wire(f, (300, 60), (330, 60), (330, 140))
    wire(f, pins['out'], (370, 140))
    dot(f, 330, 140)
    terminal(f, 370, 140)
    text(f, 380, 144, 'v_out', 'start')
    wire(f, pins['-'], (210, 152), (210, 190))
    ground(f, 210, 190)
    plot = Plot(f, 540, 40, 300, 200, (-1.4, 1.4), (-1.4, 1.4))
    plot.axes('v_in', 'v_out', [(-0.5, ''), (0.5, '')], [], xzero=0, yzero=0)
    loop = [(-1.3, -1), (0.5, -1), (0.5, 1), (1.3, 1), (-0.5, 1), (-0.5, -1), (-1.3, -1)]
    plot.curve(loop, 'w bold')
    for vx, vy, angle in ((0.5, 0.1, -math.pi / 2), (-0.5, -0.1, math.pi / 2), (-0.5, -1, 0), (0.5, 1, math.pi)):
        f.add(head(plot.X(vx), plot.Y(vy), angle, 10))
    text(f, plot.X(0.5) + 6, plot.Y(0) + 16, '+V_T', 'start', 't s')
    text(f, plot.X(-0.5) - 6, plot.Y(0) - 8, '−V_T', 'end', 't s')
    text(f, plot.X(1.3) + 6, plot.Y(1) + 4, '+V_sat', 'start', 't s')
    text(f, plot.X(-1.3) - 6, plot.Y(-1) + 4, '−V_sat', 'end', 't s')
    unit = 0.96 / 5.2
    times = [0]
    for size in (1.8 * unit, 0.02, 0.8 * unit, 1.8 * unit, 0.02, 0.8 * unit):
        times.append(times[-1] + size)
    walk = travel(f, 'walk', [(plot.X(vx), plot.Y(vy)) for vx, vy in loop], 8, times)
    f.add(f'<g class="{walk}"><circle class="walker" r="6"/></g>')
    return f


def slew(t, rate=3.2, step=0.001):
    """A follower's output chasing a 1 V, 1 Hz sine at a limited slew rate in V/s."""
    v, out = 0.0, [(0.0, 0.0)]
    for k in range(1, round(t / step) + 1):
        goal = math.sin(2 * math.pi * k * step)
        v += max(-rate * step, min(rate * step, goal - v))
        if k % 10 == 0:
            out.append((k * step, v))
    return out


def limits():
    f = Figure(900, 290, 'Gain against frequency for a 1 MHz op-amp, and a sine distorted by slew-rate limiting')
    plot = Plot(f, 80, 30, 460, 210, (1, 1e7), (-10, 110), xlog=True)
    names = ('1', '10', '100', '1k', '10k', '100k', '1M', '10M')
    plot.axes('f (Hz)', 'gain (dB)', [(10 ** k, name) for k, name in enumerate(names)],
              [(v, str(v)) for v in range(0, 101, 20)], grid=True)
    plot.curve(lambda x: 100 - 10 * math.log10(1 + (x / 10) ** 2))
    plot.curve(lambda x: 20 - 10 * math.log10(1 + (x / 1e5) ** 2), 'w curve dash')
    plot.mark(1e5, 17, '−3 dB at 100 kHz', 'end', -8, 18)
    plot.mark(1e6, 0, 'f_T = 1 MHz', 'start', 8, -8)
    text(f, plot.X(2), plot.Y(52), 'solid: open loop', 'start', 't s')
    text(f, plot.X(2), plot.Y(52) + 15, 'dashed: gain of 10', 'start', 't s')
    slow = Plot(f, 680, 50, 180, 180, (0, 2), (-1.3, 1.3))
    slow.axes('t', None, [(1, ''), (2, '')], [], yzero=0)
    slow.curve(lambda x: math.sin(2 * math.pi * x), 'w curve dash')
    slow.curve(slew(2))
    text(f, 770, 30, 'too fast for the slew rate', 'middle', 't s')
    return f


def photodiode():
    f = Figure(900, 260, 'A transimpedance amplifier turning photodiode current into a voltage')
    pins = opamp(f, 360, 150)
    two(f, 'PD', (230, 226), (230, 166), 'D1')
    ground(f, 230, 226)
    wire(f, (230, 166), (230, 138), pins['-'])
    dot(f, 270, 138)
    wire(f, (270, 138), (270, 70), (310, 70))
    two(f, 'R', (310, 70), (390, 70), 'R_f', '1 MΩ', side=-1)
    wire(f, (390, 70), (430, 70), (430, 150))
    wire(f, (290, 70), (290, 30), (336, 30))
    two(f, 'C', (336, 30), (360, 30), 'C_f')
    wire(f, (360, 30), (410, 30), (410, 70))
    dot(f, 290, 70)
    dot(f, 410, 70)
    wire(f, pins['out'], (470, 150))
    dot(f, 430, 150)
    terminal(f, 470, 150)
    text(f, 480, 154, 'v_out', 'start')
    wire(f, pins['+'], (310, 162), (310, 200))
    ground(f, 310, 200)
    flow(f, [(396, 150), (430, 150), (430, 70), (390, 70)], 1.6)
    flow(f, [(310, 70), (290, 70), (270, 70), (270, 138), (230, 138), (230, 166)], 1.6)
    text(f, 560, 120, 'v_out = I_p R_f', 'start')
    text(f, 560, 144, '1 µA of light → 1 V', 'start', 't s')
    text(f, 560, 160, 'C_f keeps it from oscillating', 'start', 't s')
    return f


def sections():
    return [
        ('ideal', 'The op-amp', [
            p('An operational amplifier has two inputs and one output. It amplifies the difference between its '
              'inputs by an enormous gain $A$, 100 000 or more, so a few microvolts of difference drive the '
              'output all the way to one of its supply rails.'),
            eq(r'v_{out} = A\,(v_+ - v_-)', 'Op-amp, open loop'),
            fig(open_loop(), 'Left: the symbol, with its supplies drawn; schematics often leave them off. Right: '
                'the output against the input difference. The slope is so steep that the output is almost '
                'always pinned at a rail unless feedback holds it in the narrow linear region.'),
            p('Used like this, with no feedback, it is a comparator. Every other use wraps feedback around it.'),
        ]),
        ('feedback', 'Negative feedback and the golden rules', [
            p('Feed a fraction $\\beta$ of the output back and subtract it from the input. The amplifier then '
              'works on the error, and with $A$ huge the error shrinks almost to nothing: the gain depends only '
              'on $\\beta$, set by resistors, and no longer on the transistors inside.'),
            fig(feedback(), 'The loop: the amplifier sees only the difference $e$ between the input and the '
                'fed-back fraction of its output.'),
            eq(r'\frac{y}{x} = \frac{A}{1 + A\beta} \approx \frac{1}{\beta}', 'Negative feedback'),
            p('Two rules then solve almost every op-amp circuit:'),
            ol('No current flows into either input.',
               'With negative feedback, the output does whatever makes $v_+ = v_-$.'),
        ]),
        ('inverting', 'The inverting amplifier', [
            fig(inverting(), 'The + input is grounded, so the output holds the − input at 0 V too: a virtual '
                'ground. The input current $v_{in}/R_{in}$ cannot enter the op-amp, so all of it flows on '
                'through $R_f$, swinging back and forth with the input. To push it through, the output must sit '
                'at $-v_{in} R_f/R_{in}$: twice the input, upside down.'),
            eq(r'v_{out} = -\frac{R_f}{R_{in}}\,v_{in} \qquad Z_{in} = R_{in}', 'Inverting amplifier'),
            p('The input impedance is just $R_{in}$, since the far end of $R_{in}$ sits at 0 V.'),
        ]),
        ('noninverting', 'The non-inverting amplifier and the follower', [
            fig(non_inverting(), 'Left: the output is divided by $R_f$ and $R_g$ and fed back, so the output must '
                'be larger than the input by the inverse of that division. Right: with all of the output fed '
                'back, the output simply copies the input.'),
            eq(r'v_{out} = \left(1 + \frac{R_f}{R_g}\right) v_{in}', 'Non-inverting amplifier'),
            p('Its input draws no current, so a non-inverting stage can read a weak source, a divider or a sensor '
              'without loading it. The follower, gain 1, does nothing else: it is a buffer.'),
        ]),
        ('arithmetic', 'Sums and differences', [
            fig(arithmetic(), 'Left: each input sends its own current into the virtual ground, and $R_f$ '
                'carries their sum. Right: a matched pair of dividers subtracts one input from the other.'),
            eq(r'v_{out} = -R_f\left(\frac{v_1}{R_1} + \frac{v_2}{R_2} + \frac{v_3}{R_3}\right)',
               'Summing amplifier'),
            eq(r'v_{out} = \frac{R_2}{R_1}\,(v_2 - v_1)', 'Difference amplifier'),
            p('With inputs from four logic pins through $R$, $2R$, $4R$ and $8R$, the summing amplifier is a '
              '4-bit digital-to-analog converter. The difference amplifier measures current through a small '
              'shunt resistor that sits above ground; its accuracy depends on matched resistor pairs.'),
        ]),
        ('integrator', 'Integrators and differentiators', [
            fig(integrator(), 'A capacitor in place of $R_f$. A steady input drives a steady current '
                '$v_{in}/R$ into the capacitor, so the output ramps at a steady rate; when the input flips, the '
                'ramp turns round.'),
            eq(r'v_{out}(t) = -\frac{1}{RC}\int_0^t v_{in}\,dt', 'Integrator'),
            p('Swap R and C to differentiate. Real integrators drift on their own offset, so a large resistor '
              'across C limits the DC gain; real differentiators amplify noise, so a small resistor in series '
              'with C limits the high-frequency gain.'),
            eq(r'v_{out} = -RC\,\frac{dv_{in}}{dt}', 'Differentiator'),
        ]),
        ('active-filters', 'Active filters', [
            p('A capacitor across $R_f$ of an inverting amplifier makes a low-pass filter with gain, its output '
              'stiff for any load:'),
            eq(r'H(j\omega) = -\frac{R_f}{R_{in}}\,\frac{1}{1 + j\omega R_f C_f} \qquad f_c = \frac{1}{2\pi R_f C_f}',
               'Active low-pass filter'),
            p('Two resistors and two capacitors around a follower give a second-order filter that falls 40 dB '
              'per decade, twice as steep:'),
            fig(sallen_key(), 'The Sallen–Key low-pass. $C_1$ feeds the output back to the middle node, '
                'sharpening the corner.'),
            eq(r'f_c = \frac{1}{2\pi\sqrt{R_1 R_2 C_1 C_2}} \qquad Q = \frac{\sqrt{R_1 R_2 C_1 C_2}}{C_2\,(R_1 + R_2)}',
               'Sallen–Key low-pass'),
            p('With equal resistors $Q = \\tfrac{1}{2}\\sqrt{C_1/C_2}$, so the maximally flat Butterworth response, '
              '$Q = 1/\\sqrt{2}$, takes $C_1 = 2C_2$. A filter like this in front of an ADC removes frequencies '
              'above half the sampling rate, which would otherwise alias.'),
        ]),
        ('comparators', 'Comparators and the Schmitt trigger', [
            p('Without feedback the output says which input is higher. Dedicated comparators such as the LM393 '
              'switch faster than op-amps and have open-collector outputs: add a pull-up to the logic supply.'),
            fig(comparators(), 'The same noisy signal into a plain comparator and a Schmitt trigger. Near each '
                'crossing the noise carries the input back and forth over the threshold, and the comparator '
                'chatters. The Schmitt trigger switches up only above $+V_T$ and down only below $-V_T$, once '
                'each way.'),
            p('Positive feedback makes the Schmitt trigger: once the output switches, it pulls the threshold the '
              'other way, so the input must travel back past a second threshold before it switches again.'),
            fig(hysteresis(), 'A non-inverting Schmitt trigger: $R_2$ feeds the output back to the + input. Its '
                'transfer curve is a loop; the ring follows the output as the input sweeps up and down.'),
            eq(r'V_T = \pm\frac{R_1}{R_2}\,V_{sat}', 'Schmitt trigger thresholds',
               r'non-inverting, with the − input at 0 V'),
            p('On a single supply, take the − input to a reference such as half the supply instead of ground. '
              'The 74HC14 is six Schmitt-trigger inverters, and most microcontroller inputs have a little '
              'hysteresis built in.'),
        ]),
        ('real', 'Real op-amps', [
            p('Gain falls with frequency. Above a corner of a few hertz, the open-loop gain of most op-amps '
              'drops 20 dB per decade to 1 at the transition frequency $f_T$, so gain times bandwidth is '
              'constant: an op-amp with a 1 MHz gain-bandwidth product gives 100 kHz at a gain of 10. The output '
              'can also only change so fast, its slew rate, which limits large fast signals:'),
            eq(r'A_{cl} \cdot f_{-3\,\mathrm{dB}} \approx \mathrm{GBW} = f_T', 'Gain-bandwidth product'),
            eq(r'f_{max} = \frac{SR}{2\pi V_p}', 'Slew rate and full-power bandwidth'),
            fig(limits(), 'Left: open-loop gain, solid, and the response at a closed-loop gain of 10, dashed; '
                'the bandwidth ends where the two meet. Right: a sine that asks for a faster change than the '
                'slew rate allows comes out as a smaller triangle.'),
            table(['Limit', 'Typical', 'Effect'],
                  ['input offset voltage', '0.1 to 5 mV', 'multiplied by the gain, it shifts the output'],
                  ['input bias current', 'pA (CMOS, JFET) to nA (bipolar)', 'a voltage drop across the source '
                   'resistance'],
                  ['output swing', 'rail to rail, or 1 to 2 V short of each rail', 'clipping'],
                  ['input common-mode range', 'may exclude the top rail', 'wrong output near that rail'],
                  ['gain-bandwidth product', '1 to 100 MHz', 'bandwidth at a given gain'],
                  ['slew rate', '0.3 to 20 V/µs', 'large fast signals turn into triangles'], wide=True),
            table(['Part', 'Supply', 'GBW, slew rate', 'Notes'],
                  ['LM358', '3 to 32 V single', '0.7 MHz, 0.3 V/µs', 'inputs include ground; output stops '
                   '1.5 V below the top rail'],
                  ['MCP6002', '1.8 to 6 V', '1 MHz, 0.6 V/µs', 'rail-to-rail inputs and output: good for 3.3 V '
                   'boards'],
                  ['TL072', '±5 to ±15 V', '3 MHz, 13 V/µs', 'JFET inputs, tiny bias current; not rail to rail'],
                  ['NE5532', '±3 to ±20 V', '10 MHz, 9 V/µs', 'low-noise audio'],
                  ['LM393', '2 to 36 V', 'comparator', 'open-collector outputs need pull-ups'], wide=True),
        ]),
        ('sensors', 'Reading sensors', [
            p('A photodiode gives a current proportional to light. A transimpedance amplifier holds the diode at '
              '0 V and turns its current into a voltage:'),
            fig(photodiode(), 'The photocurrent cannot enter the − input, so the output pushes it through $R_f$. '
                '$C_f$ across $R_f$ sets the bandwidth and keeps the loop stable.'),
            eq(r'v_{out} = I_p\,R_f', 'Transimpedance amplifier'),
            p('A load cell or bridge sensor gives millivolts riding on half the supply. An instrumentation '
              'amplifier, three op-amps in one package, amplifies only the difference, with the gain set by one '
              'resistor $R_G$:'),
            eq(r'G = 1 + \frac{49.4\,\mathrm{k\Omega}}{R_G}', 'Instrumentation amplifier gain',
               r'AD620; the INA128 uses 50 kΩ'),
            note('Read more: MIT 6.002 lectures 19 to 21 (the op-amp abstraction, op-amp circuits, positive '
                 'feedback) and the operational amplifier chapter of <em>Lessons in Electric Circuits III: '
                 'Semiconductors</em>, in DOCS → CIRCUITS LIBRARY.'),
        ]),
    ]
