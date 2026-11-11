import inspect
import math
import struct

from draw import (Figure, Plot, arrow, begin, chip, circle, dimension, dot, end, flow, ground, line, path, phases,
                  poly, rail, rect, sweep, terminal, text, trace, two, wire)
from page import code, eq, fig, link, note, p, table

NAME = '11-badges'
TITLE = 'Badges and projects'
LEDE = ('Electronic badges and other boards made for fun: what a badge is built from, board art, add-on '
        'connectors and Tildagon hexpansions, LED tricks, key matrices, touch pads and charging a lithium '
        'cell, with project ideas.')


def block(f, x, y, w, h, name, sub=None):
    rect(f, x, y, w, h, 'w thin', 4)
    text(f, x + w / 2, y + h / 2 + (-2 if sub else 4), name)
    if sub:
        text(f, x + w / 2, y + h / 2 + 14, sub, 'middle', 't s')


def anatomy():
    f = Figure(900, 280, 'The parts of a typical electronic badge and how they connect')
    block(f, 40, 40, 110, 46, 'USB-C', 'power and data')
    block(f, 200, 40, 120, 46, 'charger', 'CC/CV')
    block(f, 200, 160, 120, 46, 'LiPo cell', '3.0 to 4.2 V')
    block(f, 370, 100, 130, 46, 'regulator', '3.3 V')
    block(f, 560, 60, 140, 140, 'microcontroller', 'Wi-Fi or radio')
    block(f, 560, 230, 140, 36, 'add-on ports')
    for k, (name, bus) in enumerate((('LEDs', 'data'), ('buttons', 'GPIO'), ('display', 'SPI'), ('sensors', 'I2C'))):
        y = 56 + 40 * k
        block(f, 770, y, 110, 32, name)
        line(f, 700, y + 16, 770, y + 16, 'w thin')
        text(f, 735, y + 11, bus, 'middle', 't s')
    wire(f, (630, 200), (630, 230), cls='w thin')
    wire(f, (95, 40), (95, 20), (630, 20), (630, 60), cls='w thin dash')
    text(f, 360, 14, 'USB data', 'middle', 't s')
    for points in ([(150, 63), (200, 63)], [(260, 86), (260, 160)], [(320, 183), (435, 183), (435, 146)],
                   [(500, 123), (560, 123)]):
        wire(f, *points)
        flow(f, points, 1.4)
    text(f, 175, 56, '5 V', 'middle', 't s')
    text(f, 530, 116, '3.3 V', 'middle', 't s')
    return f


ART = (('mask on copper', 'shiny, a light', 'tint of the mask', True, True, False),
       ('mask on board', 'matte, a darker', 'tint of the mask', False, True, False),
       ('bare copper, ENIG', 'gold, flat and', 'mirror-like', True, False, False),
       ('silkscreen', 'printed ink,', 'usually white', False, True, True),
       ('bare FR-4', 'translucent: it', 'glows when lit behind', False, False, False))


def art():
    f = Figure(900, 210, 'How copper, solder mask, silkscreen and bare board give a badge its look')
    rect(f, 60, 110, 780, 30, 'shade')
    rect(f, 60, 110, 780, 30, 'w thin faint')
    for k, (name, look, more, copper, mask, silk) in enumerate(ART):
        x0, x1 = 60 + 156 * k, 216 + 156 * k
        if mask and copper:
            shape = poly([(x0, 110), (x0, 106), (x0 + 10, 106), (x0 + 10, 100), (x1 - 10, 100), (x1 - 10, 106),
                          (x1, 106), (x1, 110)]) + ' Z'
            path(f, shape, 'shade2')
            path(f, shape, 'w thin dim')
        elif mask:
            rect(f, x0, 106, x1 - x0, 4, 'shade2')
            rect(f, x0, 106, x1 - x0, 4, 'w thin dim')
        if copper:
            rect(f, x0 + 14, 104, x1 - x0 - 28, 6 if mask else 5, 'fill')
            if not mask:
                line(f, x0 + 14, 101.5, x1 - 14, 101.5, 'w thin')
        if silk:
            rect(f, x0 + 40, 102, x1 - x0 - 80, 4, 'fill')
        if not (copper or mask):
            for x in (x0 + 48, x0 + 78, x0 + 108):
                arrow(f, x, 154, x, 84, 'w thin dim', 6)
        text(f, (x0 + x1) / 2, 70, name)
        text(f, (x0 + x1) / 2, 172, look, 'middle', 't s')
        text(f, (x0 + x1) / 2, 188, more, 'middle', 't s')
    return f


