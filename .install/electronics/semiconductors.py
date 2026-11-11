import math
import random

from draw import (Figure, Plot, begin, bjt, circle, dot, end, flow, flow_by, ground, line, mosfet, num, phases,
                  poly, rail, rect, sweep, terminal, text, two, wire)
from page import eq, fig, note, p, table

NAME = '04-semiconductors'
TITLE = 'Diodes and transistors'
LEDE = ('How a PN junction conducts one way; diodes in rectifiers, references and protection; bipolar and MOS '
        'transistors as switches and amplifiers; the CMOS inverter inside every logic chip; and the H-bridge '
        'that drives a motor both ways.')


def holes(f, points, period):
    """Moving rings: holes, the missing electrons that carry current in P-type silicon."""
    d = poly(points)
    style = f' style="--t:{num(period)}s"'
    f.add(f'<path class="flow-halo" d="{d}"{style}/>', f'<path class="flow hole" d="{d}"{style}/>',
          f'<path class="flow hole-in" d="{d}"{style}/>')


def junction():
    f = Figure(900, 270, 'A PN junction, forward and reverse biased')
    rect(f, 150, 40, 600, 120)
    line(f, 450, 40, 450, 160, 'w thin faint')
    text(f, 300, 184, 'P: holes', 'middle', 't s')
    text(f, 600, 184, 'N: free electrons', 'middle', 't s')
    wire(f, (150, 100), (110, 100), (110, 230), (400, 230))
    wire(f, (500, 230), (790, 230), (790, 100), (750, 100))
    forward, reverse = phases(f, 2, 10)
    begin(f, forward)
    f.add('<rect class="shade2" x="436" y="41" width="28" height="118"/>')
    for y in (62, 86, 110, 134):
        holes(f, [(156, y), (462, y)], 1.4)
        flow(f, [(744, y), (438, y)], 1.4)
    two(f, 'B', (400, 230), (500, 230))
    for points in ([(400, 230), (110, 230), (110, 100), (150, 100)], [(750, 100), (790, 100), (790, 230), (500, 230)]):
        flow(f, points, 1.4)
    text(f, 450, 260, 'forward bias: the junction narrows and current flows', 'middle', 't s')
    end(f)
    begin(f, reverse)
    f.add('<rect class="shade2" x="380" y="41" width="140" height="118"/>')
    scatter = random.Random(1)
    for x0, x1, cls in ((160, 372, 'hole'), (528, 740, 'electron')):
        for _ in range(26):
            x, y = scatter.uniform(x0, x1), scatter.uniform(50, 150)
            if cls == 'hole':
                circle(f, x, y, 3.2, 'w thin hollow')
            else:
                dot(f, x, y, 3)
    two(f, 'B', (500, 230), (400, 230))
    text(f, 450, 260, 'reverse bias: the depletion region widens; almost no current', 'middle', 't s')
    end(f)
    text(f, 450, 30, 'depletion region', 'middle', 't s')
    return f


def diode_current(v):
    """Milliamperes through a silicon diode with a 5.1 V Zener breakdown."""
    forward = 1e3 * 4e-15 * (math.exp(min(v, 1) / 0.02585) - 1)
    breakdown = -0.1 * math.exp(25 * (-5.1 - v)) if v < -4.6 else 0
    return forward + breakdown


def diode_curve():
    f = Figure(640, 300, 'Current against voltage for a diode with a Zener breakdown')
    plot = Plot(f, 60, 40, 480, 210, (-6, 1.2), (-20, 20))
    plot.axes('v (V)', 'i (mA)', [(v, str(v).replace('-', '−')) for v in (-6, -5, -4, -3, -2, -1, 1)],
              [(-20, '−20'), (-10, '−10'), (10, '10'), (20, '20')], grid=True, xzero=0, yzero=0)
    points = [(v / 1000, diode_current(v / 1000)) for v in range(-6000, 1201, 5)]
    plot.curve([(v, i) for v, i in points if -20 <= i <= 20])
    text(f, plot.X(-0.2), plot.Y(17), 'forward: conducts', 'end', 't s')
    text(f, plot.X(-0.2), plot.Y(17) + 15, 'above about 0.6 V →', 'end', 't s')
    text(f, plot.X(-2.6), plot.Y(3), 'reverse: blocks', 'middle', 't s')
    text(f, plot.X(-4.95), plot.Y(-15), 'breakdown at −V_Z', 'start', 't s')
    return f


