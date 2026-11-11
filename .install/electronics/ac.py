import math

from draw import (Figure, Plot, arrow, begin, bjt, circle, dot, end, flow, flow_by, ground, keyframes, line, poly,
                  phases, rail, sampled, sweep, terminal, text, travel, two, wire)
from page import eq, fig, note, p, table

NAME = '03-ac'
TITLE = 'Capacitors, inductors and AC'
LEDE = ('Parts that store energy and the time they take to fill and empty; sine waves, phasors and impedance; '
        'filters and their Bode plots; resonance and AC power.')


def sign(kind, x, y):
    """A small + or − drawn as paths."""
    bar = f'M {x - 3.5} {y} H {x + 3.5}'
    return f'<path class="w thin" d="{bar}{f" M {x} {y - 3.5} V {y + 3.5}" if kind == "+" else ""}"/>'


def integral(fn, t, step=0.01):
    """The integral of fn from 0 to t by the midpoint rule."""
    n = max(1, round(t / step))
    h = t / n
    return sum(fn((k + 0.5) * h) for k in range(n)) * h


FULL = 1 - math.exp(-5)


def charge(t):
    """Charge as a fraction of full over a 10 s cycle: τ = 1 s, charging for 5τ, then discharging."""
    return 1 - math.exp(-t) if t <= 5 else FULL * math.exp(-(t - 5))


def charging():
    f = Figure(900, 280, 'A capacitor charging through a resistor, then discharging')
    two(f, 'V', (60, 110), (60, 170), 'V', '5 V', side=-1)
    two(f, 'R', (220, 50), (300, 50), 'R', '10 kΩ')
    two(f, 'C', (360, 100), (360, 160), 'C', '100 µF')
    wire(f, (60, 110), (60, 50), (140, 50))
    wire(f, (180, 50), (220, 50))
    wire(f, (300, 50), (360, 50), (360, 100))
    wire(f, (360, 160), (360, 210), (60, 210), (60, 170))
    wire(f, (140, 80), (140, 210))
    dot(f, 140, 210)
    distance = 80
    flow_by(f, [(180, 50), (220, 50)], 'qa', lambda t: distance * charge(t), 10)
    flow_by(f, [(300, 50), (360, 50), (360, 100)], 'qb', lambda t: distance * charge(t), 10)
    flow_by(f, [(360, 160), (360, 210), (140, 210)], 'qc', lambda t: distance * charge(t), 10)
    charged, discharged = phases(f, 2, 10)
    begin(f, charged)
    line(f, 180, 50, 140, 50)
    flow_by(f, [(60, 110), (60, 50), (140, 50)], 'qd', lambda t: distance * charge(min(t, 5)), 10)
    flow_by(f, [(140, 210), (60, 210), (60, 170)], 'qe', lambda t: distance * charge(min(t, 5)), 10)
    text(f, 210, 140, 'charging', 'middle', 't s')
    end(f)
    begin(f, discharged)
    line(f, 180, 50, 140, 80)
    flow_by(f, [(140, 80), (140, 210)], 'qf', lambda t: distance * (FULL - charge(max(t, 5))), 10)
    text(f, 250, 140, 'discharging', 'middle', 't s')
    end(f)
    for x, y in ((140, 50), (140, 80), (180, 50)):
        circle(f, x, y, 2.8, 'w hollow')
    text(f, 140, 38, '1', 'middle', 't s')
    text(f, 128, 84, '2', 'end', 't s')
    for k, (x, threshold) in enumerate(((349, 0.15), (371, 0.4), (355, 0.65), (365, 0.9))):
        on, off = -math.log(1 - threshold), 5 + math.log(FULL / threshold)
        shown = keyframes(f, f'm{k}', [(0, 'opacity:0'), (10 * on, 'opacity:1'), (10 * off, 'opacity:0')], 10,
                          'step-end', 'opacity:0')
        f.add(f'<g class="{shown}">{sign("+", x, 117)}{sign("-", x, 143)}</g>')
    plot = Plot(f, 520, 40, 320, 170, (0, 10), (0, 5))
    plot.axes('t', 'v_C (V)', [(k, {0: '0', 1: 'τ', 5: '5τ', 6: '6τ', 10: '10τ'}.get(k, '')) for k in range(11)],
              [(0, '0'), (5 * (1 - math.exp(-1)), '3.16'), (5 * FULL * math.exp(-1), '1.83'), (5, '5')],
              grid=True)
    samples = [(k / 20, 5 * charge(k / 20)) for k in range(201)]
    plot.curve(samples)
    line(f, plot.X(5), plot.Y(0), plot.X(5), plot.Y(5), 'w thin dash')
    text(f, plot.X(5) + 6, plot.Y(5) + 12, 'switch to 2', 'start', 't s')
    trace = travel(f, 'trace', [(plot.X(t), plot.Y(v)) for t, v in samples], 10, [t / 10 for t, _ in samples])
    f.add(f'<g class="{trace}"><circle class="walker" r="6"/></g>')
    return f


