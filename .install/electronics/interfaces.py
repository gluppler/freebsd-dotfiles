import math

from draw import (Figure, Plot, begin, dot, end, flow, ground, line, mosfet, phases, rail, rect, sweep, terminal,
                  text, trace, two, wire)
from page import code, eq, fig, link, note, p, table

NAME = '09-interfaces'
TITLE = 'Microcontroller hardware'
LEDE = ('Driving and reading pins; buttons and debouncing; level shifting; UART, I2C and SPI on the wire; '
        'regulators and battery life; decoupling, clocks and protection; and reading sensors.')

HIGH, LOW = 'w bold', 'w thin dim'


def push_pull():
    f = Figure(900, 260, 'A push-pull output sourcing current into one LED, then sinking it from another')
    rail(f, 300, 30, 'V_DD')
    top = mosfet(f, 292, 80, True)
    bottom = mosfet(f, 292, 180)
    text(f, 312, 64, 'P', 'start', 't s')
    text(f, 312, 210, 'N', 'start', 't s')
    wire(f, (300, 30), top['S'])
    wire(f, top['D'], bottom['D'])
    ground(f, *bottom['S'])
    wire(f, top['G'], (240, 72), (240, 188), bottom['G'])
    wire(f, (150, 130), (240, 130))
    terminal(f, 150, 130)
    dot(f, 240, 130)
    dot(f, 300, 130)
    wire(f, (300, 130), (470, 130))
    terminal(f, 380, 130)
    text(f, 380, 120, 'pin', 'middle', 't s')
    dot(f, 470, 130)
    rail(f, 470, 30, 'V_DD')
    two(f, 'LED', (470, 30), (470, 80))
    two(f, 'R', (470, 80), (470, 130))
    two(f, 'LED', (470, 130), (470, 184))
    two(f, 'R', (470, 184), (470, 230))
    ground(f, 470, 230)
    states = ((0, 'HIGH', ('The gate is low: the P-MOSFET conducts', 'and connects the pin to V_DD. The pin',
                           'sources current through the lower LED.')),
              (1, 'LOW', ('The gate is high: the N-MOSFET conducts',
                          'and connects the pin to ground. The pin', 'sinks current from the upper LED.')))
    for cls, (gate, level, words) in zip(phases(f, 2, 8), states):
        begin(f, cls)
        text(f, 150, 112, f'gate {gate}', 'middle', 't s')
        if gate:
            flow(f, [(470, 30), (470, 130), (300, 130), bottom['D']])
            flow(f, [bottom['S'], (300, 214)])
            text(f, 500, 59, 'lit', 'start', 't b')
        else:
            flow(f, [(300, 30), top['S']])
            flow(f, [top['D'], (300, 130), (470, 130), (470, 240)])
            text(f, 500, 161, 'lit', 'start', 't b')
        text(f, 580, 100, f'pin {level}', 'start', 't head')
        for k, line_text in enumerate(words):
            text(f, 580, 128 + 18 * k, line_text, 'start', 't s')
        end(f)
    return f


def open_drain():
    f = Figure(900, 250, 'Two open-drain outputs sharing one line with a pull-up resistor')
    rail(f, 180, 30, 'V_DD')
    two(f, 'R', (180, 30), (180, 100), 'R_pu', side=-1)
    xs = (360, 560)
    pins = [mosfet(f, x - 8, 150) for x in xs]
    for k, (x, pin) in enumerate(zip(xs, pins)):
        wire(f, (x, 100), pin['D'])
        dot(f, x, 100)
        ground(f, *pin['S'])
        wire(f, pin['G'], (x - 50, 158))
        terminal(f, x - 50, 158)
        text(f, x - 58, 162, f'device {k + 1}', 'end', 't s')
    terminal(f, 720, 100)
    text(f, 730, 104, 'line', 'start')
    states = (((0, 0), 'Nobody pulls: the resistor holds the line high.'),
              ((1, 0), 'Device 1 pulls the line low, through the resistor.'),
              ((0, 1), 'Device 2 pulls it low; neither can drive it high.'))
    for cls, (pulls, words) in zip(phases(f, 3, 9), states):
        level = 0 if any(pulls) else 1
        begin(f, cls)
        wire(f, (180, 100), (720, 100), cls=HIGH if level else LOW)
        for x, pull in zip(xs, pulls):
            text(f, x - 50, 180, f'gate {pull}', 'middle', 't s')
            if pull:
                flow(f, [(180, 30), (180, 100), (x, 100), (x, 126)])
                flow(f, [(x, 174), (x, 184)])
        text(f, 730, 124, f'= {level}', 'start', 't b')
        text(f, 450, 236, words, 'middle', 't s')
        end(f)
    for x in (180,) + xs:
        dot(f, x, 100)
    return f