def bridge():
    f = Figure(900, 290, 'A full-wave bridge rectifier through both half cycles')
    period = 4
    top, right, bottom, left = (250, 50), (330, 130), (250, 210), (170, 130)
    two(f, 'AC', (60, 100), (60, 160), 'v_in', side=-1)
    two(f, 'D', top, right, 'D1')
    two(f, 'D', bottom, right, 'D2', side=-1)
    two(f, 'D', left, top, 'D3')
    two(f, 'D', left, bottom, 'D4', side=-1)
    two(f, 'R', (440, 100), (440, 180), 'R_L', 'load')
    supply_top = [(60, 100), (60, 30), (250, 30), top]
    supply_bottom = [(60, 160), (60, 250), (250, 250), bottom]
    out = [right, (380, 130), (380, 70), (440, 70), (440, 100)]
    back = [(440, 180), (440, 270), (120, 270), (120, 130), left]
    for points in (supply_top, supply_bottom, out, back):
        wire(f, *points)
    for point in (top, right, bottom, left):
        dot(f, *point)
    rectified = lambda t: 30 * integral_abs_sine(t, period)
    flow_by(f, out, 'out', rectified, period)
    flow_by(f, back, 'back', rectified, period)
    positive, negative = phases(f, 2, period)
    begin(f, positive)
    half = lambda t: 30 * integral_abs_sine(min(t, period / 2), period)
    flow_by(f, supply_top, 'pa', half, period)
    flow_by(f, list(reversed(supply_bottom)), 'pb', half, period)
    text(f, 312, 76, 'on', 'start', 't s')
    text(f, 188, 196, 'on', 'end', 't s')
    end(f)
    begin(f, negative)
    later = lambda t: 30 * (integral_abs_sine(max(t, period / 2), period) - integral_abs_sine(period / 2, period))
    flow_by(f, supply_bottom, 'na', later, period)
    flow_by(f, list(reversed(supply_top)), 'nb', later, period)
    text(f, 312, 196, 'on', 'start', 't s')
    text(f, 188, 76, 'on', 'end', 't s')
    end(f)
    plot = Plot(f, 560, 50, 300, 170, (0, 1), (-1.15, 1.15))
    plot.axes('t', None, [(0.5, ''), (1, '')], [], yzero=0)
    plot.curve(lambda t: math.sin(2 * math.pi * t), 'w curve dash')
    plot.curve(lambda t: max(abs(math.sin(2 * math.pi * t)) - 0.14, 0))
    text(f, plot.X(0.25), plot.Y(1.05) - 4, 'v_in', 'middle', 't s')
    text(f, plot.X(0.75), plot.Y(0.86) - 6, 'v_out', 'middle', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(1), plot.y, plot.y + plot.h, period)
    return f


def integral_abs_sine(t, period):
    """The integral of |sin(2πs/T)| from 0 to t, in seconds."""
    whole, part = divmod(t, period / 2)
    each = period / math.pi
    return whole * each + (1 - math.cos(2 * math.pi * part / period)) * period / (2 * math.pi)


def ripple():
    f = Figure(600, 280, 'A rectified sine smoothed by a capacitor')
    plot = Plot(f, 70, 40, 420, 180, (0, 3.4), (0, 1.1))
    plot.axes('t (cycles)', None, [(k, str(k)) for k in range(4)], [(0, '0'), (1, 'V_p')], grid=True)
    plot.curve(plot.points(lambda t: abs(math.sin(2 * math.pi * t)), 0, 3), 'w curve dash')
    held, out, rc, step = 0.0, [], 3.0, 0.002
    for k in range(1501):
        t = k * step
        held = max(abs(math.sin(2 * math.pi * t)), held * math.exp(-step / rc))
        out.append((t, held))
    plot.curve(out)
    low = min(v for t, v in out if t > 1)
    for level in (1, low):
        line(f, plot.X(2.6), plot.Y(level), plot.X(3.18), plot.Y(level), 'w thin dots')
    line(f, plot.X(3.12), plot.Y(1), plot.X(3.12), plot.Y(low), 'w thin')
    text(f, plot.X(3.17), plot.Y((1 + low) / 2) + 4, 'ΔV', 'start', 't s')
    return f