def coil_current(t):
    """Coil current as a fraction of its final value: on for 5 s, then off; L/R = 1 s."""
    return 1 - math.exp(-t) if t <= 5 else FULL * math.exp(-(t - 5))


def flyback():
    f = Figure(900, 300, 'A relay coil switched by a transistor, with its flyback diode')
    rail(f, 300, 50, '+12 V')
    two(f, 'L', (300, 75), (300, 135), 'K1', 'coil', side=-1)
    two(f, 'D', (390, 135), (390, 75), 'D1')
    wire(f, (300, 50), (300, 75))
    wire(f, (300, 135), (300, 166))
    wire(f, (300, 60), (390, 60), (390, 75))
    wire(f, (390, 135), (390, 150), (300, 150))
    dot(f, 300, 60)
    dot(f, 300, 150)
    pins = bjt(f, 292, 190, label='Q1')
    two(f, 'R', (190, 190), (250, 190), 'R_B', '1 kΩ')
    wire(f, (170, 190), (190, 190))
    wire(f, (250, 190), pins['B'])
    terminal(f, 170, 190)
    text(f, 160, 194, 'GPIO', 'end', 't s')
    wire(f, pins['E'], (300, 236))
    ground(f, 300, 236)
    speed = 36
    flowing = lambda t: speed * integral(coil_current, t)
    flow_by(f, [(300, 60), (300, 75)], 'ia', flowing, 10)
    flow_by(f, [(300, 135), (300, 150)], 'ib', flowing, 10)
    on, off = phases(f, 2, 10)
    begin(f, on)
    for k, points in enumerate(([(300, 50), (300, 60)], [(300, 150), (300, 166)], [(300, 214), (300, 236)])):
        flow_by(f, points, f'ic{k}', lambda t: speed * integral(coil_current, min(t, 5)), 10)
    flow(f, [(170, 190), (190, 190)], 3)
    flow(f, [(250, 190), (270, 190)], 3)
    text(f, 160, 120, 'Q1 on:', 'end', 't s')
    text(f, 160, 136, 'current rises', 'end', 't s')
    end(f)
    begin(f, off)
    since = lambda t: speed * (integral(coil_current, max(t, 5)) - integral(coil_current, 5))
    flow_by(f, [(300, 150), (390, 150), (390, 135)], 'id', since, 10)
    flow_by(f, [(390, 75), (390, 60), (300, 60)], 'ie', since, 10)
    text(f, 160, 120, 'Q1 off:', 'end', 't s')
    text(f, 160, 136, 'current circles', 'end', 't s')
    text(f, 160, 152, 'through D1', 'end', 't s')
    end(f)
    plot = Plot(f, 540, 50, 300, 160, (0, 10), (0, 1.1))
    plot.axes('t', 'i_L', [(0, '0'), (5, 'off'), (10, '')], [(0, '0'), (1, 'V/R')], grid=True)
    samples = [(k / 20, coil_current(k / 20)) for k in range(201)]
    plot.curve(samples)
    trace = travel(f, 'trace', [(plot.X(t), plot.Y(v)) for t, v in samples], 10, [t / 10 for t, _ in samples])
    f.add(f'<g class="{trace}"><circle class="walker" r="6"/></g>')
    return f


