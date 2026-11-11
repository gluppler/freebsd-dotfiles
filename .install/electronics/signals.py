import inspect
import math
import random

from draw import (Figure, Plot, arrow, begin, circle, dot, end, line, phases, rect, steps, sweep, text, travel,
                  wire)
from page import code, eq, fig, note, p, table

NAME = '07-signals'
TITLE = 'Signals, sampling and control'
LEDE = ('PWM and the spectrum of a square wave; sampling, aliasing and ADC resolution; smoothing noisy readings; '
        'poles and stability; and feedback control with a PID loop, simulated on this page.')


def pwm():
    f = Figure(900, 230, 'Pulse-width modulation at four duty cycles, with its average and an LED driven by it')
    plot = Plot(f, 70, 40, 600, 150, (0, 3), (0, 1.25))
    plot.axes('t', None, [(1, ''), (2, ''), (3, '')], [(1, 'V_S'), (0, '0')])
    circle(f, 790, 115, 36, 'w')
    for cls, duty in zip(phases(f, 4, 12), (0.1, 0.25, 0.5, 0.9)):
        begin(f, cls)
        samples = [point for k in range(3) for point in ((k, 1), (k + duty, 0))] + [(3, 0)]
        plot.curve(steps(samples))
        plot.curve([(0, duty), (3, duty)], 'w thin dash')
        text(f, 70, 24, f'D = {100 * duty:.0f}%: average {duty:.2f} V_S', 'start')
        f.add(f'<circle class="fill" cx="790" cy="115" r="30" fill-opacity="{duty}"/>')
        end(f)
    text(f, 790, 172, 'LED', 'middle', 't s')
    return f


def fourier():
    f = Figure(900, 270, 'A square wave built up from its odd harmonics')
    plot = Plot(f, 60, 40, 520, 190, (0, 2), (-1.45, 1.45))
    plot.axes('t', None, [(1, ''), (2, '')], [(1, '1'), (-1, '−1')], yzero=0)
    plot.curve(steps([(0, 1), (0.5, -1), (1, 1), (1.5, -1), (2, -1)]), 'w thin dash')
    bars = Plot(f, 650, 40, 220, 190, (0, 20), (0, 1.4))
    bars.axes('k', None, [(k, str(k)) for k in (1, 5, 9, 13, 17)], [(4 / math.pi, '4/π')])
    for cls, terms in zip(phases(f, 4, 12), (1, 2, 3, 10)):
        begin(f, cls)
        partial = lambda t: sum(4 / math.pi * math.sin(2 * math.pi * (2 * k + 1) * t) / (2 * k + 1)
                                for k in range(terms))
        plot.curve(plot.points(partial, 0, 2, 1200))
        for k in range(10):
            h = 2 * k + 1
            top = bars.Y(4 / math.pi / h)
            rect(f, bars.X(h) - 3.5, top, 7, bars.Y(0) - top, 'fill' if k < terms else 'w thin faint')
        words = f'{terms} term{"s" if terms > 1 else ""}: harmonics 1 to {2 * terms - 1}'
        text(f, 60, 24, words, 'start')
        end(f)
    return f


def aliasing():
    f = Figure(900, 250, 'A sine sampled at three frequencies, the last above half the sampling rate')
    plot = Plot(f, 50, 50, 800, 160, (0, 10), (-1.3, 1.3))
    plot.axes('n', None, [(k, str(k)) for k in range(11)], [], yzero=0)
    words = {0.1: 'f = 0.1 f_s: ten samples a cycle; the shape is clear',
             0.45: 'f = 0.45 f_s: just over two a cycle; enough, in theory',
             0.9: 'f = 0.9 f_s: the samples trace a false sine at 0.1 f_s'}
    for cls, ratio in zip(phases(f, 3, 12), words):
        begin(f, cls)
        plot.curve(plot.points(lambda t: math.sin(2 * math.pi * ratio * t), 0, 10, 900), 'w thin dim')
        if ratio > 0.5:
            plot.curve(lambda t: math.sin(2 * math.pi * (ratio - 1) * t), 'w curve dash')
        for n in range(11):
            dot(f, plot.X(n), plot.Y(math.sin(2 * math.pi * ratio * n)), 4.5)
        text(f, 50, 26, words[ratio], 'start')
        end(f)
    return f