def bjt_curves():
    f = Figure(640, 300, 'Collector current against collector-emitter voltage for five base currents')
    plot = Plot(f, 70, 40, 440, 200, (0, 10), (0, 12))
    plot.axes('v_CE (V)', 'i_C (mA)', [(v, str(v)) for v in range(0, 11, 2)], [(i, str(i)) for i in range(0, 13, 2)],
              grid=True)
    f.add(f'<rect class="shade" x="{num(plot.X(0))}" y="{num(plot.y)}" width="{num(plot.X(0.3) - plot.X(0))}" '
          f'height="{num(plot.h)}"/>')
    for base in (20, 40, 60, 80, 100):
        top = 0.1 * base
        plot.curve(lambda v: top * (1 - math.exp(-v / 0.12)) * (1 + v / 60))
        text(f, plot.X(10) + 6, plot.Y(top * (1 + 10 / 60)) + 4, f'i_B = {base} µA', 'start', 't s')
    text(f, plot.X(0.45), plot.Y(11.4), '← saturation', 'start', 't s')
    text(f, plot.X(5), plot.Y(11.4), 'active: i_C = β i_B', 'middle', 't s')
    text(f, plot.X(5), plot.Y(0.6), 'cutoff', 'middle', 't s')
    return f


def led_switch():
    f = Figure(640, 300, 'An NPN transistor switching an LED from a logic pin')
    rail(f, 300, 50, '+5 V')
    two(f, 'R', (300, 50), (300, 110), 'R_C', '150 Ω')
    two(f, 'LED', (300, 124), (300, 172), 'D1', side=-1)
    wire(f, (300, 110), (300, 124))
    pins = bjt(f, 292, 210, label='Q1')
    wire(f, (300, 172), pins['C'])
    wire(f, pins['E'], (300, 254))
    ground(f, 300, 254)
    two(f, 'R', (170, 210), (250, 210), 'R_B', '1 kΩ')
    wire(f, (150, 210), (170, 210))
    wire(f, (250, 210), pins['B'])
    terminal(f, 150, 210)
    text(f, 140, 214, 'GPIO', 'end', 't s')
    off, on = phases(f, 2, 8)
    begin(f, off)
    text(f, 470, 120, 'GPIO at 0 V:', 'start', 't s')
    text(f, 470, 136, 'no base current,', 'start', 't s')
    text(f, 470, 152, 'Q1 off, LED dark', 'start', 't s')
    end(f)
    begin(f, on)
    for points in ([(150, 210), (170, 210)], [(250, 210), (270, 210)]):
        flow(f, points, 3)
    for points in ([(300, 40), (300, 50)], [(300, 110), (300, 124)], [(300, 172), (300, 186)]):
        flow(f, points, 0.4)
    flow(f, [(300, 234), (300, 254)], 0.35)
    for x1, y1, x2, y2 in ((324, 140, 344, 132), (328, 152, 350, 152), (324, 164, 344, 172)):
        line(f, x1, y1, x2, y2, 'w thin')
    text(f, 470, 120, 'GPIO at 3.3 V:', 'start', 't s')
    text(f, 470, 136, 'base 2.6 mA,', 'start', 't s')
    text(f, 470, 152, 'collector 20 mA,', 'start', 't s')
    text(f, 470, 168, 'Q1 saturated, LED lit', 'start', 't s')
    end(f)
    return f