SAO = (('VCC', 'GND'), ('SDA', 'SCL'), ('GPIO1', 'GPIO2'))


def sao():
    f = Figure(900, 240, 'The Simple Add-On connector: power, an I2C bus and two GPIO pins')
    pitch, x0, y0 = 50.8, 150, 180
    rect(f, x0 - 34, y0 - 2 * pitch - 34, pitch + 68, 2 * pitch + 68, 'w thin dim', 6)
    for row, names in enumerate(SAO):
        for col, name in enumerate(names):
            number, x, y = 2 * row + col + 1, x0 + col * pitch, y0 - row * pitch
            if number == 1:
                rect(f, x - 10, y - 10, 20, 20, 'fill')
            else:
                circle(f, x, y, 10, 'fill')
            circle(f, x, y, 4.5, 'hollow')
            if col:
                text(f, x + 46, y + 5, f'{number}  {name}', 'start')
            else:
                text(f, x - 46, y + 5, f'{name}  {number}', 'end')
    text(f, x0 + pitch / 2, 30, 'HEADER, FROM ABOVE', 'middle', 't head')
    names = ['3V3', 'GND', 'SDA', 'SCL', 'GPIO1', 'GPIO2']
    badge = chip(f, 450, 40, 130, 160, 'badge', right=names, pitch=24)
    addon = chip(f, 740, 40, 140, 160, 'add-on', left=names, pitch=24)
    for name in names:
        wire(f, badge[name], addon[name], cls='w thin')
    text(f, 660, 30, '2 × 3 pins, 2.54 mm apart', 'middle', 't s')
    return f


def hexpansion():
    f = Figure(900, 340, 'A Tildagon hexpansion drawn to scale, and how the badge detects one')
    scale, cx, cy = 6, 300, 170
    r = 32 / math.sqrt(3)

    def at(x, y):
        return cx + x * scale, cy + y * scale
    outline = [(0, -r), (16, -r / 2), (16, r / 2), (0, r), (-16, r / 2), (-16, 6), (-11.25, 6), (-11.25, 4.6),
               (-17.75, 4.6), (-17.75, -4.6), (-11.25, -4.6), (-11.25, -6), (-16, -6), (-16, -r / 2)]
    shape = poly([at(x, y) for x, y in outline]) + ' Z'
    path(f, shape, 'shade')
    path(f, shape)
    for k in range(10):
        x, y = at(-17.25, (k - 4.5) * 0.8 - 0.25)
        rect(f, x, y, 3 * scale, 0.5 * scale, 'fill')
    for y in (-12.5, 12.5):
        circle(f, *at(-3.5, y), 1.1 * scale)
        circle(f, *at(-3.5, y), 2 * scale, 'w thin dim')
    line(f, cx, 22, cx, 290, 'w thin dash')
    text(f, cx, 14, 'badge edge', 'middle', 't s')
    for sign in (-1, 1):
        line(f, *at(0, sign * r), *at(11.2, sign * (r + 0.35 * r)), 'w thin dim')
    text(f, *at(12, -r - 4.5), 'outside: any shape within the lines', 'start', 't s')
    front = at(-17.75, 0)[0]
    line(f, front, 44, front, 140, 'w thin faint')
    dimension(f, front, 44, cx, 44, '17.75 mm', (front + (cx - front) / 2, 38))
    dimension(f, 176, at(0, -4.6)[1], 176, at(0, 4.6)[1], '9.2 mm', (170, cy + 4), 'end')
    dimension(f, *at(-16, 22), *at(16, 22), '32 mm', (cx, at(0, 22)[1] + 16))
    for y in (-12.5, 12.5):
        line(f, at(-3.5, y)[0] + 8, at(0, y)[1], 336, at(0, y)[1], 'w thin faint')
    dimension(f, 332, at(0, -12.5)[1], 332, at(0, 12.5)[1], '25 mm', (338, cy + 4), 'start')
    # The detect pin, on the right.
    rail(f, 560, 80, '3.3 V')
    two(f, 'R', (560, 80), (560, 140), 'weak pull-up', side=-1)
    wire(f, (560, 140), (700, 140))
    wire(f, (560, 140), (560, 196))
    dot(f, 560, 140)
    terminal(f, 560, 200)
    text(f, 560, 222, 'the badge reads Detect', 'middle', 't s')
    line(f, 700, 70, 700, 230, 'w thin dash')
    terminal(f, 700, 140)
    text(f, 640, 62, 'BADGE', 'middle', 't head')
    text(f, 770, 62, 'HEXPANSION', 'middle', 't head')
    states = ((1, 'An empty port: the weak pull-up holds Detect high,', "and the port's 3.3 V supply stays off."),
              (0, 'A hexpansion joins Detect to ground: the badge reads 0', "and switches on the port's 3.3 V."))
    for cls, (level, *words) in zip(phases(f, 2, 8), states):
        begin(f, cls)
        text(f, 630, 132, f'Detect = {level}', 'middle', 't b')
        if not level:
            wire(f, (703, 140), (780, 140), (780, 160))
            ground(f, 780, 160)
            flow(f, [(560, 80), (560, 140), (780, 140), (780, 170)])
        for k, words_line in enumerate(words):
            text(f, 680, 270 + 18 * k, words_line, 'middle', 't s')
        end(f)
    return f