def quantise():
    f = Figure(900, 290, 'A 3-bit ADC: its staircase of codes and the error it makes')
    plot = Plot(f, 90, 40, 400, 200, (0, 8), (0, 8))
    plot.axes('V_in / LSB', 'code', [(k, str(k)) for k in range(9)], [(k, format(k, '03b')) for k in range(8)],
              grid=True)
    plot.curve([(0, 0), (8, 8)], 'w thin dash')
    stairs = steps([(0, 0)] + [(k - 0.5, k) for k in range(1, 8)] + [(8, 7)])
    plot.curve(stairs)
    times, last = [], -1
    for v, _ in stairs:
        last = max(v / 8, last + 0.002)
        times.append(last)
    walk = travel(f, 'walk', [(plot.X(v), plot.Y(c)) for v, c in stairs], 12, [t / times[-1] for t in times])
    f.add(f'<g class="{walk}"><circle class="walker" r="6"/></g>')
    error = Plot(f, 610, 70, 230, 140, (0, 8), (-1.1, 1.1))
    error.axes('V_in', 'error (LSB)', [(4, '4'), (8, '8')], [(0.5, '+½'), (0, '0'), (-0.5, '−½'), (-1, '−1')],
               grid=True)
    error.curve(error.points(lambda v: min(7, math.floor(v + 0.5)) - v, 0, 8, 1600))
    return f


def noisy_step():
    """A step at sample 25 with uniform noise, the same on every build."""
    rng = random.Random(3)
    return [(n, (1 if n >= 25 else 0) + rng.uniform(-0.3, 0.3)) for n in range(120)]


def smoothing():
    f = Figure(900, 250, 'A noisy step smoothed by a moving average and by an exponential average')
    data = noisy_step()
    average, ema, y = [], [], 0.0
    for n, x in data:
        window = [v for _, v in data[max(0, n - 7):n + 1]]
        average.append((n, sum(window) / len(window)))
        y = 0.2 * x + 0.8 * y
        ema.append((n, y))
    plot = Plot(f, 60, 40, 600, 180, (0, 120), (-0.5, 1.5))
    plot.axes('n', None, [(k, str(k)) for k in range(0, 121, 20)], [(0, '0'), (1, '1')], grid=True)
    plot.curve(data, 'w thin dim')
    plot.curve(average)
    plot.curve(ema, 'w curve dash')
    for k, words in enumerate(('thin: input with noise', 'solid: moving average of 8', 'dashed: EMA, α = 0.2')):
        text(f, 700, 90 + 18 * k, words, 'start', 't s')
    return f


def poles():
    f = Figure(900, 280, 'Pole positions in the s-plane and the responses they give')
    plane = Plot(f, 60, 30, 260, 220, (-2, 1), (-2.6, 2.6))
    rect(f, plane.X(0), plane.y, plane.X(1) - plane.X(0), plane.h, 'shade')
    plane.axes('σ', 'jω', [], [], xzero=0, yzero=0)
    text(f, plane.X(0.5), plane.y + 16, 'unstable', 'middle', 't s')
    marks = (('a', -1, 0), ('b', -0.5, 2), ('b', -0.5, -2), ('c', 0.4, 1.5), ('c', 0.4, -1.5))
    for name, re, im in marks:
        x, y = plane.X(re), plane.Y(im)
        line(f, x - 6, y - 6, x + 6, y + 6, 'w bold')
        line(f, x - 6, y + 6, x + 6, y - 6, 'w bold')
        text(f, x - 10, y - 8, name, 'end', 't s')
    responses = (('a', lambda t: math.exp(-t), 'one real pole: decays'),
                 ('b', lambda t: math.exp(-0.5 * t) * math.cos(2 * t), 'complex pair, left half: rings down'),
                 ('c', lambda t: 0.009 * math.exp(0.4 * t) * math.cos(1.5 * t), 'right half: grows'))
    for k, (name, response, words) in enumerate(responses):
        small = Plot(f, 420, 36 + 80 * k, 420, 52, (0, 12), (-1.2, 1.2))
        small.axes(None, None, [], [], yzero=0)
        small.curve(small.points(response, 0, 12, 600))
        text(f, 404, 36 + 80 * k + 30, name, 'end', 't b')
        text(f, 840, 36 + 80 * k - 2, words, 'end', 't s')
    return f