def mosfet_curves():
    f = Figure(640, 300, 'Drain current against drain-source voltage for four gate voltages')
    plot = Plot(f, 70, 40, 440, 200, (0, 5), (0, 70))
    plot.axes('v_DS (V)', 'i_D (mA)', [(v, str(v)) for v in range(6)], [(i, str(i)) for i in range(0, 71, 10)],
              grid=True)
    k, threshold = 20, 2
    for gate in (3, 3.5, 4, 4.5):
        over = gate - threshold
        plot.curve(lambda v: k * (over * v - v * v / 2) if v < over else k / 2 * over * over)
        text(f, plot.X(5) + 6, plot.Y(k / 2 * over * over) + 4, f'v_GS = {gate:g} V', 'start', 't s')
    plot.curve(lambda v: k / 2 * v * v, 'w thin dash')
    text(f, plot.X(0.75), plot.Y(56), 'triode', 'middle', 't s')
    text(f, plot.X(3.7), plot.Y(51), 'saturation', 'middle', 't s')
    return f


def motor_switch():
    f = Figure(640, 290, 'An N-channel MOSFET switching a motor')
    rail(f, 300, 50, '+12 V')
    two(f, 'M', (300, 70), (300, 140), 'M1', side=-1)
    two(f, 'D', (380, 140), (380, 70), 'D1')
    wire(f, (300, 50), (300, 70))
    wire(f, (300, 60), (380, 60), (380, 70))
    wire(f, (380, 140), (380, 150), (300, 150))
    wire(f, (300, 140), (300, 166))
    dot(f, 300, 60)
    dot(f, 300, 150)
    pins = mosfet(f, 292, 190, label='Q1')
    wire(f, (300, 214), (300, 250))
    ground(f, 300, 250)
    two(f, 'R', (180, 198), (250, 198), 'R_G', '100 Ω')
    wire(f, (250, 198), pins['G'])
    wire(f, (150, 198), (180, 198))
    terminal(f, 150, 198)
    text(f, 140, 202, 'GPIO', 'end', 't s')
    wire(f, (260, 198), (260, 210))
    two(f, 'R', (260, 210), (260, 250), 'R_PD', '100 kΩ', side=-1)
    wire(f, (260, 250), (300, 250))
    dot(f, 260, 198)
    dot(f, 300, 250)
    text(f, 430, 110, 'D1: flyback path', 'start', 't s')
    text(f, 430, 190, 'R_G slows the gate edge', 'start', 't s')
    text(f, 430, 206, 'R_PD holds Q1 off while', 'start', 't s')
    text(f, 430, 222, 'the GPIO floats at reset', 'start', 't s')
    return f


def inverter():
    f = Figure(900, 290, 'A CMOS inverter in both states, and its transfer curve')
    rail(f, 200, 50, 'V_DD')
    upper = mosfet(f, 192, 82, p=True)
    lower = mosfet(f, 192, 198, label=None)
    wire(f, (200, 50), upper['S'])
    wire(f, upper['D'], lower['D'])
    wire(f, (200, 140), (290, 140))
    dot(f, 200, 140)
    terminal(f, 290, 140)
    wire(f, lower['S'], (200, 236))
    ground(f, 200, 236)
    wire(f, upper['G'], (140, 74), (140, 206), lower['G'])
    wire(f, (90, 140), (140, 140))
    dot(f, 140, 140)
    terminal(f, 90, 140)
    text(f, 90, 124, 'in', 'middle', 't s')
    text(f, 290, 124, 'out', 'middle', 't s')
    low, high = phases(f, 2, 6)
    for cls, value, result, top, bottom in ((low, '0', '1', 'on', 'off'), (high, '1', '0', 'off', 'on')):
        begin(f, cls)
        text(f, 74, 145, value, 'end', 't b')
        text(f, 306, 145, result, 'start', 't b')
        text(f, 230, 86, f'P: {top}', 'start', 't s')
        text(f, 230, 202, f'N: {bottom}', 'start', 't s')
        if top == 'on':
            flow(f, [(200, 40), (200, 58)], 1)
            flow(f, [(200, 106), (200, 140), (290, 140)], 1)
        else:
            flow(f, [(290, 140), (200, 140), (200, 174)], 1)
            flow(f, [(200, 222), (200, 236)], 1)
        end(f)
    plot = Plot(f, 520, 40, 300, 200, (0, 3.3), (0, 3.3))
    plot.axes('v_in (V)', 'v_out (V)', [(0, '0'), (1.65, '1.65'), (3.3, '3.3')], [(0, '0'), (1.65, '1.65'),
              (3.3, '3.3')], grid=True)
    plot.curve(lambda v: 3.3 / (1 + math.exp((v - 1.65) / 0.09)))
    plot.mark(0.2, 3.3, 'in 0 → out 1', 'start', 8, 16)
    plot.mark(3.1, 0, 'in 1 → out 0', 'end', -8, -8)
    return f