HEXPANSION_PINS = (('1', 'GND', '11', 'GND'), ('2', 'low speed 1', '12', 'high speed 1'),
                   ('3', 'low speed 2', '13', 'high speed 2'), ('4', 'I2C SDA', '14', 'GND'),
                   ('5', 'I2C SCL', '15', '+3V3'), ('6', 'Detect', '16', '+3V3'),
                   ('7', 'low speed 3', '17', 'GND'), ('8', 'low speed 4', '18', 'high speed 3'),
                   ('9', 'low speed 5', '19', 'high speed 4'), ('10', 'GND', '20', 'GND'))


def header(vid, pid, name, unique=0, offset=32, page=32, size=8192):
    """A hexpansion EEPROM header: 32 bytes, little-endian, the last one a checksum."""
    data = b'THEX2024' + struct.pack('<HHIHHH', offset, page, size, vid, pid, unique)
    data += name.encode('ascii')[:9].ljust(9, b'\0')
    checksum = 0x55
    for byte in data[1:]:
        checksum ^= byte
    return data + bytes([checksum])


EXAMPLE = b'THEX2024\x40\x00\x40\x00\x00\x00\x01\x00\x55\xf0\x01\x00\x02\x00EXAMPLE\x00\x00\xeb'

LEDS = (('A', 'B', 280), ('B', 'A', 340), ('B', 'C', 440), ('C', 'B', 500), ('A', 'C', 580), ('C', 'A', 640))


def charlieplex():
    f = Figure(900, 280, 'Charlieplexing: three pins lighting six LEDs, one at a time')
    ys, ends = {'A': 60, 'B': 120, 'C': 180}, {'A': 660, 'B': 520, 'C': 660}
    for pin, y in ys.items():
        terminal(f, 106, y)
        text(f, 92, y + 5, pin, 'end')
        two(f, 'R', (110, y), (180, y))
        wire(f, (180, y), (ends[pin], y))
    for k, (anode, cathode, x) in enumerate(LEDS):
        two(f, 'LED', (x, ys[anode]), (x, ys[cathode]))
        dot(f, x, ys[anode])
        dot(f, x, ys[cathode])
        down = ys[cathode] > ys[anode]
        middle = (ys[anode] + ys[cathode]) / 2
        text(f, x - 22 if down else x + 22, middle + 4, f'D{k + 1}', 'end' if down else 'start', 't s')
    text(f, 450, 228, 'H: driven high; L: driven low; Z: an input, floating', 'middle', 't s')
    for k, cls in enumerate(phases(f, 6, 9)):
        anode, cathode, x = LEDS[k]
        other = next(pin for pin in ys if pin not in (anode, cathode))
        begin(f, cls)
        for pin, y in ys.items():
            text(f, 48, y + 5, 'H' if pin == anode else 'L' if pin == cathode else 'Z', 'middle', 't b')
        flow(f, [(106, ys[anode]), (x, ys[anode]), (x, ys[cathode]), (106, ys[cathode])])
        circle(f, x, (ys[anode] + ys[cathode]) / 2, 17, 'w thin')
        text(f, 450, 254, f'D{k + 1} lights: {anode} high, {cathode} low, {other} floating', 'middle', 't s')
        end(f)
    return f