def phasor():
    f = Figure(900, 280, 'A rotating phasor and the sine wave it traces')
    cx, cy, a, x0, wave, period, width = 130, 135, 80, 260, 200, 4, 580
    circle(f, cx, cy, a, 'w thin dim')
    line(f, cx - a - 14, cy, x0 + width, cy, 'w thin faint')
    line(f, cx, cy - a - 14, cx, cy + a + 14, 'w thin faint')
    line(f, x0, cy - a, x0 + width, cy - a, 'w thin dash')
    line(f, x0, cy - a / math.sqrt(2), x0 + width, cy - a / math.sqrt(2), 'w thin dots')
    text(f, x0 + width + 6, cy - a + 4, 'V_p', 'start', 't s')
    text(f, x0 + width + 6, cy - a / math.sqrt(2) + 4, 'V_rms', 'start', 't s')
    clip = f'{f.id}clip'
    f.add(f'<clipPath id="{clip}"><rect x="{x0}" y="0" width="{width}" height="280"/></clipPath>')
    points = [(x, cy + a * math.sin(2 * math.pi * (x - x0) / wave)) for x in range(x0 - wave, x0 + width + 1, 4)]
    scroll = keyframes(f, 'scroll', [(0, 'transform:translateX(0px)'), (100, f'transform:translateX({wave}px)')],
                       period)
    f.add(f'<g clip-path="url(#{clip})"><path class="w curve {scroll}" d="{poly(points)}"/></g>')
    height = sampled(f, 'height', lambda t: f'transform:translateY({-a * math.sin(2 * math.pi * t / period):.2f}px)',
                     period)
    f.add(f'<g class="{height}"><path class="w thin dash" d="M {cx - a} {cy} H {x0}"/>'
          f'<circle class="fill" cx="{x0}" cy="{cy}" r="4"/></g>')
    spin = keyframes(f, 'spin', [(0, 'transform:rotate(0deg)'), (100, 'transform:rotate(-360deg)')], period)
    f.add(f'<g transform="translate({cx} {cy})"><g class="{spin}"><path class="w bold" d="M 0 0 H {a - 9}"/>'
          f'<path class="fill" d="M {a} 0 L {a - 11} -5 L {a - 11} 5 Z"/></g></g>')
    dot(f, cx, cy, 3)
    arrow(f, x0 + wave / 2 - 10, cy + a + 26, x0, cy + a + 26, 'w thin', 6)
    arrow(f, x0 + wave / 2 + 10, cy + a + 26, x0 + wave, cy + a + 26, 'w thin', 6)
    text(f, x0 + wave / 2, cy + a + 30, 'T', 'middle', 't s')
    text(f, cx, cy + a + 30, 'ω = 2π f', 'middle', 't s')
    return f


def leads_and_lags():
    f = Figure(900, 230, 'Current and voltage in a capacitor and in an inductor')
    for ox, title, shift, name in ((40, 'capacitor: i leads v by 90°', math.pi / 2, 'leads'),
                                   (490, 'inductor: i lags v by 90°', -math.pi / 2, 'lags')):
        plot = Plot(f, ox, 50, 360, 140, (0, 4 * math.pi), (-1.2, 1.2))
        plot.axes('t', None, [], [], yzero=0)
        plot.curve(math.sin)
        plot.curve(lambda t: 0.75 * math.sin(t + shift), 'w curve dash')
        text(f, ox + 180, 24, title, 'middle', 't head')
        text(f, plot.X(math.pi / 2), plot.Y(1) - 6, 'v', 'middle')
        peak = math.pi / 2 - shift
        text(f, plot.X(peak + 2 * math.pi if peak < 0 else peak), plot.Y(0.75) - 6, 'i', 'middle')
    return f