BOUNCE = [(0, 1), (5.0, 0), (5.4, 1), (5.9, 0), (6.1, 1), (6.8, 0), (7.0, 1), (7.3, 0),
          (25.0, 1), (25.3, 0), (25.8, 1), (26.0, 0), (26.4, 1)]


def raw(t):
    return [v for when, v in BOUNCE if when <= t][-1]


def debounced(samples=5):
    """The output of the debounce code below, sampling raw() every millisecond."""
    state, count, changes = 1, 0, [(0, 1)]
    for ms in range(41):
        if raw(ms) == state:
            count = 0
        else:
            count += 1
            if count >= samples:
                state, count = raw(ms), 0
                changes.append((ms, state))
    return changes


def bounce():
    f = Figure(900, 230, 'A push button bouncing as it is pressed and released, and the debounced signal')
    x0, scale = 120, 18
    trace(f, x0, 50, scale, BOUNCE, 40, 'contact')
    for ms in range(41):
        line(f, x0 + ms * scale, 92, x0 + ms * scale, 97, 'w thin faint')
    text(f, x0 - 14, 98, 'samples', 'end', 't s')
    clean = debounced()
    trace(f, x0, 130, scale, clean, 40, 'debounced')
    for when, words in ((6, 'pressed: bounces'), (25.7, 'released')):
        text(f, x0 + when * scale, 36, words, 'middle', 't s')
    for when, _ in clean[1:]:
        line(f, x0 + when * scale, 120, x0 + when * scale, 164, 'w thin dash')
    text(f, x0, 196, '0', 'middle', 't s')
    for ms in (10, 20, 30, 40):
        text(f, x0 + ms * scale, 196, f'{ms} ms', 'middle', 't s')
    sweep(f, 'cursor', x0, x0 + 40 * scale, 30, 170, 10)
    return f


DEBOUNCE = '''
/* Call every millisecond with the pin's level; 1 is released, with a pull-up.
   The result changes only after five equal readings in a row. */
uint8_t debounce(uint8_t raw)
{
    static uint8_t state = 1, count;

    if (raw == state) {
        count = 0;
    } else if (++count >= 5) {
        state = raw;
        count = 0;
    }
    return state;
}
'''


def shifter():
    f = Figure(900, 290, 'A one-MOSFET bidirectional level shifter between 3.3 V and 5 V logic')
    cx, cy = 450, 140
    begin(f, transform=f'translate({cx} {cy}) rotate(90)')
    local = mosfet(f, 0, 0)
    end(f)
    pins = {name: (cx - y, cy + x) for name, (x, y) in local.items()}
    line_y = pins['S'][1]
    rail(f, pins['G'][0], 60, '3.3 V')
    wire(f, (pins['G'][0], 60), pins['G'])
    text(f, cx + 34, cy - 14, 'BSS138', 'start', 't s')
    rail(f, 300, 50, '3.3 V')
    rail(f, 600, 50, '5 V')
    two(f, 'R', (300, 50), (300, line_y), 'R_1', side=-1)
    two(f, 'R', (600, 50), (600, line_y), 'R_2', side=1)
    wire(f, (150, line_y), pins['S'])
    wire(f, pins['D'], (750, line_y))
    wire(f, (410, line_y), (410, 190))
    two(f, 'D', (410, 190), (490, 190))
    wire(f, (490, 190), (490, line_y))
    text(f, 450, 212, 'body diode', 'middle', 't s')
    for x in (300, 410, 490, 600):
        dot(f, x, line_y)
    for x, name in ((150, '3.3 V side'), (750, '5 V side')):
        terminal(f, x, line_y)
        text(f, x, line_y + 24, name, 'middle', 't s')
    for x in (210, 690):
        dot(f, x, line_y)
        ground(f, x, 222)
    states = (('Both released', (3.3, 5.0), ('each pull-up holds its own side high.',
                                             'V_GS = 0, so the MOSFET is off.')),
              ('3.3 V side pulls low', (0.0, 0.0), ('the source falls and V_GS rises to 3.3 V,',
                                                    'so the MOSFET turns on and pulls the 5 V side low.')),
              ('5 V side pulls low', (0.0, 0.0), ('the body diode drags the source down,',
                                                  'V_GS rises, and the MOSFET turns on.')))
    for k, (cls, (title, volts, words)) in enumerate(zip(phases(f, 3, 12), states)):
        begin(f, cls)
        wire(f, (150, line_y), pins['S'], cls=HIGH if volts[0] else LOW)
        wire(f, pins['D'], (750, line_y), cls=HIGH if volts[1] else LOW)
        text(f, 250, line_y - 10, f'{volts[0]:g} V', 'middle', 't b')
        text(f, 650, line_y - 10, f'{volts[1]:g} V', 'middle', 't b')
        two(f, 'SWon' if k == 1 else 'SW', (210, line_y), (210, 222))
        two(f, 'SWon' if k == 2 else 'SW', (690, line_y), (690, 222))
        if k == 1:
            flow(f, [(600, 50), (600, line_y), pins['D']])
            flow(f, [pins['S'], (210, line_y), (210, 232)])
            flow(f, [(300, 50), (300, line_y)])
        elif k == 2:
            flow(f, [(300, 50), (300, line_y), pins['S']])
            flow(f, [pins['D'], (690, line_y), (690, 232)])
            flow(f, [(600, 50), (600, line_y)])
        for n, words_line in enumerate((f'{title}: {words[0]}', words[1])):
            text(f, 450, 236 + 18 * n, words_line, 'middle', 't s')
        end(f)
    return f