COLOURS = ('red', 'green', 'blue')


def addressable():
    f = Figure(900, 300, 'Addressable LEDs: how bits are sent, and how each LED takes its own colour')
    for x0, high, name in ((140, 0.4, '0 bit'), (480, 0.8, '1 bit')):
        trace(f, x0, 40, 160, [(0, 1), (high, 0)], 1.25, name, 26)
        text(f, x0 + high * 80, 32, f'{high:g} µs', 'middle', 't s')
        text(f, x0 + (high + 1.25) * 80, 84, f'{1.25 - high:g} µs', 'middle', 't s')
    text(f, 790, 50, '1.25 µs a bit,', 'middle', 't s')
    text(f, 790, 66, '24 bits a colour', 'middle', 't s')
    leds = (230, 470, 690)
    terminal(f, 50, 175)
    wire(f, (53, 175), (230, 175))
    for k, x in enumerate(leds):
        rect(f, x, 150, 100, 50)
        text(f, x + 50, 170, f'LED {k + 1}')
        wire(f, (x + 100, 175), (leds[k + 1] if k < 2 else 890, 175))
    text(f, 50, 196, 'data in', 'middle', 't s')
    text(f, 890, 196, 'to more LEDs', 'end', 't s')
    captions = ('The microcontroller sends one 24-bit colour for each LED, back to back.',
                'The first LED keeps the first 24 bits it receives and passes the rest on.',
                'Each LED does the same, so the second keeps the next colour, and so on.',
                'A pause of at least 50 µs, 280 µs for newer parts, and every LED shows its colour.')
    for k, cls in enumerate(phases(f, 4, 8)):
        begin(f, cls)
        if k < 3:
            stop = leds[k]
            for i, colour in enumerate(COLOURS[k:]):
                rect(f, stop - 8 - 52 * (i + 1), 165, 48, 20, 'w thin hollow')
                text(f, stop - 8 - 52 * (i + 1) + 24, 179, colour, 'middle', 't s')
        for i in range(min(k, 3)):
            state = f'shows {COLOURS[i]}' if k == 3 else f'{COLOURS[i]} stored'
            text(f, leds[i] + 50, 188, state, 'middle', 't s')
        text(f, 450, 250, captions[k], 'middle', 't s')
        end(f)
    return f


ROWS, COLUMNS = (90, 170, 250), (260, 400, 540)
PRESSED = {(0, 0), (0, 1), (1, 0)}


def columns_low(pressed, row, diodes=True):
    """The columns that read low while one row is driven low. Current runs from a column through
    a pressed key into its row; without a diode it can also run back out of a row into a column."""
    def reaches(column):
        seen, todo = set(), [('column', column)]
        while todo:
            node = todo.pop()
            if node == ('row', row):
                return True
            if node in seen:
                continue
            seen.add(node)
            kind, index = node
            for r, c in pressed:
                if kind == 'column' and c == index:
                    todo.append(('row', r))
                elif kind == 'row' and r == index and not diodes:
                    todo.append(('column', c))
        return False
    return [c for c in range(len(COLUMNS)) if reaches(c)]