def block(f, x, y, label, width=100):
    rect(f, x, y - 25, width, 50)
    text(f, x + width / 2, y + 5, label, 'middle', 't b')


def loop():
    f = Figure(900, 210, 'A feedback control loop')
    arrow(f, 60, 80, 166, 80, 'w', 8)
    circle(f, 180, 80, 14)
    line(f, 170, 70, 190, 90, 'w thin')
    line(f, 170, 90, 190, 70, 'w thin')
    arrow(f, 194, 80, 290, 80, 'w', 8)
    block(f, 290, 80, 'C(s)')
    arrow(f, 390, 80, 490, 80, 'w', 8)
    block(f, 490, 80, 'P(s)')
    arrow(f, 590, 80, 790, 80, 'w', 8)
    dot(f, 700, 80)
    wire(f, (700, 80), (700, 160), (180, 160))
    arrow(f, 180, 160, 180, 94, 'w', 8)
    text(f, 50, 84, 'r', 'end', 't b')
    text(f, 800, 84, 'y', 'start', 't b')
    text(f, 160, 70, '+', 'end')
    text(f, 170, 120, '−', 'end')
    text(f, 240, 70, 'e = r − y', 'middle', 't s')
    text(f, 440, 70, 'u', 'middle', 't s')
    text(f, 340, 128, 'controller', 'middle', 't s')
    text(f, 540, 128, 'plant', 'middle', 't s')
    text(f, 440, 178, 'measured by a sensor', 'middle', 't s')
    return f


def controller(kp, ki, kd, dt, low=-10.0, high=10.0):
    """A PID controller; step(setpoint, measured) returns the output."""
    state = {'integral': 0.0, 'last': None}

    def step(setpoint, measured):
        error = setpoint - measured
        # Differentiate the measurement, not the error: no kick when the setpoint jumps.
        rate = 0.0 if state['last'] is None else (measured - state['last']) / dt
        state['last'] = measured
        integral = state['integral'] + ki * error * dt
        out = kp * error + integral - kd * rate
        if low < out < high:  # anti-windup: stop integrating while the output is pinned
            state['integral'] = integral
        return max(low, min(high, out))
    return step


def simulate(kp, ki, kd, seconds=20.0, dt=0.01):
    """Step response of the plant 1/(s + 1)^3, three lags in a row, under PID control."""
    control = controller(kp, ki, kd, dt)
    x = [0.0, 0.0, 0.0]
    out = [(0.0, 0.0)]
    for n in range(int(seconds / dt)):
        u = control(1.0, x[2])
        x[0] += (u - x[0]) * dt
        x[1] += (x[0] - x[1]) * dt
        x[2] += (x[1] - x[2]) * dt
        out.append(((n + 1) * dt, x[2]))
    return out


GAINS = (('P', (2, 0, 0), 'w curve dots'), ('PI', (1.2, 0.5, 0), 'w curve dash'), ('PID', (3, 0.7, 2.5), 'w curve'))
ZIEGLER = (4.8, 2.65, 2.18)