def lowpass(f, ox=0, oy=0):
    two(f, 'AC', (ox + 60, oy + 110), (ox + 60, oy + 170), 'v_in', side=-1)
    wire(f, (ox + 60, oy + 110), (ox + 60, oy + 60), (ox + 100, oy + 60))
    two(f, 'R', (ox + 100, oy + 60), (ox + 180, oy + 60), 'R')
    wire(f, (ox + 180, oy + 60), (ox + 270, oy + 60))
    wire(f, (ox + 220, oy + 60), (ox + 220, oy + 100))
    two(f, 'C', (ox + 220, oy + 100), (ox + 220, oy + 160), 'C')
    wire(f, (ox + 220, oy + 160), (ox + 220, oy + 200))
    wire(f, (ox + 60, oy + 170), (ox + 60, oy + 200), (ox + 270, oy + 200))
    dot(f, ox + 220, oy + 60)
    dot(f, ox + 220, oy + 200)
    terminal(f, ox + 270, oy + 60)
    terminal(f, ox + 270, oy + 200)
    text(f, ox + 278, oy + 134, 'v_out', 'start')
    ground(f, ox + 140, oy + 200)


def bode():
    f = Figure(900, 340, 'An RC low-pass filter and its Bode plot')
    lowpass(f, 0, 20)
    mag = Plot(f, 440, 30, 390, 140, (0.01, 100), (-40, 5), xlog=True)
    decades = [(0.01, '0.01'), (0.1, '0.1'), (1, '1'), (10, '10'), (100, '100')]
    mag.axes(None, 'gain (dB)', [(x, '') for x, _ in decades], [(0, '0'), (-20, '−20'), (-40, '−40')], grid=True)
    mag.curve([(0.01, 0), (1, 0)], 'w thin dash')
    mag.curve([(1, 0), (100, -40)], 'w thin dash')
    mag.curve(lambda x: -10 * math.log10(1 + x * x))
    mag.mark(1, -3.01, '−3 dB at f_c', 'end', -8, 18)
    text(f, mag.X(12), mag.Y(-16), '−20 dB per decade', 'start', 't s')
    phase = Plot(f, 440, 210, 390, 90, (0.01, 100), (-90, 0), xlog=True)
    phase.axes('f / f_c', 'phase', decades, [(0, '0°'), (-45, '−45°'), (-90, '−90°')], grid=True)
    phase.curve(lambda x: -math.degrees(math.atan(x)))
    phase.mark(1, -45)
    return f


def filtering():
    f = Figure(900, 250, 'A low-pass filter passing a slow sine and shrinking a fast one')
    plot = Plot(f, 60, 60, 760, 150, (0, 2), (-1.2, 1.2))
    plot.axes(None, None, [], [(1, '1'), (-1, '−1')], yzero=0)
    text(f, 440, 236, 'two cycles of the input', 'middle', 't s')
    text(f, 840, 34, 'dashed: v_in   solid: v_out', 'end', 't s')
    frames = phases(f, 3, 12)
    for cls, ratio in zip(frames, (0.2, 1, 5)):
        gain, lag = 1 / math.sqrt(1 + ratio * ratio), math.atan(ratio)
        begin(f, cls)
        plot.curve(lambda x: math.sin(2 * math.pi * x), 'w curve dash')
        plot.curve(lambda x: gain * math.sin(2 * math.pi * x - lag))
        name = {0.2: 'f = f_c / 5', 1: 'f = f_c', 5: 'f = 5 f_c'}[ratio]
        text(f, 60, 34, f'{name}: output {100 * gain:.0f}% of input, {math.degrees(lag):.0f}° behind', 'start')
        end(f)
    return f