def matrix():
    f = Figure(900, 390, 'Scanning a key matrix one row at a time, with a diode at every key')
    for i, y in enumerate(ROWS):
        terminal(f, 140, y)
        text(f, 126, y + 5, f'R{i}', 'end')
        wire(f, (143, y), (590, y))
    for j, x in enumerate(COLUMNS):
        wire(f, (x, ROWS[0] - 46), (x, 287))
        terminal(f, x, 290)
        text(f, x, 312, f'C{j}')
        for i, y in enumerate(ROWS):
            dot(f, x, y - 46)
            wire(f, (x, y - 46), (x + 30, y - 46))
            two(f, 'SWon' if (i, j) in PRESSED else 'SW', (x + 30, y - 46), (x + 30, y - 20))
            two(f, 'D', (x + 30, y - 20), (x + 30, y))
            dot(f, x + 30, y)
    text(f, 210, 334, 'reads', 'end', 't s')
    captions = (('Row 0 is driven low: keys 0,0 and 0,1 pull columns 0 and 1 low.', ''),
                ('Row 1 is driven low: key 1,0 pulls column 0 low. Without diodes, current from column 1 could run',
                 'through keys 0,1, 0,0 and 1,0 into row 1, and key 1,1 would read as pressed: a ghost.'),
                ('Row 2 is driven low: no key in it is pressed, so every column reads 1.', ''))
    for r, cls in enumerate(phases(f, 3, 9)):
        begin(f, cls)
        for i, y in enumerate(ROWS):
            text(f, 80, y + 4, 'low' if i == r else 'off', 'middle', 't s')
        low = columns_low(PRESSED, r)
        for c, x in enumerate(COLUMNS):
            text(f, x, 336, '0' if c in low else '1', 'middle', 't b')
            if (r, c) in PRESSED:
                flow(f, [(x, 287), (x, ROWS[r] - 46), (x + 30, ROWS[r] - 46), (x + 30, ROWS[r]), (143, ROWS[r])])
        if r == 1:
            x, y = COLUMNS[0] + 30, ROWS[0] - 10
            line(f, x + 8, y - 6, x + 20, y + 6, 'w thin')
            line(f, x + 8, y + 6, x + 20, y - 6, 'w thin')
            text(f, x + 26, y + 4, 'blocks it', 'start', 't s')
        for k, words in enumerate(captions[r]):
            text(f, 450, 356 + 18 * k, words, 'middle', 't s')
        end(f)
    return f


SCAN = '''
/* Rows are outputs, columns inputs with pull-ups; each key's diode
   points from its column to its row. */
void scan(uint8_t pressed[ROWS][COLS])
{
    for (int r = 0; r < ROWS; r++) {
        row_low(r);                     /* the other rows float */
        delay_us(5);                    /* let the lines settle */
        for (int c = 0; c < COLS; c++)
            pressed[r][c] = !column_read(c);
        row_float(r);
    }
}
'''


def touch():
    f = Figure(900, 270, 'Charging a touch pad through 1 MΩ, with and without a finger on it')
    plot = Plot(f, 110, 30, 520, 190, (0, 40), (0, 3.6))
    plot.axes('t', 'v', [(k, f'{k} µs' if k else '0') for k in range(0, 41, 10)], [(1.65, '1.65'), (3.3, '3.3 V')],
              grid=True)
    plot.curve([(0, 1.65), (40, 1.65)], 'w thin dots')
    times = []
    for k, (farads, cls, words) in enumerate(((10e-12, 'w curve', 'pad alone, 10 pF'),
                                              (15e-12, 'w curve dash', 'with a finger, 15 pF'))):
        tau = 1e6 * farads * 1e6
        plot.curve(lambda t: 3.3 * (1 - math.exp(-t / tau)), cls)
        times.append(tau * math.log(2))
        plot.mark(times[-1], 1.65)
        line(f, 670, 70 + 26 * k, 710, 70 + 26 * k, cls)
        text(f, 720, 74 + 26 * k, words, 'start', 't s')
    line(f, 670, 122, 710, 122, 'w thin dots')
    text(f, 720, 126, 'input threshold', 'start', 't s')
    y = plot.Y(1.65) + 36
    for t in times:
        line(f, plot.X(t), plot.Y(1.65) + 5, plot.X(t), y, 'w thin faint')
    dimension(f, plot.X(times[0]), y, plot.X(times[1]), y, 'Δt', (plot.X(sum(times) / 2), y + 16))
    sweep(f, 'cursor', plot.X(0), plot.X(40), plot.y, plot.y + plot.h, 4)
    return f, times


DONE = 50 + 30 * math.log(10)


def charge(t):
    """An illustrative 1C charge at t minutes: (cell voltage, current as a fraction of C)."""
    if t < 50:
        return 3.0 + 0.6 * (1 - math.exp(-t / 4)) + 0.6 * (t / 50) ** 1.6, 1.0
    if t < DONE:
        return 4.2, math.exp(-(t - 50) / 30)
    return 4.2, 0.0