def responses():
    f = Figure(900, 270, 'Step responses of the same plant under P, PI and PID control')
    plot = Plot(f, 70, 40, 560, 190, (0, 20), (0, 1.3))
    plot.axes('t (s)', None, [(k, str(k)) for k in range(0, 21, 5)], [(0, '0'), (1, 'setpoint')], grid=True)
    for name, gains, cls in GAINS:
        plot.curve(simulate(*gains), cls)
    plot.curve([(0, 2 / 3), (20, 2 / 3)], 'w thin faint')
    rows = [f'{style}: {name}, K_p {kp:g}, K_i {ki:g}, K_d {kd:g}'
            for (name, (kp, ki, kd), _), style in zip(GAINS, ('dotted', 'dashed', 'solid'))]
    for k, words in enumerate(rows):
        text(f, 660, 90 + 18 * k, words, 'start', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(20), plot.y, plot.y + plot.h, 10)
    return f


def summary(gains):
    """Final value, peak, 90% rise time and 2% settling time of a step response."""
    data = simulate(*gains)
    final = data[-1][1]
    peak = max(v for _, v in data)
    rise = next(t for t, v in data if v >= 0.9 * final)
    settle = next((t for t, v in reversed(data) if abs(v - final) > 0.02 * final), 0.0)
    return final, peak, rise, settle


def volts(value):
    return f'{value * 1e3:.3g} mV' if value >= 1e-3 else f'{value * 1e6:.3g} µV'