def second_order(zeta, t_end=14, step=0.002):
    """Unit-step response of x'' + 2ζx' + x = 1, by RK4, sampled every 0.05."""
    x, v, t, out = 0.0, 0.0, 0.0, [(0.0, 0.0)]

    def accel(x, v):
        return 1 - 2 * zeta * v - x
    while t < t_end - 1e-9:
        k1x, k1v = v, accel(x, v)
        k2x, k2v = v + step / 2 * k1v, accel(x + step / 2 * k1x, v + step / 2 * k1v)
        k3x, k3v = v + step / 2 * k2v, accel(x + step / 2 * k2x, v + step / 2 * k2v)
        k4x, k4v = v + step * k3v, accel(x + step * k3x, v + step * k3v)
        x += step / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
        v += step / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        t += step
        if round(t / step) % 25 == 0:
            out.append((t, x))
    return out


def step_responses():
    f = Figure(600, 290, 'Step responses of a second-order system')
    plot = Plot(f, 70, 40, 420, 190, (0, 14), (0, 1.6))
    plot.axes('ω_0 t', None, [(k, str(k)) for k in range(0, 15, 2)], [(0, '0'), (1, '1'), (1.5, '1.5')], grid=True)
    for row, (zeta, cls, style) in enumerate(((0.2, 'w curve', 'solid'), (1, 'w curve dash', 'dashed'),
                                              (3, 'w curve dots', 'dotted'))):
        plot.curve(second_order(zeta), cls)
        text(f, plot.X(8.4), plot.Y(0.5) + 15 * row, f'{style}: ζ = {zeta:g}', 'start', 't s')
    return f


def resonance():
    f = Figure(600, 290, 'Resonance of a series RLC circuit for three values of Q')
    plot = Plot(f, 70, 40, 420, 190, (0.1, 10), (0, 1.05), xlog=True)
    plot.axes('ω / ω_0', 'I / I_max', [(0.1, '0.1'), (1, '1'), (10, '10')], [(0, '0'), (0.707, '0.71'), (1, '1')],
              grid=True)
    for q, cls in ((1, 'w curve dots'), (3, 'w curve dash'), (10, 'w curve')):
        plot.curve(lambda x: 1 / math.sqrt(1 + q * q * (x - 1 / x) ** 2), cls)
    for row, words in enumerate(('solid: Q = 10', 'dashed: Q = 3', 'dotted: Q = 1')):
        text(f, plot.X(0.11), plot.Y(0.97) + 15 * row, words, 'start', 't s')
    return f


def tank():
    f = Figure(900, 270, 'Energy moving between a capacitor and an inductor')
    period = 4
    two(f, 'C', (120, 90), (120, 150), 'C', side=-1)
    two(f, 'L', (260, 80), (260, 160), 'L')
    upper, lower = [(120, 90), (120, 50), (260, 50), (260, 80)], [(260, 160), (260, 210), (120, 210), (120, 150)]
    wire(f, *upper)
    wire(f, *lower)
    swing = lambda t: 40 * (1 - math.cos(2 * math.pi * t / period))
    flow_by(f, upper, 'ua', swing, period)
    flow_by(f, lower, 'ub', swing, period)
    edge = math.acos(0.35) / (2 * math.pi)
    positive = keyframes(f, 'pos', [(0, 'opacity:1'), (100 * edge, 'opacity:0'), (100 * (1 - edge), 'opacity:1')],
                         period, 'step-end', 'opacity:1')
    negative = keyframes(f, 'neg', [(0, 'opacity:0'), (100 * (0.5 - edge), 'opacity:1'),
                                    (100 * (0.5 + edge), 'opacity:0')], period, 'step-end', 'opacity:0')
    for cls, top, bottom in ((positive, '+', '-'), (negative, '-', '+')):
        f.add(f'<g class="{cls}">' + ''.join(sign(top, x, 106) + sign(bottom, x, 134) for x in (110, 130)) + '</g>')
    for x, name, energy in ((430, 'E_C', lambda t: math.cos(2 * math.pi * t / period) ** 2),
                            (510, 'E_L', lambda t: math.sin(2 * math.pi * t / period) ** 2)):
        f.add(f'<rect class="w" x="{x}" y="50" width="26" height="150"/>')
        bar = sampled(f, f'bar{x}', lambda t, energy=energy: f'transform:scaleY({energy(t):.3f})', period, 48,
                      'transform-box:fill-box;transform-origin:50% 100%')
        f.add(f'<rect class="fill {bar}" x="{x + 3}" y="53" width="20" height="144"/>')
        text(f, x + 13, 222, name)
    text(f, 476, 250, 'their sum stays the same', 'middle', 't s')
    plot = Plot(f, 610, 50, 230, 150, (0, period), (-1.2, 1.2))
    plot.axes('t', None, [(period / 2, ''), (period, '')], [], yzero=0)
    text(f, plot.X(period / 2), plot.y + plot.h + 18, 'one period', 'middle', 't s')
    plot.curve(lambda t: math.cos(2 * math.pi * t / period))
    plot.curve(lambda t: math.sin(2 * math.pi * t / period), 'w curve dash')
    text(f, plot.X(0) + 8, plot.Y(1) - 6, 'v_C', 'start', 't s')
    text(f, plot.X(1) - 4, plot.Y(1) - 6, 'i', 'middle', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(period), plot.y, plot.y + plot.h, period)
    return f