def charging():
    f = Figure(900, 330, 'Charging a lithium cell: constant current, then constant voltage')
    ticks = [(t, f'{t} min' if t else '0') for t in (0, 30, 60, 90, 120)]
    volts = Plot(f, 110, 30, 560, 110, (0, 140), (3.0, 4.4))
    volts.axes(None, 'V', [(t, '') for t, _ in ticks], [(3.0, '3.0'), (3.6, '3.6'), (4.2, '4.2 V')], grid=True)
    volts.curve(lambda t: charge(t)[0])
    amps = Plot(f, 110, 190, 560, 100, (0, 140), (0, 1.25))
    amps.axes('t', 'I', ticks, [(0.1, 'C/10'), (1, '1C')], grid=True)
    amps.curve([(t / 4, charge(t / 4)[1]) for t in range(int(DONE * 4) + 1)] + [(DONE, 0), (140, 0)])
    for t in (50, DONE):
        line(f, volts.X(t), 30, volts.X(t), 290, 'w thin dash')
    text(f, volts.X(25), amps.Y(1) - 8, 'constant current', 'middle', 't s')
    text(f, volts.X((50 + DONE) / 2), volts.Y(4.2) - 8, 'constant voltage', 'middle', 't s')
    text(f, volts.X(DONE) + 6, amps.Y(0.5), 'below C/10:', 'start', 't s')
    text(f, volts.X(DONE) + 6, amps.Y(0.5) + 14, 'charged', 'start', 't s')
    sweep(f, 'cursor', volts.X(0), volts.X(140), 30, 290, 8)
    return f