def hbridge():
    f = Figure(900, 300, 'An H-bridge driving a motor forwards, then in reverse')
    two(f, 'B2', (60, 110), (60, 190), 'BT1', side=-1)
    wire(f, (60, 110), (60, 40), (450, 40))
    wire(f, (60, 190), (60, 260), (450, 260))
    for x in (150, 450):
        wire(f, (x, 40), (x, 60))
        wire(f, (x, 120), (x, 180))
        wire(f, (x, 240), (x, 260))
        dot(f, x, 40)
        dot(f, x, 260)
        dot(f, x, 150)
    two(f, 'M', (230, 150), (370, 150), 'M1')
    wire(f, (150, 150), (230, 150))
    wire(f, (370, 150), (450, 150))
    forward, backward = phases(f, 2, 8)
    closed = {forward: ('S1', 'S4'), backward: ('S2', 'S3')}
    switches = {'S1': ((150, 60), (150, 120)), 'S2': ((450, 60), (450, 120)), 'S3': ((150, 180), (150, 240)),
                'S4': ((450, 180), (450, 240))}
    for cls in (forward, backward):
        begin(f, cls)
        for name, (a, b) in switches.items():
            two(f, 'SWon' if name in closed[cls] else 'SW', a, b, name, side=1 if a[0] > 300 else -1)
        if cls == forward:
            paths = ([(60, 110), (60, 40), (150, 40), (150, 60)], [(150, 120), (150, 150), (230, 150)],
                     [(370, 150), (450, 150), (450, 180)], [(450, 240), (450, 260), (60, 260), (60, 190)])
            text(f, 300, 112, '→ forward', 'middle', 't s')
        else:
            paths = ([(60, 110), (60, 40), (450, 40), (450, 60)], [(450, 120), (450, 150), (370, 150)],
                     [(230, 150), (150, 150), (150, 180)], [(150, 240), (150, 260), (60, 260), (60, 190)])
            text(f, 300, 112, 'reverse ←', 'middle', 't s')
        for points in paths:
            flow(f, points, 0.8)
        end(f)
    text(f, 560, 120, 'S1 + S4: current left to right', 'start', 't s')
    text(f, 560, 140, 'S2 + S3: right to left', 'start', 't s')
    text(f, 560, 172, 'never S1 + S3 or S2 + S4:', 'start', 't s')
    text(f, 560, 188, 'that shorts the supply', 'start', 't s')
    return f