def sections():
    return [
        ('capacitors', 'Capacitors', [
            p('A capacitor stores charge on two plates separated by an insulator, the dielectric. The charge is '
              'proportional to the voltage, so changing the voltage takes current, and a fast change takes a lot.'),
            eq(r'q = C\,v \qquad i = C\,\frac{dv}{dt} \qquad W = \tfrac{1}{2} C v^2', 'Capacitor'),
            eq(r'C = \varepsilon_0 \varepsilon_r \frac{A}{d}', 'Parallel-plate capacitance',
               r'plate area $A$, gap $d$, $\varepsilon_0 = 8.85\,\mathrm{pF/m}$'),
            p('Its voltage cannot jump, since that would need infinite current: a capacitor holds a voltage '
              'steady, which is why every chip has one beside its supply pins. Capacitors in parallel add; in '
              'series they combine like resistors in parallel.'),
            eq(r'C_{par} = C_1 + C_2 \qquad \frac{1}{C_{ser}} = \frac{1}{C_1} + \frac{1}{C_2}',
               'Capacitors combined'),
        ]),
        ('rc', 'Charging and the time constant', [
            fig(charging(), 'In position 1 the source charges C through R: the current, and the dots, start '
                'fast and slow as the capacitor fills, since less voltage is left across R. In position 2 the '
                'capacitor drives the current back the other way and empties. The ring follows $v_C$.'),
            p('Charging from 0 V towards $V$, and discharging from $V_0$, follow exponentials with one time '
              'constant $\\tau = RC$. With 10 kΩ and 100 µF, $\\tau = 1$ s.'),
            eq(r'v_C(t) = V\left(1 - e^{-t/\tau}\right) \qquad \tau = R\,C', 'RC charging'),
            eq(r'v_C(t) = V_0\,e^{-t/\tau} \qquad i(t) = \frac{V}{R}\,e^{-t/\tau}', 'RC discharging and current'),
            table(['Time', 'Charged', 'Left when discharging'],
                  ['$\\tau$', '63.2%', '36.8%'], ['$2\\tau$', '86.5%', '13.5%'], ['$3\\tau$', '95.0%', '5.0%'],
                  ['$4\\tau$', '98.2%', '1.8%'], ['$5\\tau$', '99.3%', '0.7%']),
            p('After five time constants a capacitor counts as full or empty. RC delays debounce buttons, hold a '
              'chip in reset while its supply settles, and set the timing of oscillators.'),
        ]),
        ('inductors', 'Inductors', [
            p('An inductor stores energy in the magnetic field of its current, and resists any change in that '
              'current by producing a voltage. Its current cannot jump, as a capacitor\'s voltage cannot.'),
            eq(r'v = L\,\frac{di}{dt} \qquad W = \tfrac{1}{2} L i^2', 'Inductor'),
            eq(r'i(t) = \frac{V}{R}\left(1 - e^{-t/\tau}\right) \qquad \tau = \frac{L}{R}', 'RL current rise'),
            fig(flyback(), 'With Q1 on, the coil current rises with time constant $L/R$. When Q1 turns off, '
                'the coil keeps that current flowing; D1 gives it a path, and it fades as the coil\'s energy '
                'becomes heat.'),
            p('Without D1, the current would stop in nanoseconds, and $v = L\\,di/dt$ would put hundreds of volts '
              'across the transistor. Every relay, solenoid and motor switched by a transistor needs this '
              '<em>flyback</em> diode, cathode to the supply.'),
            p('Two coils on one core make a transformer, which trades voltage for current in the ratio of their '
              'turns and transforms impedance by its square:'),
            eq(r'\frac{V_s}{V_p} = \frac{N_s}{N_p} = \frac{I_p}{I_s} \qquad Z_{in} = \left(\frac{N_p}{N_s}\right)^2 '
               r'Z_L', 'Transformer'),
        ]),
        ('sines', 'Sine waves', [
            p('Any steady AC signal is built from sine waves, and linear circuits keep their shape, changing only '
              'size and timing. A sine has a peak $V_p$, a frequency $f$ and a phase $\\varphi$:'),
            eq(r'v(t) = V_p \sin(\omega t + \varphi) \qquad \omega = 2\pi f = \frac{2\pi}{T}', 'Sinusoid'),
            fig(phasor(), 'A sine wave is the height of a rotating arrow, the phasor. One turn is one period; the '
                'wave scrolls right as the arrow turns.'),
            p('The root-mean-square value is the DC voltage that would heat a resistor equally. Mains of 230 V '
              'RMS peaks at 325 V.'),
            eq(r'V_{rms} = \sqrt{\frac{1}{T}\int_0^T v^2\,dt} = \frac{V_p}{\sqrt{2}} \qquad V_{pp} = 2 V_p',
               'RMS of a sine'),
        ]),
        ('impedance', 'Phasors and impedance', [
            p('Euler\'s formula turns the rotating arrow into a complex number. Each sine of one frequency becomes '
              'a phasor $V = V_p e^{j\\varphi}$, and $j$ marks the imaginary part, since $i$ is taken by current.'),
            eq(r'e^{j\theta} = \cos\theta + j \sin\theta \qquad v(t) = \operatorname{Re}\left\{V e^{j\omega t}\right\}',
               "Euler's formula"),
            p('Differentiating becomes multiplying by $j\\omega$, so capacitors and inductors obey Ohm\'s law with '
              'a complex resistance, the impedance $Z$:'),
            eq(r'V = I\,Z \qquad Z_R = R \qquad Z_C = \frac{1}{j\omega C} \qquad Z_L = j\omega L', 'Impedance'),
            table(['Part', 'Impedance', 'Size', 'Phase of v against i', 'At DC', 'At high frequency'],
                  ['Resistor', '$R$', '$R$', '0°', '$R$', '$R$'],
                  ['Capacitor', '$1/(j\\omega C)$', '$1/(\\omega C)$', '−90°', 'open circuit', 'short circuit'],
                  ['Inductor', '$j\\omega L$', '$\\omega L$', '+90°', 'short circuit', 'open circuit'], wide=True),
            fig(leads_and_lags(), 'A capacitor\'s current peaks a quarter cycle before its voltage, since it '
                'flows most while the voltage changes fastest. An inductor\'s current peaks a quarter cycle after.'),
            p('Series and parallel rules, dividers, node analysis and Thévenin all work unchanged with impedances, '
              'calculated in complex numbers.'),
        ]),
        ('filters', 'RC filters and Bode plots', [
            p('An RC divider whose lower arm is a capacitor passes slow signals and shorts fast ones to ground: a '
              'low-pass filter. Its transfer function is the divider formula with impedances.'),
            eq(r'H(j\omega) = \frac{v_{out}}{v_{in}} = \frac{1}{1 + j\omega RC} \qquad f_c = \frac{1}{2\pi RC}',
               'RC low-pass filter'),
            eq(r'|H| = \frac{1}{\sqrt{1 + (f/f_c)^2}} \qquad \varphi = -\arctan\frac{f}{f_c}'),
            fig(bode(), 'The Bode plot shows gain in decibels and phase against frequency on log scales. At the '
                'cutoff $f_c$ the gain is −3 dB, half the power; above it the gain falls 20 dB per decade. The '
                'dashed lines are the straight-line asymptotes used for sketching.'),
            fig(filtering(), 'The same filter fed sines at three frequencies: below the cutoff the output follows '
                'the input; at it, the output is 71% as large and 45° late; well above it, little gets through.'),
            p('Swap R and C and the filter passes high frequencies instead:'),
            eq(r'H(j\omega) = \frac{j\omega RC}{1 + j\omega RC}', 'RC high-pass filter'),
            p('Decibels compare two levels on a log scale; a voltage ratio uses 20 log, a power ratio 10 log, so '
              'both give the same number. −3 dB is a voltage ratio of 0.707, −20 dB of 0.1.'),
            eq(r'\mathrm{dB} = 20 \log_{10}\frac{V_2}{V_1} = 10 \log_{10}\frac{P_2}{P_1}', 'Decibels'),
        ]),
        ('resonance', 'Second-order circuits and resonance', [
            p('A capacitor and an inductor together pass energy back and forth: the capacitor\'s charge drives a '
              'current through the inductor, whose current then recharges the capacitor the other way.'),
            fig(tank(), 'An ideal LC tank. The dots surge one way and back as the charge moves between the '
                'plates; the bars show the energy moving from the capacitor\'s field into the inductor\'s and back.'),
            eq(r'\omega_0 = \frac{1}{\sqrt{LC}} \qquad f_0 = \frac{1}{2\pi\sqrt{LC}}', 'Resonant frequency'),
            p('Resistance takes energy out on every swing. A series RLC circuit is described by its natural '
              'frequency and its damping ratio $\\zeta$, or the quality factor $Q$:'),
            eq(r'\zeta = \frac{R}{2}\sqrt{\frac{C}{L}} \qquad Q = \frac{1}{2\zeta} = \frac{1}{R}\sqrt{\frac{L}{C}}',
               'Damping and quality factor'),
            fig(step_responses(), 'Below $\\zeta = 1$ the response overshoots and rings; at 1 it settles fastest '
                'without overshoot; above it, it creeps. The same three behaviours appear in mechanics and in '
                'control loops.'),
            p('Driven by a sine, a series RLC circuit\'s reactances cancel at $\\omega_0$, leaving only $R$: the '
              'current peaks there. The higher the $Q$, the narrower the peak; its width between the −3 dB points '
              'is $f_0 / Q$. Radios tune this way.'),
            fig(resonance(), 'Current against frequency for $Q$ of 1, 3 and 10.'),
        ]),
        ('power', 'Power in AC circuits', [
            p('With voltage and current out of phase, part of the energy only sloshes back and forth. The average, '
              'real power counts just the in-phase part; the rest is reactive power, and their combination is the '
              'apparent power a supply must carry.'),
            eq(r'P = V_{rms} I_{rms} \cos\varphi \qquad Q = V_{rms} I_{rms} \sin\varphi \qquad S = V_{rms} I_{rms}',
               'AC power'),
            p('The power factor $\\cos\\varphi$ is 1 for a resistor and 0 for an ideal capacitor or inductor. '
              'Units: watts for $P$, volt-amperes reactive for $Q$, volt-amperes for $S$.'),
            note('Read more: MIT 6.002 lectures 12 to 18 (first- and second-order circuits, sinusoidal steady '
                 'state, impedance, filters) and <em>Lessons in Electric Circuits II: AC</em>, in DOCS → CIRCUITS '
                 'LIBRARY.'),
        ]),
    ]