def uart():
    f = Figure(900, 210, "A UART sending the byte 0x41, the letter A, as one frame")
    x0, scale = 100, 60
    bits = [(value >> k) & 1 for value in (0x41,) for k in range(8)]
    levels = [1, 0] + bits + [1, 1]
    trace(f, x0, 60, scale, [(k, v) for k, v in enumerate(levels)], 12, 'TX', 36)
    names = ['idle', 'start'] + [f'D{k}' for k in range(8)] + ['stop', 'idle']
    for k, (name, value) in enumerate(zip(names, levels)):
        x = x0 + (k + 0.5) * scale
        if 0 < k < 11:
            line(f, x0 + k * scale, 50, x0 + k * scale, 104, 'w thin faint')
            dot(f, x, 60 if value else 96, 3.5)
        text(f, x, 126, name, 'middle', 't s')
        if 1 < k < 10:
            text(f, x, 42, str(value), 'middle', 't b')
    line(f, x0 + 11 * scale, 50, x0 + 11 * scale, 104, 'w thin faint')
    text(f, 450, 160, 'least significant bit first: 0x41 = 0100 0001 is sent as 1, 0, 0, 0, 0, 0, 1, 0', 'middle',
         't s')
    text(f, 450, 182, 'the receiver samples the middle of each bit, timed from the falling edge of the start bit',
         'middle', 't s')
    sweep(f, 'cursor', x0, x0 + 12 * scale, 34, 110, 12)
    return f


def i2c():
    f = Figure(900, 270, 'An I2C write of the byte 0xA5 to the device at address 0x3C')
    x0, scale = 80, 40
    address = [(0x3C >> (6 - k)) & 1 for k in range(7)]
    data = [(0xA5 >> (7 - k)) & 1 for k in range(8)]
    bits = address + [0, 0] + data + [0]
    scl, sda = [(0, 1)], [(0, 1), (0.5, 0)]
    for k, bit in enumerate(bits, start=1):
        scl += [(k, 0), (k + 0.25, 1), (k + 0.75, 0)]
        sda.append((k + 0.1, bit))
    stop = len(bits) + 1
    scl += [(stop, 0), (stop + 0.25, 1)]
    sda += [(stop + 0.1, 0), (stop + 0.5, 1)]
    for k in (9, 18):
        rect(f, x0 + k * scale, 100, scale, 44, 'shade')
    trace(f, x0, 52, scale, scl, stop + 1, 'SCL', 30)
    trace(f, x0, 108, scale, sda, stop + 1, 'SDA', 30)
    labels = ['S'] + [str(b) for b in address] + ['W', 'ACK'] + [str(b) for b in data] + ['ACK', 'P']
    for k, name in enumerate(labels):
        text(f, x0 + (k + 0.5) * scale, 164, name, 'middle', 't s')
    for start, stop_slot, name in ((1, 8, 'address 0x3C'), (8, 9, 'write'), (10, 18, 'data 0xA5')):
        middle = x0 + (start + stop_slot) / 2 * scale
        line(f, x0 + start * scale + 4, 184, x0 + stop_slot * scale - 4, 184, 'w thin')
        text(f, middle, 202, name, 'middle', 't s')
    text(f, x0 + 0.5 * scale, 36, 'start', 'middle', 't s')
    text(f, x0 + (stop + 0.5) * scale, 36, 'stop', 'middle', 't s')
    text(f, 450, 240, 'shaded: the device pulls SDA low to acknowledge; SDA changes only while SCL is low',
         'middle', 't s')
    sweep(f, 'cursor', x0, x0 + (stop + 1) * scale, 44, 146, 12)
    return f