def sections():
    touch_figure, (alone, touched) = touch()
    assert header(0xF055, 0x0001, 'EXAMPLE', 2, 64, 64, 0x10000) == EXAMPLE
    assert columns_low(PRESSED, 1) == [0] and columns_low(PRESSED, 1, diodes=False) == [0, 1]
    return [
        ('anatomy', 'What a badge is made of', [
            p('A badge is a board worn on a lanyard at a conference or festival: a name tag, an artwork and a '
              'small computer in one. Most share a design: a microcontroller with Wi-Fi or a radio, LEDs, '
              'buttons, often a display, a battery with its charger, and connectors for add-ons.'),
            fig(anatomy(), 'Moving dots show power: USB charges the cell, and the cell feeds the regulator that '
                'powers everything else at 3.3 V.'),
            table(['Badge', 'Inside', 'In the docs'],
                  ['Tildagon, EMF Camp 2024', 'ESP32-S3, a round GC9A01 LCD, six buttons, LEDs, a 2000 mAh LiPo '
                   'cell and six hexpansion ports', 'DOCS → PCB AND BADGES, five Tildagon sets'],
                  ['Communicator, Hackaday Supercon 2025', 'ESP32-S3-WROOM-1, an SX1262 LoRa radio, an LCD, a '
                   'keyboard scanned by a TCA8418, an MCP73831 charger, an AP2112 regulator and SAO ports',
                   'the schematic'],
                  ['Vectorscope, Hackaday Supercon 2023', 'a round display and add-on ports', 'the board layers']),
            p('Power sets most of a badge\'s design ('
              f'{link("09-interfaces", "battery", "Batteries and sleep")}): a CR2032 coin cell lasts days with a '
              'few LEDs and deep sleep, two AAA cells give more current, and a LiPo cell with a charger runs '
              'displays and radios for a day.'),
        ]),
        ('art', 'Board art', [
            p('Badges use the board itself as the artwork. Each layer is a colour to paint with: copper under '
              'the mask shows a lighter shade of the mask colour, bare board under it a darker one; exposed '
              'copper is plated gold with ENIG; silkscreen prints on top; and bare FR-4, with neither copper '
              'nor mask, lets light through.'),
            fig(art(), 'A cross-section of the five looks. Light arrows: an LED behind bare FR-4 makes it glow.'),
            p('Draw the art in a vector program, import it as copper, mask or silkscreen layers in the PCB '
              'program, and keep artwork copper away from the circuit\'s nets. Reverse-mount LEDs, soldered on '
              'the back and shining through a hole, light the board from behind. Mask comes in green, black, '
              'white, red, blue, yellow and purple; choose ENIG for any exposed copper art, since it stays '
              'flat and does not tarnish.'),
        ]),
        ('sao', 'Simple add-ons', [
            p('The SAO connector, born on DEF CON badges, lets anyone build a small board that plugs into any '
              'badge that has one. Version 2 has six pins: 3.3 V power, ground, an I2C bus and two GPIO pins. '
              'The Communicator\'s schematic labels it Simple_Addon_v2.'),
            fig(sao(), 'Left: the badge\'s header from above, pin 1 square. Right: what each pin carries; an add-on '
                f'can be as simple as an LED on GPIO1, or an I2C chip ({link("09-interfaces", "i2c", "I2C")}).'),
            p('An add-on with an I2C chip must use an address no other device on the badge uses. Keep it light '
              'and low power: it hangs on the header and runs from the badge\'s battery.'),
        ]),
        ('hexpansion', 'Tildagon hexpansions', [
            p('The Tildagon has six hexpansion ports, edge connectors that take hexagonal add-on boards. Each '
              'port provides 3.3 V at up to 600 mA, its own I2C bus, four fast GPIO pins wired to the ESP32-S3 '
              'and five slower ones on a GPIO expander that can also drive LEDs.'),
            fig(hexpansion(), 'Left: the standard shape, 32 mm across the flats, with its tab of ten pads a side; '
                'the badge is to the left of its edge. Right: the Detect pin tells the badge a hexpansion is '
                'in, and switches on its power.'),
            table(['Pin', 'Bottom side', 'Pin', 'Top side'], *HEXPANSION_PINS),
            p('The rules from the hexpansion documentation:'),
            table(['Rule', 'Why'],
                  ['exactly 1 mm thick, ±0.1 mm', 'the connector grips a 1 mm board'],
                  ['ENIG finish, never HASL', 'the pads must be flat to make contact'],
                  ['the tab 9.2 mm wide and 6.5 mm long, with no panel tabs near it', 'it must slide into the '
                   'connector; mounting holes, if used, are 25 mm apart and 14.25 mm from the tab\'s front'],
                  ['stay within the hexagon segment', 'so neighbouring hexpansions fit'],
                  ['tie Detect to ground', 'or the port stays unpowered'],
                  ['fit your own I2C pull-ups', 'the bus has none'],
                  ['never use I2C address 0x77', 'the badge uses it for its I2C switch'],
                  ['parts over the badge at most 1 mm tall near the connector, 7 mm further out', 'the '
                   'battery sits beneath; the two slots over the USB connectors allow nothing below the board']),
            p('A hexpansion with an I2C EEPROM, at address 0x50 or 0x57, can identify itself and even carry its '
              'own app. The EEPROM starts with a 32-byte header; this builds one, and is checked against the '
              'example in the documentation:'),
            code(inspect.getsource(header)),
            p('Get a vendor and product ID before shipping one: the documentation explains the shared IDs and '
              'how to flash the EEPROM from a computer with mpremote.'),
        ]),
        ('charlieplexing', 'Charlieplexing LEDs', [
            p('A pin can be high, low, or an input that floats, connected to nothing. Charlieplexing uses all '
              'three: with one pin high, one low and the rest floating, exactly one LED between the high and '
              'the low pin lights. Stepping through every pair faster than the eye can follow seems to light '
              'any pattern.'),
            fig(charlieplex(), 'Each LED in turn. The ring marks the lit LED; the other LEDs between the two pins '
                'form paths of two in series, which need twice the forward voltage and stay dark.'),
            eq(r'N = n\,(n - 1)', 'Charlieplexing', '$n$ pins drive $N$ LEDs: 3 pins 6 LEDs, 5 pins 20, 10 pins 90'),
            p('Each LED is lit for only $1/N$ of the time, so it looks dimmer: drive it harder, within the pin\'s '
              'limits, or use fewer LEDs per group. Keep the supply below twice the LEDs\' forward voltage so '
              'the series paths stay dark.'),
        ]),
        ('addressable', 'Addressable LEDs', [
            p('Addressable LEDs, such as the WS2812B, contain a red, green and blue LED and a small controller. '
              'They chain on one data line: each keeps the first colour it receives and passes the rest on. '
              'The data is a pulse per bit, its width telling 0 from 1.'),
            fig(addressable(), 'Top: the two bit shapes. Bottom: three colours sent down a chain of three '
                'LEDs. The bits of each colour go green, red, blue, most significant first.'),
            eq(r'I_{max} \approx N \times 60\,\mathrm{mA} \qquad t_{frame} = 30\,\mu\mathrm{s} \times N + '
               r't_{reset}', 'Addressable LEDs',
               'full white draws about 20 mA per colour; each LED takes 24 bits of 1.25 µs'),
            p('Sixty LEDs at full white draw 3.6 A from 5 V, so budget power first and limit brightness in '
              'software. Their data input expects at least 0.7 × 5 V = 3.5 V for a 1, which a 3.3 V '
              'microcontroller does not reliably give: add a 74AHCT125 buffer '
              f'({link("09-interfaces", "levels", "Level shifting")}). Put a large capacitor across the supply '
              'where the power enters, and a 100 nF capacitor at each LED.'),
        ]),
        ('matrix', 'Key matrices', [
            p('Keyboards wire their keys in a grid of rows and columns, so many keys need few pins. The '
              'microcontroller drives one row low at a time and reads the columns, which have pull-ups: a pressed '
              'key in that row pulls its column low.'),
            fig(matrix(), 'Pressed: keys 0,0, 0,1 and 1,0. The readings are computed from the circuit; the cross '
                'marks the diode that stops the ghost.'),
            eq(r'\text{keys} = r \times c \qquad \text{pins} = r + c', 'Key matrix',
               '60 keys in 5 rows of 12 columns need 17 pins'),
            p('The diodes also let any number of keys be pressed at once, which games and fast typists need. '
              'Debounce every key as in '
              f'{link("09-interfaces", "buttons", "Buttons and debouncing")}. The Communicator hands its '
              'keyboard to a TCA8418, a chip that scans the matrix and reports keys over I2C.'),
            code(SCAN),
        ]),
        ('touch', 'Touch pads', [
            p('A copper pad under the solder mask makes a touch button with no moving parts. The pad has a few '
              'picofarads of capacitance to its surroundings, and a finger adds a few more '
              f'({link("03-ac", "capacitors", "Capacitors")}). Charged through a resistor, the pad takes longer '
              'to reach the input threshold when touched:'),
            fig(touch_figure, 'The microcontroller times the charge over and over, and reports a touch when the '
                'time grows.'),
            eq(r't = R\,C \ln\frac{V_{DD}}{V_{DD} - V_{th}}', 'Touch pad charge time',
               f'1 MΩ: {alone:.1f} µs alone and {touched:.1f} µs with a 5 pF finger'),
            p('Many microcontrollers, the ESP32-S3 among them, have touch inputs that do this in hardware. Make '
              'pads about the size of a fingertip, 10 to 15 mm, keep a gap to the ground pour around them, and '
              'run their tracks short and away from noisy signals.'),
        ]),
        ('charging', 'Charging a lithium cell', [
            p('A lithium cell charges at a constant current until it reaches 4.2 V, then at a constant 4.2 V '
              'while the current falls away. The charger stops when the current drops to a tenth or so of the '
              'starting value.'),
            fig(charging(), 'The shape of a typical charge at 1C, a current equal to the capacity per hour; real '
                'cells and chargers vary.'),
            eq(r'I_{charge} = \frac{1000\,\mathrm{V}}{R_{PROG}}', 'Charge current (MCP73831)',
               'the resistor on its PROG pin sets the current: 2 kΩ for 500 mA'),
            p('Charge small LiPo cells at 0.5C to 1C, never below freezing, and always through a charger IC. '
              'Use protected cells, or add a protection chip, so a short or a flat battery cannot damage the '
              'cell.'),
        ]),
        ('projects', 'Project ideas', [
            table(['Project', 'What it teaches', 'Chapters'],
                  ['an LED name badge on a coin cell', 'charlieplexing, sleep current',
                   link('09-interfaces', 'battery', 'Microcontroller hardware')],
                  ['a macropad of a few keys', 'key matrix, debouncing, USB',
                   link('06-digital', 'fsm', 'Digital logic')],
                  ['an addressable LED lamp', 'power budget, level shifting',
                   link('09-interfaces', 'power', 'Regulators')],
                  ['a sensor logger', 'I2C, ADC, battery life', link('07-signals', 'adc', 'Signals')],
                  ['a line-following robot', 'H-bridge, PID control', link('08-robotics', 'motors', 'Robotics')],
                  ['an SAO for any badge', 'a tiny board, I2C', link('10-pcb', 'footprints', 'PCB design')],
                  ['a Tildagon hexpansion', 'the EEPROM header, a MicroPython app', '<a href="#hexpansion">Above</a>'],
                  ['a LoRa messenger', 'SPI radio, 50 Ω antenna track', link('10-pcb', 'impedance',
                                                                             'Controlled impedance')]),
            note('Read more: DOCS → PCB AND BADGES has the Tildagon documentation, with hexpansions, apps and '
                 'repairs, the Communicator schematic and the Vectorscope board layers.'),
        ]),
    ]