def sections():
    p_final, p_peak, _, _ = summary(GAINS[0][1])
    pi_final, pi_peak, _, pi_settle = summary(GAINS[1][1])
    pid_final, pid_peak, pid_rise, pid_settle = summary(GAINS[2][1])
    _, zn_peak, zn_rise, _ = summary(ZIEGLER)
    assert abs(p_final - 2 / 3) < 0.01 and abs(pi_final - 1) < 0.01 and abs(pid_final - 1) < 0.01
    assert pid_peak < pi_peak and pid_settle < pi_settle
    return [
        ('pwm', 'Pulse-width modulation', [
            p('A digital pin can only be on or off, but switched fast enough its average can be anything in '
              'between. The duty cycle $D$ is the fraction of each period spent on:'),
            eq(r'D = \frac{t_{on}}{T} \qquad V_{avg} = D\,V_S', 'PWM average'),
            fig(pwm(), 'Four duty cycles. An LED switched this fast looks as bright as its average, since the eye '
                'averages anything above about 100 Hz; a motor\'s inertia averages it too.'),
            p('Choose the frequency for the load: a few hundred hertz or more for LEDs, so they do not flicker on '
              'camera, and above 20 kHz for motors, so they do not whine. An RC low-pass filter with its cutoff '
              'well below the PWM frequency turns PWM into a steady voltage, a cheap DAC.'),
        ]),
        ('spectrum', 'Spectra and the square wave', [
            p('Any periodic signal is a sum of sines at multiples of its frequency, its harmonics. A square wave '
              'contains only the odd ones, falling as $1/k$:'),
            eq(r'x(t) = \frac{4}{\pi} \sum_{k = 1, 3, 5, \ldots} \frac{\sin(k \omega t)}{k}', 'Square-wave series'),
            fig(fourier(), 'Adding harmonics one at a time sharpens the edges. The ripple near each edge never '
                'shrinks below about 9% of the jump, the Gibbs phenomenon. Right: the size of each harmonic.'),
            p('This is why fast digital edges radiate interference far above the clock frequency, and why a '
              'square wave through a low-pass filter comes out rounded: the filter removes the upper harmonics.'),
        ]),
        ('sampling', 'Sampling and aliasing', [
            p('An ADC measures a signal at regular instants, $f_s$ times a second. The samples capture '
              'everything below half that rate, the Nyquist frequency; anything above it is not lost but '
              'folded down, indistinguishable from a lower frequency.'),
            eq(r'f_s > 2 f_{max} \qquad f_{alias} = \left| f - k f_s \right|', 'Sampling theorem'),
            fig(aliasing(), 'The same ten sample instants applied to three sines. Above $f_s/2$, the samples '
                'are exactly those of a slower sine, and nothing after the ADC can tell them apart.'),
            p('So filter before sampling: an analog low-pass filter, an anti-aliasing filter, removes what is '
              'above $f_s/2$ before the ADC sees it. The same effect makes wheels in films seem to turn '
              'backwards.'),
        ]),
        ('adc', 'ADCs and resolution', [
            p('An $N$-bit ADC divides its reference voltage into $2^N$ steps. One step is the least significant '
              'bit, the LSB, the smallest change it can see:'),
            eq(r'\mathrm{LSB} = \frac{V_{ref}}{2^N} \qquad \mathrm{code} = \left\lfloor \frac{V_{in}}{\mathrm{LSB}} '
               r'+ \frac{1}{2} \right\rfloor', 'ADC resolution'),
            fig(quantise(), 'An ideal ADC rounds to the nearest step, so its error, right, stays within half an '
                'LSB until the input passes the top code. The ring climbs the staircase as the input rises.'),
            p('That rounding error behaves like noise, which limits the signal-to-noise ratio of a perfect '
              '$N$-bit converter to:'),
            eq(r'\mathrm{SNR} = 6.02\,N + 1.76\ \mathrm{dB}', 'Quantisation noise'),
            table(['Bits', 'Steps', 'LSB at 3.3 V', 'Ideal SNR'],
                  *[[str(n), f'{2 ** n:,}'.replace(',', ' '), volts(3.3 / 2 ** n), f'{6.02 * n + 1.76:.0f} dB']
                    for n in (8, 10, 12, 16)]),
            p('Real converters fall short of their bit count: noise, offset and gain error each cost some. The '
              'effective number of bits is the SNR you measure turned back into bits. A DAC runs the other way, '
              '$V_{out} = \\mathrm{code} \\cdot V_{ref}/2^N$.'),
        ]),
        ('smoothing', 'Smoothing readings', [
            p('Sensor readings are noisy. A moving average of the last $M$ samples divides the noise by '
              '$\\sqrt{M}$ and delays the reading by about $M/2$ samples:'),
            eq(r'y[n] = \frac{1}{M} \sum_{k=0}^{M-1} x[n-k]', 'Moving average'),
            p('An exponential moving average needs no buffer. Each new sample pulls the average a fraction '
              '$\\alpha$ of the way towards it; it is the digital twin of an RC low-pass filter:'),
            eq(r'y[n] = \alpha\,x[n] + (1 - \alpha)\,y[n-1] \qquad \alpha = \frac{\Delta t}{RC + \Delta t}',
               'Exponential moving average'),
            fig(smoothing(), 'Both follow the step and ignore most of the noise. The moving average reaches the '
                'new level in exactly eight samples; the exponential average approaches it gradually.'),
            p('With $\\alpha$ a power of two, firmware needs only a shift and an add. Keep the average scaled up, '
              'or the rounding loses the small steps:'),
            code('''
/* Exponential moving average with alpha = 1/8; avg8 holds eight times the average. */
static int32_t avg8;

int32_t smooth(int32_t sample)
{
    avg8 += sample - (avg8 >> 3);
    return avg8 >> 3;
}
'''),
            p('For readings with occasional wild spikes, such as an ultrasonic range finder, a median of the last '
              'three or five samples removes the spikes before averaging.'),
        ]),
        ('poles', 'Transfer functions and stability', [
            p('A linear system is described by its transfer function $H(s)$, where $s$ stands for '
              'differentiation: an RC filter is $1/(sRC + 1)$, a capacitor $1/(sC)$. The values of $s$ that '
              'make the denominator zero, the poles, decide how the system responds:'),
            eq(r'H(s) = \frac{K}{\tau s + 1} \qquad H(s) = \frac{\omega_0^2}{s^2 + 2\zeta\omega_0 s + \omega_0^2}',
               'First- and second-order systems'),
            fig(poles(), 'Each pole $s = \\sigma + j\\omega$ contributes a response $e^{\\sigma t}$, '
                'oscillating at $\\omega$ if $\\omega \\ne 0$. Poles in the left half decay; any pole in the '
                'shaded right half grows without limit.'),
            p('A system is stable if every pole has a negative real part. Sampled systems use $z = e^{sT}$ in '
              'place of $s$, and are stable if every pole lies inside the unit circle.'),
        ]),
        ('feedback', 'Feedback control', [
            p('A controller compares the measured output $y$ with the setpoint $r$ and drives the plant, the '
              'motor or heater or arm, to shrink the error:'),
            fig(loop(), 'The closed loop: the controller sees only the error.'),
            eq(r'T(s) = \frac{C(s)\,P(s)}{1 + C(s)\,P(s)}', 'Closed-loop transfer function'),
            p('Feedback makes a system follow the setpoint, resist disturbances and tolerate an imprecise plant. '
              'Too much gain, with delays in the loop, makes it oscillate: the same instability as a pole '
              'crossing into the right half plane.'),
        ]),
        ('pid', 'PID control', [
            p('The PID controller, used in everything from ovens to drones, adds three terms: one proportional '
              'to the error, one to its integral, which removes any lasting error, and one to its rate of '
              'change, which damps overshoot:'),
            eq(r'u(t) = K_p\,e(t) + K_i \int_0^t e\,d\tau + K_d\,\frac{de}{dt}', 'PID controller'),
            p('Sampled every $\\Delta t$ seconds, the integral becomes a running sum and the derivative a '
              'difference. This code draws the graph below: it runs when this page is built.'),
            code(inspect.getsource(controller) + '\n\n' + inspect.getsource(simulate)),
            fig(responses(), f'The plant is three first-order lags in a row. Proportional control alone settles '
                f'at {p_final:.2f}, short of the setpoint, after peaking at {p_peak:.2f}. Integral action removes '
                f'the error but overshoots to {pi_peak:.2f} and takes {pi_settle:.0f} s to settle within 2%. '
                f'Derivative action damps the loop, which allows higher gains: 90% after {pid_rise:.1f} s, a peak '
                f'of {pid_peak:.2f}, settled after {pid_settle:.0f} s.'),
            eq(r'e_{ss} = \frac{1}{1 + K_p P(0)}', 'Steady-state error under P control'),
            p('To tune by hand: start with $K_i = K_d = 0$ and raise $K_p$ until the response is quick but rings; '
              'add $K_d$ to damp the ringing; add a little $K_i$ to remove the remaining error. The '
              'Ziegler–Nichols rule starts from the gain $K_u$ at which proportional control just oscillates, '
              'with period $T_u$:'),
            eq(r'K_p = 0.6\,K_u \qquad T_i = \frac{T_u}{2} \qquad T_d = \frac{T_u}{8} \qquad K_i = \frac{K_p}{T_i} '
               r'\qquad K_d = K_p T_d', 'Ziegler–Nichols tuning'),
            p(f'For this plant $K_u = 8$ and $T_u = 2\\pi/\\sqrt{{3}} \\approx 3.6$ s, giving $K_p = 4.8$, '
              f'$K_i = 2.65$, $K_d = 2.18$: a fast rise, 90% in {zn_rise:.1f} s, but a peak of {zn_peak:.2f}. '
              f'Ziegler–Nichols is a starting point; most loops then need their gains reduced.'),
            note('Read more: <em>Feedback Systems</em> by Åström and Murray, in DOCS → ROBOTICS LIBRARY, covers '
                 'all of this in depth; <em>Lessons in Electric Circuits IV: Digital</em> has a chapter on ADCs '
                 'and DACs, in DOCS → CIRCUITS LIBRARY.'),
        ]),
    ]