def spi():
    f = Figure(900, 280, 'An SPI transfer in mode 0: a byte out on MOSI and a byte in on MISO at the same time')
    x0, scale = 110, 80
    out, back = 0x9C, 0x5A
    trace(f, x0, 40, scale, [(0, 1), (0.5, 0), (8.6, 1)], 9.2, 'CS', 26)
    clock = [(0, 0)] + [point for k in range(8) for point in ((1 + k, 1), (1.5 + k, 0))]
    trace(f, x0, 92, scale, clock, 9.2, 'SCLK', 26)
    for row, (name, value) in enumerate((('MOSI', out), ('MISO', back))):
        y = 144 + 52 * row
        bits = [(value >> (7 - k)) & 1 for k in range(8)]
        trace(f, x0, y, scale, [(0, 0)] + [(0.6 + k, b) for k, b in enumerate(bits)] + [(8.6, 0)], 9.2, name, 26)
        for k, b in enumerate(bits):
            dot(f, x0 + (1 + k) * scale, y + (0 if b else 26), 3.5)
            text(f, x0 + (1.1 + k) * scale, y - 6, str(b), 'start', 't s')
    for k in range(8):
        line(f, x0 + (1 + k) * scale, 34, x0 + (1 + k) * scale, 226, 'w thin faint')
    text(f, 450, 254, 'both lines are sampled on each rising clock edge (dots), and change on the falling edge',
         'middle', 't s')
    sweep(f, 'cursor', x0, x0 + 9.2 * scale, 34, 226, 12)
    return f


def buck():
    f = Figure(900, 330, 'A buck converter switching: current through the inductor ramps up, then down')
    y, gy = 60, 160
    two(f, 'V', (80, y), (80, gy), 'V_in', side=-1)
    wire(f, (80, gy), (480, gy))
    wire(f, (80, y), (110, y))
    wire(f, (190, y), (230, y))
    dot(f, 210, y)
    two(f, 'Sch', (210, gy), (210, y), 'D', side=-1)
    two(f, 'L', (230, y), (330, y), 'L')
    wire(f, (330, y), (480, y))
    dot(f, 380, y)
    dot(f, 380, gy)
    two(f, 'C', (380, y), (380, gy), 'C', side=1)
    two(f, 'R', (480, y), (480, gy), 'load', side=1)
    ground(f, 280, gy)
    duty, period = 0.4, 3
    for cls, on in zip(phases(f, 2, period, [0, duty, 1]), (True, False)):
        begin(f, cls)
        two(f, 'SWon' if on else 'SW', (110, y), (190, y), 'switch')
        if on:
            flow(f, [(80, y), (330, y), (480, y), (480, gy), (80, gy), (80, y)])
            words = ('switch on: V_in drives current through L', 'into the load; the current ramps up')
        else:
            flow(f, [(230, y), (330, y), (480, y), (480, gy), (210, gy), (210, y), (230, y)])
            words = ('switch off: L keeps the current flowing,', 'round through the diode; it ramps down')
        for k, words_line in enumerate(words):
            text(f, 560, 96 + 18 * k, words_line, 'start', 't s')
        end(f)
    plot = Plot(f, 120, 210, 600, 80, (0, 3), (0, 1.3))
    plot.axes('t', 'i_L', [(k, '') for k in (1, 2, 3)], [(1, 'I_out')])
    ripple = []
    for k in range(3):
        ripple += [(k, 0.75), (k + duty, 1.25)]
    ripple.append((3, 0.75))
    plot.curve(ripple)
    plot.curve([(0, 1), (3, 1)], 'w thin dash')
    sweep(f, 'cursor', plot.X(0), plot.X(3), plot.y, plot.y + plot.h, 3 * period)
    return f