def sections():
    return [
        ('junction', 'The PN junction', [
            p('Pure silicon barely conducts. Doping it with a few phosphorus atoms leaves free electrons (N-type); '
              'boron leaves <em>holes</em>, missing electrons that move like positive charges (P-type). Where the '
              'two meet, carriers cross and cancel, leaving a thin depletion region with no free carriers and a '
              'built-in barrier of about 0.7 V.'),
            fig(junction(), 'Forward bias, P positive, pushes holes and electrons into the junction, which '
                'narrows until current flows. Reverse bias pulls them away and the junction widens: only a '
                'tiny leakage remains. Inside the silicon, rings are holes and dots are electrons, each moving '
                'its own way; in the wires, as everywhere in this guide, dots show conventional current.'),
        ]),
        ('diodes', 'Diodes', [
            p('The current grows exponentially with forward voltage. In the Shockley equation $I_S$ is a tiny '
              'saturation current, $n$ between 1 and 2, and $V_T$ the thermal voltage, about 26 mV at room '
              'temperature:'),
            eq(r'I = I_S\left(e^{V/(n V_T)} - 1\right) \qquad V_T = \frac{kT}{q}', 'Diode equation'),
            fig(diode_curve(), 'Almost nothing flows until about 0.6 V; then every 60 mV more gives ten times '
                'the current, so silicon diodes sit near 0.6 to 0.7 V. In reverse a diode blocks, until a Zener '
                'breaks down at its rated voltage and holds it.'),
            table(['Model', 'Use it for'],
                  ['ideal: a wire forward, open reverse', 'which way current goes'],
                  ['constant drop: 0.7 V forward (LED: its $V_F$)', 'most circuit calculations'],
                  ['drop plus a series resistance', 'large currents'],
                  ['the exponential', 'small signals, temperature, log amplifiers'], wide=True),
            p('The forward voltage falls about 2 mV for each degree of warming, which makes a diode a cheap '
              'thermometer. An LED needs its current set; with a supply $V_S$:'),
            eq(r'R = \frac{V_S - V_F}{I_F}', 'LED resistor', r'5 V, a red LED at 2 V and 10 mA: $R = 300\,\Omega$'),
            p('Diodes also protect: in series against a reversed battery, across a relay coil against flyback, '
              'and from a pin to each rail against static discharge.'),
        ]),
        ('rectifiers', 'Rectifiers', [
            p('A bridge of four diodes turns AC into DC by steering both halves of the cycle through the load '
              'the same way.'),
            fig(bridge(), 'On the positive half cycle D1 and D4 conduct; on the negative half D2 and D3. The '
                'current through the load never reverses. The output is the size of the input less two diode '
                'drops.'),
            p('A capacitor across the load fills at each peak and supplies the load between peaks, leaving a '
              'ripple that falls as the capacitor grows. For a full-wave rectifier at mains frequency $f$, '
              'with load current $I$:'),
            eq(r'\Delta V \approx \frac{I}{2 f C}', 'Rectifier ripple'),
            fig(ripple(), 'Dashed: the rectified sine. Solid: across the capacitor, recharged at each peak and '
                'sagging between them.'),
        ]),
        ('bjt', 'Bipolar transistors', [
            p('In an NPN transistor a small current into the base lets a current $\\beta$ times larger, '
              'typically 100 to 300, flow from collector to emitter. The base-emitter junction is a diode, so '
              'it sits near 0.65 V when on.'),
            eq(r'i_C = \beta\, i_B \qquad i_E = i_C + i_B \qquad v_{BE} \approx 0.65\,\mathrm{V}', 'BJT'),
            fig(bjt_curves(), 'In the active region the collector current follows the base current, nearly '
                'independent of $v_{CE}$; that is how it amplifies. Squeezed against the left edge it saturates: '
                'fully on, with only 0.1 to 0.2 V across it.'),
            p('As a switch, drive it into saturation with more base current than $I_C/\\beta$ needs; aim for a '
              'forced gain of 10 to 20.'),
            fig(led_switch(), r'Base resistor: $(3.3 - 0.7)\,\mathrm{V} / 1\,\mathrm{k\Omega} = 2.6\,\mathrm{mA}$, '
                r'well over the 0.2 mA that 20 mA needs at $\beta = 100$. Collector: $(5 - 2 - 0.1)\,\mathrm{V} / '
                r'150\,\Omega \approx 20\,\mathrm{mA}$.'),
            eq(r'R_B = \frac{V_{in} - 0.7\,\mathrm{V}}{I_B} \qquad I_B \ge \frac{I_C}{10}', 'Saturated BJT switch'),
            p('As an amplifier the collector current depends exponentially on $v_{BE}$. Its transconductance, '
              'the change of collector current per volt at the base, sets the gain of a common-emitter stage '
              'with collector resistor $R_C$:'),
            eq(r'g_m = \frac{I_C}{V_T} \qquad A_v \approx -g_m R_C', 'BJT gain'),
        ]),
        ('mosfet', 'MOSFETs', [
            p('A MOSFET\'s gate is insulated: it draws no steady current, only a burst to charge its '
              'capacitance. Above the threshold $V_{th}$ the gate voltage opens a channel from drain to source. '
              'With a little drain-source voltage the channel acts as a resistor (the triode region); with more, '
              'the current saturates:'),
            eq(r'i_D = k\left[(v_{GS} - V_{th})\,v_{DS} - \tfrac{1}{2} v_{DS}^2\right] \qquad v_{DS} < v_{GS} - '
               r'V_{th}', 'MOSFET, triode region'),
            eq(r'i_D = \frac{k}{2}\,(v_{GS} - V_{th})^2 \qquad v_{DS} \ge v_{GS} - V_{th}', 'MOSFET, saturation'),
            fig(mosfet_curves(), 'The dashed parabola divides the two regions. A switch works at the far left, '
                'where the transistor is a small resistance $R_{DS(on)}$.'),
            p('Fully on, a MOSFET dissipates $I^2 R_{DS(on)}$. Pick a <em>logic-level</em> part whose '
              '$R_{DS(on)}$ is specified at your gate voltage, 2.5 or 4.5 V; its threshold is only where it '
              'begins to turn on.'),
            eq(r'P = I^2 R_{DS(on)}', 'MOSFET switch loss'),
            fig(motor_switch(), 'A low-side switch: the MOSFET connects the motor\'s lower end to ground. A '
                'P-channel MOSFET does the same from the supply side, on when its gate is pulled below its '
                'source.'),
            p('Every power MOSFET has a body diode from source to drain, drawn or not, so it blocks only one '
              'direction.'),
        ]),
        ('cmos', 'The CMOS inverter', [
            p('Logic chips are built from complementary pairs: a P-channel transistor to the supply and an '
              'N-channel to ground, with their gates joined. One is always off, so no current flows except '
              'while switching.'),
            fig(inverter(), 'Input low: the P transistor is on and pulls the output to $V_{DD}$. Input high: the '
                'N transistor pulls it to ground. Moving dots show the output charging and discharging the '
                'next gate. The transfer curve is steep, so small noise on the input is not passed on.'),
            p('Each switch charges the load capacitance $C$ of the wiring and the next gates, so a CMOS chip\'s '
              'power grows with its clock frequency and the square of its supply voltage, the reason chips run '
              'at low voltages:'),
            eq(r'P = \alpha\, C\, V_{DD}^2\, f', 'CMOS switching power', r'$\alpha$: the fraction of nodes '
               'switching each cycle'),
        ]),
        ('hbridge', 'The H-bridge', [
            p('Four switches around a motor let current go through it either way, so it can turn both ways. '
              'In practice the switches are MOSFETs, often in one driver chip with the protection built in.'),
            fig(hbridge(), 'Closing S1 and S4 drives the motor one way; S2 and S3 the other. Pulsing the '
                'switches with PWM sets the speed.'),
            table(['Part', 'Kind', 'Typical use'],
                  ['1N4148', 'small-signal diode', 'signals, protection, logic'],
                  ['1N4001 to 1N4007', '1 A rectifier, 50 to 1000 V', 'power supplies, reverse polarity'],
                  ['1N5817 to 1N5819', '1 A Schottky, 20 to 40 V', 'low-loss power paths, flyback'],
                  ['2N3904, 2N3906', 'NPN and PNP, up to 200 mA', 'small switches and amplifiers'],
                  ['BSS138', 'N-MOSFET, 50 V, small', 'logic level shifting'],
                  ['AO3400, AO3401', 'N and P MOSFETs, 30 V, a few amperes', 'LED strips, small motors, '
                   'power switching'],
                  ['IRLZ44N', 'logic-level N-MOSFET, 55 V, tens of amperes', 'motors and heaters'], wide=True),
            note('Read more: MIT 6.002 lectures 4 to 10 (the digital gate, MOSFETs, amplifiers) and <em>Lessons '
                 'in Electric Circuits III: Semiconductors</em>, in DOCS → CIRCUITS LIBRARY.'),
        ]),
    ]