def battery():
    f = Figure(900, 250, 'Current drawn by a device that wakes for 10 ms each second, on a logarithmic scale')
    plot = Plot(f, 110, 30, 600, 180, (0, 3), (1e-6, 0.1), ylog=True)
    plot.axes('t (s)', None, [(1, '1'), (2, '2'), (3, '3')],
              [(1e-6, '1 µA'), (1e-5, '10 µA'), (1e-4, '100 µA'), (1e-3, '1 mA'), (1e-2, '10 mA'),
               (1e-1, '100 mA')], grid=True)
    samples = [(0, 5e-6)]
    for start in (0.5, 1.5, 2.5):
        samples += [(start, 5e-6), (start, 0.02), (start + 0.01, 0.02), (start + 0.01, 5e-6)]
    samples.append((3, 5e-6))
    plot.curve(samples)
    average = 0.01 * 0.02 + 0.99 * 5e-6
    plot.curve([(0, average), (3, average)], 'w thin dash')
    text(f, plot.X(3) + 8, plot.Y(average) + 4, f'average {average * 1e3:.3f} mA', 'start', 't s')
    text(f, plot.X(3) + 8, plot.Y(0.02) + 4, 'awake 20 mA', 'start', 't s')
    text(f, plot.X(3) + 8, plot.Y(5e-6) + 4, 'asleep 5 µA', 'start', 't s')
    return f


def impedance():
    f = Figure(900, 280, 'The impedance of real capacitors against frequency, with their self-resonance')
    plot = Plot(f, 110, 30, 560, 200, (1e3, 1e9), (1e-3, 1e3), xlog=True, ylog=True)
    plot.axes('f', '|Z|', [(10 ** k, label) for k, label in ((3, '1 kHz'), (6, '1 MHz'), (9, '1 GHz'))] +
              [(10 ** k, '') for k in (4, 5, 7, 8)],
              [(1e-3, '1 mΩ'), (1, '1 Ω'), (1e3, '1 kΩ')] + [(10 ** k, '') for k in (-2, -1, 1, 2)], grid=True)
    parts = (('100 nF', 100e-9, 1e-9, 0.02, 'w curve'), ('10 µF', 10e-6, 2e-9, 0.005, 'w curve dash'))
    for k, (name, c, esl, esr, cls) in enumerate(parts):
        def z(freq, c=c, esl=esl, esr=esr):
            w = 2 * math.pi * freq
            return math.hypot(esr, w * esl - 1 / (w * c))
        plot.curve(plot.points(z, samples=600), cls)
        f0 = 1 / (2 * math.pi * math.sqrt(esl * c))
        plot.mark(f0, z(f0))
        text(f, 700, 90 + 40 * k, f'{"solid" if k == 0 else "dashed"}: {name}', 'start', 't s')
        text(f, 700, 108 + 40 * k, f'ESL {esl * 1e9:g} nH, f_0 = {f0 / 1e6:.3g} MHz', 'start', 't s')
    text(f, 700, 190, 'below f_0 a capacitor,', 'start', 't s')
    text(f, 700, 208, 'above it an inductor', 'start', 't s')
    return f


def thermistor():
    f = Figure(900, 260, 'An NTC thermistor in a divider: its resistance and the voltage an ADC reads')
    r0, beta = 10e3, 3950

    def resistance(celsius):
        return r0 * math.exp(beta * (1 / (celsius + 273.15) - 1 / 298.15))
    left = Plot(f, 90, 40, 300, 170, (-20, 100), (100, 1e6), ylog=True)
    left.axes('°C', 'R', [(0, '0'), (25, '25'), (50, '50'), (100, '100')],
              [(1e3, '1 kΩ'), (1e4, '10 kΩ'), (1e5, '100 kΩ'), (1e6, '1 MΩ')], grid=True)
    left.curve(left.points(resistance, samples=200))
    left.mark(25, r0, '10 kΩ at 25 °C')
    right = Plot(f, 520, 40, 300, 170, (-20, 100), (0, 3.3))
    right.axes('°C', 'V_out', [(0, '0'), (25, '25'), (50, '50'), (100, '100')],
               [(0, '0'), (1.65, '1.65'), (3.3, '3.3 V')], grid=True)
    right.curve(lambda t: 3.3 * r0 / (r0 + resistance(t)))
    right.mark(25, 1.65, 'steepest near 25 °C', 'start', 8, 14)
    return f


def sections():
    return [
        ('gpio', 'Driving and reading pins', [
            p('A microcontroller pin set as an output is a push-pull stage: two transistors, one to the supply '
              'and one to ground, with only one on at a time. It can source current, out of the pin, or sink '
              'it, into the pin.'),
            fig(push_pull(), 'The same pin lighting one LED by sourcing current and the other by sinking it.'),
            p('Each pin can carry only a few milliamps, typically 4 to 20 mA, with a total limit for the whole '
              'chip; check the datasheet. An LED from a pin needs a series resistor:'),
            eq(r'R = \frac{V_{DD} - V_F}{I}', 'LED on a pin', '3.3 V, a red LED at 2.0 V and 5 mA: 260 Ω'),
            p('Anything heavier than an LED, such as a motor, relay or long LED strip, needs a transistor or a '
              f'driver chip between it and the pin ({link("04-semiconductors", "bjt", "Diodes and transistors")}).'),
            p('An open-drain output has only the transistor to ground. It can pull a line low or let go, and a '
              'pull-up resistor brings the line high. Several open-drain outputs can share one line without '
              'harm: it is low if any of them pulls it low, which is how I2C works.'),
            fig(open_drain(), 'Heavy line: high. An open-drain output never drives the line high, so two '
                'devices can never fight.'),
            eq(r'R_{pu} \ge \frac{V_{DD} - V_{OL}}{I_{OL}} \qquad t_{rise} \approx 2.2\,R_{pu}\,C',
               'Pull-up resistor', 'smaller is faster but draws more current while low'),
            p('A floating input, connected to nothing, reads at random and can draw extra current. Give every '
              'input a defined level: an internal or external pull-up or pull-down, typically 10 to 100 kΩ.'),
        ]),
        ('buttons', 'Buttons and debouncing', [
            p('A switch\'s contacts bounce for a millisecond or more as they close and open, so one press reads '
              'as many. Wire buttons from the pin to ground with a pull-up, so a press reads 0, and debounce in '
              'software: only accept a new level once it has been steady for several samples.'),
            fig(bounce(), 'The contact bounces on press and release; the debounced signal, sampled every '
                'millisecond, changes once each time, five milliseconds after the bouncing stops. The figure '
                'is computed with the same rule as the code below.'),
            code(DEBOUNCE),
            p('In hardware, an RC filter followed by a Schmitt-trigger input, such as a 74HC14, does the same. '
              'Choose $RC$ longer than the bounce, around 10 ms.'),
        ]),
        ('levels', 'Level shifting', [
            p('Logic at different voltages needs translating ('
              f'{link("06-digital", "levels", "Digital logic")}). For an open-drain bus such as I2C, one small '
              'N-MOSFET, typically a BSS138, with a pull-up on each side, shifts in both directions:'),
            fig(shifter(), 'The gate sits at 3.3 V. Whichever side pulls low, the other side follows it down; '
                'released, each side returns to its own supply through its own resistor.'),
            p('For push-pull signals such as SPI, use a buffer made for the job: a 74LVC1T45 for one direction '
              'chosen by a pin, or a 74AHCT125 to take 3.3 V logic up to 5 V. Going down, a divider of two '
              'resistors works for slow signals.'),
        ]),
        ('uart', 'UART', [
            p('A UART sends bytes one bit at a time with no clock line: both ends agree the speed, the baud rate, '
              'in advance. The line idles high; a start bit pulls it low, eight data bits follow, least '
              'significant first, and a stop bit returns it high.'),
            fig(uart(), 'The receiver times everything from the falling edge of the start bit, then samples each '
                'bit in its middle (dots).'),
            eq(r't_{bit} = \frac{1}{\text{baud}} \qquad \text{bytes per second} = \frac{\text{baud}}{10} '
               r'\qquad \text{divisor} = \frac{f_{clk}}{16 \cdot \text{baud}}', 'UART timing',
               'with 8 data bits, no parity and 1 stop bit, written 8N1'),
            p('By the stop bit, a receiver running at the wrong speed has drifted by nine and a half bits\' '
              'worth of error, and it must still land within the stop bit: the two ends must agree to within '
              'about 2% together. The RC oscillators inside many microcontrollers are not that accurate; use '
              'a crystal for reliable serial.'),
            p('TX of one device goes to RX of the other, with grounds joined. Logic-level UART is not RS-232, '
              'which swings to ±12 V and is inverted, and must never be connected directly.'),
        ]),
        ('i2c', 'I2C', [
            p('I2C connects many devices on two open-drain lines, SDA for data and SCL for the clock, each with '
              'a pull-up. Each device has a 7-bit address. The controller starts a transfer by pulling SDA low '
              'while SCL is high, sends the address and a read or write bit, and the addressed device pulls SDA '
              'low for one clock to acknowledge.'),
            fig(i2c(), 'A start, the address 0x3C with a write bit, an acknowledge, one data byte, a second '
                'acknowledge and a stop. Bits go most significant first.'),
            eq(r'R_{min} = \frac{V_{DD} - V_{OL}}{I_{OL}} \qquad R_{max} = \frac{t_r}{0.8473\,C_b}', 'I2C pull-ups',
               '$C_b$ is the bus capacitance; $t_r$ the allowed rise time, from 30% to 70%'),
            table(['Mode', 'Clock', 'Rise time $t_r$', 'Sink current $I_{OL}$', 'Bus capacitance'],
                  ['Standard', '100 kHz', '1000 ns', '3 mA', '400 pF'],
                  ['Fast', '400 kHz', '300 ns', '3 mA', '400 pF'],
                  ['Fast-mode Plus', '1 MHz', '120 ns', '20 mA', '550 pF']),
            p(f'At 3.3 V in fast mode with 100 pF of bus: $R_{{min}} = 2.9/0.003 = 967$ Ω and $R_{{max}} = '
              f'300\\,\\mathrm{{ns}}/(0.8473 \\times 100\\,\\mathrm{{pF}}) = {300e-9 / (0.8473 * 100e-12) / 1e3:.2f}$ '
              f'kΩ, so 2.2 kΩ is a good choice. Breakout boards often carry their own pull-ups: several in '
              f'parallel can fall below $R_{{min}}$.'),
            p('A device that stops answering mid-transfer can hold SDA low. Recover by clocking SCL nine times '
              'by hand until SDA is released, then sending a stop.'),
        ]),
        ('spi', 'SPI', [
            p('SPI uses a clock, SCLK, a line each way, MOSI and MISO, and a chip select per device, CS, '
              'active low. It is push-pull and has no addresses or acknowledgements, so it runs fast, tens of '
              'MHz. Every clock shifts one bit out and one bit in: a transfer is always an exchange.'),
            fig(spi(), 'Mode 0: the clock idles low, and both ends sample on the rising edge.'),
            table(['Mode', 'CPOL: clock idles', 'CPHA: data sampled on'],
                  ['0', 'low', 'first edge, rising'], ['1', 'low', 'second edge, falling'],
                  ['2', 'high', 'first edge, falling'], ['3', 'high', 'second edge, rising']),
            p('The mode, bit order and maximum clock are in each device\'s datasheet. Pull CS high with a '
              'resistor so devices stay deselected while the microcontroller boots.'),
        ]),
        ('power', 'Regulators', [
            p('A linear regulator drops the difference between input and output across a transistor, which '
              'turns it into heat. A low-dropout regulator, LDO, needs only a few hundred millivolts of '
              'headroom:'),
            eq(r'P = (V_{in} - V_{out})\,I \qquad \eta = \frac{V_{out}}{V_{in}} \qquad V_{in} \ge V_{out} + '
               r'V_{dropout}', 'Linear regulator'),
            p('From 12 V to 3.3 V at 1 A, a linear regulator turns 8.7 W into heat and is 28% efficient. A '
              'switching regulator chops the input and smooths it with an inductor and a capacitor, at 85 to '
              '95% efficiency.'),
            fig(buck(), 'With the switch on for 40% of each cycle, the inductor current ramps up and down around '
                'the load current, and the output settles at 40% of the input.'),
            eq(r'V_{out} = D\,V_{in} \qquad \Delta I_L = \frac{(V_{in} - V_{out})\,D}{f_s\,L}', 'Buck converter',
               '$D$ is the fraction of each cycle the switch is on'),
            eq(r'V_{out} = \frac{V_{in}}{1 - D}', 'Boost converter'),
            p('A switcher\'s layout matters as much as its parts: keep the loop through the switch, diode and '
              'input capacitor as small as possible, as the module or chip datasheet shows. Use a linear '
              'regulator after a switcher to feed noise-sensitive analog circuits.'),
        ]),
        ('battery', 'Batteries and sleep', [
            p('A battery-powered device spends most of its time asleep. Its battery life depends on the average '
              'current, which a short burst of activity can dominate:'),
            eq(r'I_{avg} = D\,I_{active} + (1 - D)\,I_{sleep} \qquad t = \frac{C}{I_{avg}}', 'Battery life with sleep',
               '$D$ is the fraction of time awake; $C$ the capacity in mAh'),
            fig(battery(), 'Awake at 20 mA for 10 ms each second and asleep at 5 µA otherwise: an average of '
                '0.205 mA, nearly all of it from the bursts.'),
            p(f'A CR2032 coin cell holds about 225 mAh, so it lasts $225/0.205 \\approx {225 / 0.205:.0f}$ hours, '
              f'{225 / 0.205 / 24:.0f} days. Waking every 10 s instead gives {225 / (0.001 * 20 + 0.999 * 0.005) / 24:.0f} days. '
              'Coin cells also cannot deliver large pulses: add a capacitor across them for radio bursts.'),
            table(['Battery', 'Voltage', 'Capacity', 'Notes'],
                  ['CR2032 lithium coin', '3.0 V', '225 mAh', 'a few mA at most'],
                  ['AA alkaline', '1.5 V, falling to 1.0', '2000–3000 mAh', 'less at high current'],
                  ['AA NiMH', '1.2 V', '2000 mAh', 'rechargeable'],
                  ['Li-ion or LiPo cell', '3.7 V, 4.2 full, 3.0 empty', 'varies', 'needs a protected charger']),
            p('Lithium cells must be charged by a proper charger IC, constant current then constant voltage to '
              '4.2 V, and protected against short circuits and discharge below about 3 V.'),
        ]),
        ('decoupling', 'Decoupling and clocks', [
            p('Every chip draws its supply current in short spikes as its logic switches. A capacitor beside each '
              'supply pin supplies the spikes locally, so they do not travel along the supply track. Real '
              'capacitors have inductance in their leads and pads, so each works only up to its resonant '
              'frequency:'),
            eq(r'\left| Z \right| = \sqrt{\mathrm{ESR}^2 + \left( 2\pi f L - \frac{1}{2\pi f C} \right)^2} \qquad f_0 = '
               r'\frac{1}{2\pi\sqrt{L C}}', 'Capacitor self-resonance'),
            fig(impedance(), 'A small capacitor covers high frequencies, a large one low frequencies. The usual '
                'recipe: 100 nF at every supply pin, as close as possible, plus 10 µF per chip or board.'),
            p('A crystal needs two load capacitors to oscillate at its marked frequency. The crystal\'s datasheet '
              'gives its load capacitance $C_L$; the pins and tracks add a stray few picofarads:'),
            eq(r'C_1 = C_2 = 2\,(C_L - C_{stray})', 'Crystal load capacitors',
               '$C_L = 12.5$ pF with 4 pF stray: 17 pF, so fit 18 pF'),
        ]),
        ('protection', 'Protecting inputs', [
            p('Inputs connected to the outside world meet static, wrong voltages and reversed power. Each pin has '
              'clamp diodes to its supply and ground, which survive only a few milliamps; a series resistor '
              'limits the current into them:'),
            eq(r'R \ge \frac{V_{in,max} - V_{DD} - 0.3}{I_{clamp}}', 'Input series resistor',
               '12 V into a 3.3 V pin with 1 mA allowed: at least 8.4 kΩ'),
            table(['Threat', 'Protection'],
                  ['static discharge on a connector', 'a TVS diode to ground beside the connector'],
                  ['reversed power', 'a series Schottky diode, or a P-MOSFET for less drop'],
                  ['overcurrent', 'a fuse or a resettable PTC fuse'],
                  ['inductive loads, relays, motors',
                   f'a flyback diode across the coil ({link("03-ac", "inductors", "Capacitors, inductors and AC")})'],
                  ['long cables to sensors', 'series resistors and small capacitors at the input']),
        ]),
        ('sensors', 'Reading sensors', [
            p('Many sensors change resistance, read through a voltage divider into an ADC '
              f'({link("02-dc", "dividers", "DC circuits and their laws")}). A thermistor\'s resistance falls '
              'steeply and '
              'non-linearly with temperature; the beta equation converts it back:'),
            eq(r'\frac{1}{T} = \frac{1}{T_0} + \frac{1}{\beta} \ln\frac{R}{R_0}', 'Thermistor',
               'temperatures in kelvin; for a common part $R_0 = 10$ kΩ at $T_0 = 298.15$ K and $\\beta = 3950$ K'),
            fig(thermistor(), 'Left: resistance against temperature, on a log scale. Right: with the thermistor '
                'from 3.3 V to the ADC pin and 10 kΩ from the pin to ground, the reading rises with temperature, '
                'most steeply near 25 °C, where the two resistances match.'),
            p('An ADC input charges a small sampling capacitor each conversion. A source impedance above about '
              '10 kΩ cannot charge it in time and reads low: add a 100 nF capacitor from the ADC pin to '
              'ground, or a slower sampling time. Measure a battery through a divider of large resistors, '
              'with that capacitor, so it drains only microamps.'),
            note('Read more: <em>Lessons in Electric Circuits</em>, volumes III and IV, in DOCS → CIRCUITS '
                 'LIBRARY; the Embedded Rust Book, as embedded-book in DOCS → RUST BOOK; and the Tildagon '
                 'hardware reference in DOCS → PCB AND BADGES, a worked example of all of this on a real board. '
                 'Always check the datasheet of the part in hand: it is the final word on its limits.'),
        ]),
    ]
