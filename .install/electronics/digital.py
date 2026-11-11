import math

from draw import (Figure, arrow, begin, circle, dff, dot, end, gate, head, line, path, phases, rect, sweep, terminal,
                  text, trace, wire)
from page import code, eq, fig, link, note, p, table

NAME = '06-digital'
TITLE = 'Digital logic'
LEDE = ('Logic levels and noise margins; gates, Boolean algebra and Karnaugh maps; adding in binary; latches, '
        'flip-flops, counters and shift registers; timing; and state machines.')

HIGH, LOW = 'w bold', 'w thin dim'


def level(f, value, *points):
    """A wire drawn heavy while it carries a 1."""
    wire(f, *points, cls=HIGH if value else LOW)


def barred(f, x, y, letters, anchor='start', cls='t'):
    """Text with a bar over it, as in Q̄."""
    f.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">'
          f'<tspan text-decoration="overline">{letters}</tspan></text>')


def levels():
    f = Figure(900, 280, 'Output levels, input thresholds and the noise margins between them, for 3.3 V logic')
    y = lambda v: 250 - 60 * v
    for x, title, high, low, middle in ((190, 'output', 2.4, 0.4, 'switching'), (560, 'input', 2.0, 0.8,
                                                                                    'undefined')):
        text(f, x + 35, 30, title, 'middle', 't head')
        rect(f, x, y(3.3), 70, y(high) - y(3.3), 'fill')
        rect(f, x, y(high), 70, y(low) - y(high), 'shade')
        rect(f, x, y(low), 70, y(0) - y(low), 'fill')
        rect(f, x, y(3.3), 70, y(0) - y(3.3))
        text(f, x + 35, (y(3.3) + y(high)) / 2 + 5, '1', 'middle', 't b inv')
        text(f, x + 35, (y(low) + y(0)) / 2 + 5, '0', 'middle', 't b inv')
        text(f, x + 35, (y(high) + y(low)) / 2 + 4, middle, 'middle', 't s')
    for v, name in ((3.3, '3.3 V'), (2.4, 'V_OH = 2.4'), (0.4, 'V_OL = 0.4'), (0, '0 V')):
        text(f, 180, y(v) + 4, name, 'end', 't s')
    for v, name in ((2.0, 'V_IH = 2.0'), (0.8, 'V_IL = 0.8')):
        text(f, 640, y(v) + 4, name, 'start', 't s')
    for v in (2.4, 2.0, 0.8, 0.4):
        line(f, 260, y(v), 560, y(v), 'w thin dash')
    for top, bottom, name in ((2.4, 2.0, 'NM_H = 0.4 V'), (0.8, 0.4, 'NM_L = 0.4 V')):
        line(f, 330, y(top), 330, y(bottom), 'w')
        text(f, 342, (y(top) + y(bottom)) / 2 + 4, name, 'start', 't s')
    return f


LOGIC = {'AND': lambda a, b: a & b, 'OR': lambda a, b: a | b, 'XOR': lambda a, b: a ^ b,
         'NAND': lambda a, b: 1 - (a & b)}
CASES = ((0, 0), (0, 1), (1, 0), (1, 1))


def gates_live():
    f = Figure(900, 190, 'An AND, an OR, an XOR and a NAND gate fed every pair of inputs in turn')
    xs = (130, 350, 570, 790)
    for x, kind in zip(xs, LOGIC):
        gate(f, kind, x, 100)
        text(f, x, 158, kind, 'middle', 't head')
    for cls, (a, b) in zip(phases(f, 4, 8), CASES):
        begin(f, cls)
        text(f, 450, 34, f'A = {a}   B = {b}', 'middle', 't b')
        for x, rule in zip(xs, LOGIC.values()):
            out = rule(a, b)
            level(f, a, (x - 70, 92), (x - 30, 92))
            level(f, b, (x - 70, 108), (x - 30, 108))
            level(f, out, (x + 30, 100), (x + 70, 100))
            text(f, x - 76, 96, str(a), 'end', 't s')
            text(f, x - 76, 112, str(b), 'end', 't s')
            text(f, x + 76, 105, str(out), 'start', 't b')
        end(f)
    return f


def tied(f, x, y, source):
    """A NAND gate with its inputs joined, an inverter; returns its output."""
    pins = gate(f, 'NAND', x, y)
    wire(f, source, (x - 40, y))
    wire(f, pins['A'], (x - 40, y - 8), (x - 40, y + 8), pins['B'])
    dot(f, x - 40, y)
    return pins['Y']


def nand_only():
    f = Figure(900, 200, 'NOT, AND and OR made from NAND gates alone')
    terminal(f, 50, 100)
    text(f, 40, 104, 'A', 'end')
    out = tied(f, 140, 100, (50, 100))
    wire(f, out, (210, 100))
    terminal(f, 210, 100)
    barred(f, 220, 104, 'A')
    text(f, 130, 170, 'NOT', 'middle', 't head')
    pins = gate(f, 'NAND', 340, 100)
    for name, yy in (('A', 92), ('B', 108)):
        terminal(f, 280, yy)
        text(f, 270, yy + 4, name, 'end')
        wire(f, (280, yy), pins[name])
    out = tied(f, 450, 100, pins['Y'])
    wire(f, out, (520, 100))
    terminal(f, 520, 100)
    text(f, 530, 104, 'AB', 'start')
    text(f, 400, 170, 'AND', 'middle', 't head')
    last = gate(f, 'NAND', 790, 100)
    for name, yy, pin in (('A', 70, 'A'), ('B', 130, 'B')):
        terminal(f, 600, yy)
        text(f, 590, yy + 4, name, 'end')
        out = tied(f, 690, yy, (600, yy))
        wire(f, out, (740, yy), (740, last[pin][1]), last[pin])
    wire(f, last['Y'], (860, 100))
    terminal(f, 860, 100)
    text(f, 860, 124, 'A + B')
    text(f, 720, 170, 'OR', 'middle', 't head')
    return f


GRAY = ('00', '01', '11', '10')
ONES = {0, 2, 5, 7, 8, 10, 13, 15}


def kmap():
    f = Figure(640, 290, 'A four-variable Karnaugh map and its two groups')
    x0, y0, size = 150, 70, 50
    line(f, x0 - 44, y0 - 34, x0, y0)
    text(f, x0 - 32, y0 - 4, 'AB', 'middle', 't s')
    text(f, x0 - 10, y0 - 24, 'CD', 'middle', 't s')
    for k, bits in enumerate(GRAY):
        text(f, x0 + size * k + size / 2, y0 - 10, bits, 'middle', 't s')
        text(f, x0 - 10, y0 + size * k + size / 2 + 4, bits, 'end', 't s')
    for row, ab in enumerate(GRAY):
        for col, cd in enumerate(GRAY):
            x, y = x0 + size * col, y0 + size * row
            rect(f, x, y, size, size, 'grid')
            one = int(ab + cd, 2) in ONES
            text(f, x + size / 2, y + size / 2 + 5, '1' if one else '0', 'middle', 't b' if one else 't s')
    rect(f, x0, y0, 4 * size, 4 * size, 'w thin')
    rect(f, x0 + size + 6, y0 + size + 6, 2 * size - 12, 2 * size - 12, 'w', 14)
    for col in (0, 3):
        for row in (0, 3):
            rect(f, x0 + size * col + 7, y0 + size * row + 7, size - 14, size - 14, 'w dash', 10)
    f.add('<text class="t b" x="420" y="140">f = BD + <tspan text-decoration="overline">B</tspan> '
          '<tspan text-decoration="overline">D</tspan></text>')
    text(f, 420, 170, 'solid: B = 1 and D = 1', 'start', 't s')
    f.add('<text class="t s" x="420" y="188">dashed: <tspan text-decoration="overline">B</tspan> and '
          '<tspan text-decoration="overline">D</tspan>, the corners</text>')
    return f


def full_adder():
    f = Figure(640, 290, 'A full adder built from two XOR, two AND and one OR gate')
    for name, y in (('A', 70), ('B', 86), ('C_in', 150)):
        terminal(f, 50, y)
        text(f, 40, y + 4, name, 'end')
    first = gate(f, 'XOR', 180, 78)
    second = gate(f, 'XOR', 380, 110)
    both = gate(f, 'AND', 380, 182)
    carry = gate(f, 'AND', 380, 246)
    either = gate(f, 'OR', 480, 214)
    wire(f, (50, 70), first['A'])
    wire(f, (50, 86), first['B'])
    wire(f, (70, 70), (70, 238), carry['A'])
    wire(f, (100, 86), (100, 254), carry['B'])
    dot(f, 70, 70)
    dot(f, 100, 86)
    wire(f, first['Y'], (250, 78), (250, 102), second['A'])
    wire(f, (250, 102), (250, 190), both['B'])
    dot(f, 250, 102)
    wire(f, (50, 150), (300, 150))
    wire(f, second['B'], (300, 118), (300, 174), both['A'])
    dot(f, 300, 150)
    wire(f, both['Y'], (430, 182), (430, 206), either['A'])
    wire(f, carry['Y'], (430, 246), (430, 222), either['B'])
    wire(f, second['Y'], (570, 110))
    wire(f, either['Y'], (570, 214))
    terminal(f, 570, 110)
    terminal(f, 570, 214)
    text(f, 580, 114, 'S', 'start')
    text(f, 580, 218, 'C_out', 'start')
    return f


def ripple():
    f = Figure(900, 250, 'A 4-bit ripple-carry adder working out 0111 + 0001')
    a, b = (1, 1, 1, 0), (1, 0, 0, 0)
    xs = (690, 510, 330, 150)
    text(f, 40, 22, 'A = 0111 (7), B = 0001 (1); bit 0 is on the right', 'start', 't s')
    for i, x in enumerate(xs):
        rect(f, x - 45, 80, 90, 70)
        text(f, x, 120, 'FA', 'middle', 't head')
        level(f, a[i], (x - 20, 54), (x - 20, 80))
        level(f, b[i], (x + 20, 54), (x + 20, 80))
        text(f, x - 24, 50, f'A_{i} = {a[i]}', 'end', 't s')
        text(f, x + 24, 50, f'B_{i} = {b[i]}', 'start', 't s')
    for x in xs:
        f.add(head(x + 45, 115, math.pi, 8))
    f.add(head(40, 115, math.pi, 8))
    carries = ((0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0))
    for k, (cls, chain) in enumerate(zip(phases(f, 4, 10, [0, 0.2, 0.4, 0.6, 1]), carries)):
        c = (0,) + chain
        s = [a[i] ^ b[i] ^ c[i] for i in range(4)]
        begin(f, cls)
        for i, x in enumerate(xs):
            right = x + 45 if i else 800
            level(f, c[i], (right + (90 if i else 0), 115), (x + 52, 115))
            text(f, (right + (90 if i else 0) + x + 45) / 2, 107, f'c_{i} = {c[i]}', 'middle', 't s')
            level(f, s[i], (x, 150), (x, 182))
            text(f, x, 200, f'S_{i} = {s[i]}', 'middle', 't b')
        level(f, c[4], (105, 115), (47, 115))
        text(f, 72, 107, f'c_4 = {c[4]}', 'middle', 't s')
        total = ''.join(str(bit) for bit in reversed(s))
        done = ' = 8, correct' if k == 3 else ', still settling'
        text(f, 450, 236, f'after {k} carry delay{"" if k == 1 else "s"}: S = {total}{done}', 'middle', 't s')
        end(f)
    return f


def mux():
    f = Figure(640, 240, 'A 2-to-1 multiplexer passing D0, then D1')
    invert = gate(f, 'NOT', 200, 150)
    upper = gate(f, 'AND', 330, 82)
    lower = gate(f, 'AND', 330, 172)
    either = gate(f, 'OR', 450, 127)
    for name, y in (('D_0 = 1', 74), ('D_1 = 0', 164), ('S', 210)):
        terminal(f, 80, y)
        text(f, 70, y + 4, name, 'end')
    dot(f, 130, 210)
    terminal(f, 540, 127)
    text(f, 550, 131, 'Y', 'start')
    for cls, select in zip(phases(f, 2, 6), (0, 1)):
        d0, d1 = 1, 0
        top, bottom = d0 & (1 - select), d1 & select
        begin(f, cls)
        level(f, d0, (80, 74), upper['A'])
        level(f, d1, (80, 164), lower['A'])
        level(f, select, (80, 210), (130, 210), (130, 150), invert['A'])
        text(f, 100, 202, str(select), 'middle', 't s')
        level(f, select, (130, 210), (280, 210), (280, 180), lower['B'])
        level(f, 1 - select, invert['Y'], (260, 150), (260, 90), upper['B'])
        level(f, top, upper['Y'], (390, 82), (390, 119), either['A'])
        level(f, bottom, lower['Y'], (390, 172), (390, 135), either['B'])
        level(f, top | bottom, either['Y'], (540, 127))
        text(f, 320, 30, f'S = {select}: Y follows D_{select}, now {top | bottom}', 'middle', 't s')
        end(f)
    return f


def sr_latch():
    f = Figure(900, 250, 'An SR latch of two NOR gates being set, holding, reset and holding')
    top = gate(f, 'NOR', 300, 90)
    bottom = gate(f, 'NOR', 300, 190)
    terminal(f, 130, 82)
    terminal(f, 130, 198)
    terminal(f, 420, 90)
    terminal(f, 420, 190)
    text(f, 120, 86, 'R', 'end')
    text(f, 120, 202, 'S', 'end')
    text(f, 430, 94, 'Q', 'start')
    barred(f, 430, 194, 'Q')
    states = (('set', 1, 0, 1, ('S = 1 drives the lower output to 0,', 'so with R = 0, Q rises to 1')),
              ('hold', 0, 0, 1, ('S = R = 0: each gate holds the', 'other in place, and Q stays 1')),
              ('reset', 0, 1, 0, ('R = 1 drives Q to 0,', 'so the lower output rises to 1')),
              ('hold', 0, 0, 0, ('S = R = 0 again:', 'the latch remembers 0')))
    for cls, (name, s, r, q, lines) in zip(phases(f, 4, 12), states):
        begin(f, cls)
        level(f, r, (130, 82), top['A'])
        level(f, s, (130, 198), bottom['B'])
        level(f, q, top['Y'], (420, 90))
        level(f, q, (360, 90), (360, 120), (240, 160), (240, 182), bottom['A'])
        level(f, 1 - q, bottom['Y'], (420, 190))
        level(f, 1 - q, (360, 190), (360, 160), (240, 120), (240, 98), top['B'])
        for value, x, y in ((r, 160, 74), (s, 160, 190), (q, 390, 82), (1 - q, 390, 182)):
            text(f, x, y, str(value), 'middle', 't s')
        text(f, 540, 110, name.upper(), 'start', 't head')
        for k, words in enumerate(lines):
            text(f, 540, 136 + 18 * k, words, 'start', 't s')
        end(f)
    dot(f, 360, 90)
    dot(f, 360, 190)
    return f


def flip_flop_timing():
    f = Figure(900, 250, 'A D flip-flop sampling its input on each rising clock edge')
    x0, scale = 110, 90
    at = lambda t: x0 + t * scale
    for edge in (1, 3, 5, 7):
        rect(f, at(edge - 0.25), 30, 0.35 * scale, 190, 'shade')
        line(f, at(edge), 30, at(edge), 220, 'w thin faint')
    text(f, at(0.9), 24, 'setup and hold window', 'middle', 't s')
    trace(f, x0, 44, scale, [(t, t % 2) for t in range(9)], 8, 'CLK')
    trace(f, x0, 114, scale, [(0, 0), (0.5, 1), (2.4, 0), (4.3, 1), (4.6, 0), (5.6, 1)], 8, 'D')
    trace(f, x0, 184, scale, [(0, 0), (1.15, 1), (3.15, 0), (7.15, 1)], 8, 'Q')
    text(f, at(4.45), 106, 'ignored', 'middle', 't s')
    sweep(f, 'cursor', at(0), at(8), 30, 220, 16)
    return f


def counter_timing():
    f = Figure(900, 280, 'A 3-bit counter counting clock edges')
    x0, scale = 110, 90
    for k in range(8):
        text(f, x0 + (k + 0.5) * scale, 30, str(k), 'middle', 't b')
    trace(f, x0, 50, scale, [(k / 2, 1 - k % 2) for k in range(16)], 8, 'CLK')
    for bit in range(3):
        trace(f, x0, 110 + 60 * bit, scale, [(k, (k >> bit) & 1) for k in range(8)], 8, f'Q_{bit}')
    sweep(f, 'cursor', x0, x0 + 8 * scale, 14, 270, 16)
    return f


def shift_register():
    f = Figure(900, 240, 'A 4-bit shift register taking in 1, 0, 1, 1')
    xs, y = (190, 350, 510, 670), 120
    pins = [dff(f, x, y, None) for x in xs]
    for left, right in zip(pins, pins[1:]):
        wire(f, left['Q'], right['D'])
    wire(f, pins[-1]['Q'], (740, y - 15))
    terminal(f, 90, y - 15)
    text(f, 80, y - 11, 'SER', 'end', 't s')
    wire(f, (90, y - 15), pins[0]['D'])
    terminal(f, 90, 196)
    text(f, 80, 200, 'CLK', 'end', 't s')
    wire(f, (90, 196), (xs[-1] - 50, 196))
    for i, (x, pin) in enumerate(zip(xs, pins)):
        wire(f, (x - 50, 196), (x - 50, y + 17), pin['CLK'])
        if i < len(xs) - 1:
            dot(f, x - 50, 196)
        wire(f, (x + 60, y - 15), (x + 60, y - 58))
        dot(f, x + 60, y - 15)
        terminal(f, x + 60, y - 58)
        text(f, x + 60, y - 68, f'Q_{i}')
    contents = ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (1, 0, 1, 0), (1, 1, 0, 1))
    serial = (1, 0, 1, 1, 0)
    for k, (cls, bits) in enumerate(zip(phases(f, 5, 10), contents)):
        begin(f, cls)
        level(f, serial[k], (90, y - 15), pins[0]['D'])
        text(f, 110, y - 23, str(serial[k]), 'middle', 't s')
        for x, bit in zip(xs, bits):
            text(f, x, y + 6, str(bit), 'middle', 't b')
            if bit:
                wire(f, (x + 38, y - 15), (x + 122 if x != xs[-1] else 740, y - 15), cls=HIGH)
                wire(f, (x + 60, y - 15), (x + 60, y - 58), cls=HIGH)
        text(f, 450, 232, f'after {k} clock edge{"" if k == 1 else "s"}: {"".join(map(str, bits))}', 'middle',
             't s')
        end(f)
    return f


def traffic():
    f = Figure(900, 260, 'A traffic-light state machine stepping through its states')
    y, states = 110, (('GREEN', 150), ('YELLOW', 450), ('RED', 750))
    for name, x in states:
        circle(f, x, y, 46)
        text(f, x, y + 5, name)
    arrow(f, 196, y, 404, y, 'w', 9)
    arrow(f, 496, y, 704, y, 'w', 9)
    text(f, 300, y - 12, 'after 30 s', 'middle', 't s')
    text(f, 600, y - 12, 'after 4 s', 'middle', 't s')
    path(f, f'M 750 {y + 46} C 750 250 150 250 150 {y + 54}')
    f.add(head(150, y + 47, -1.5708, 9))
    text(f, 450, 212, 'after 30 s', 'middle', 't s')
    for cls, (name, x) in zip(phases(f, 3, 9), states):
        begin(f, cls)
        circle(f, x, y, 40, 'fill')
        text(f, x, y + 5, name, 'middle', 't inv')
        end(f)
    return f


STATE_MACHINE = r'''
enum state { GREEN, YELLOW, RED };

struct step { enum state next; unsigned long ms; };

static const struct step table[] = {
    [GREEN]  = { YELLOW, 30000 },
    [YELLOW] = { RED,     4000 },
    [RED]    = { GREEN,  30000 },
};

static enum state now = GREEN;
static unsigned long since;

/* Called often from the main loop with a millisecond clock. */
void tick(unsigned long ms)
{
    if (ms - since >= table[now].ms) {    /* unsigned: survives wrap-around */
        now = table[now].next;
        since = ms;
        show(now);
    }
}
'''


def sections():
    return [
        ('levels', 'Logic levels and noise margins', [
            p('A digital signal is a voltage read as 1 above one threshold and 0 below another. Outputs promise '
              'to stay further out than inputs need, and the gap, the noise margin, is how much noise a signal '
              'can pick up on the way and still be read correctly.'),
            fig(levels(), 'Any output at 2.4 V or more is read as 1 by any input that needs only 2.0 V; any '
                'output at 0.4 V or less is read as 0 by any input that accepts up to 0.8 V.'),
            eq(r'NM_H = V_{OH} - V_{IH} \qquad NM_L = V_{IL} - V_{OL}', 'Noise margins'),
            table(['Family', '$V_{IL}$ max', '$V_{IH}$ min', '$V_{OL}$ max', '$V_{OH}$ min'],
                  ['TTL (74LS), 5 V', '0.8', '2.0', '0.5', '2.7'],
                  ['CMOS (74HC), 5 V', '1.5', '3.5', '0.1', '4.4'],
                  ['LVCMOS, 3.3 V', '0.8', '2.0', '0.4', '2.4'],
                  ['LVCMOS, 1.8 V', '0.63', '1.17', '0.45', '1.35']),
            p('Mixing families needs care. A 3.3 V output, at best 3.3 V, is not a guaranteed 1 for a 5 V 74HC '
              'input that needs 3.5 V; a 74HCT part, made with TTL input levels, or a level shifter fixes it. '
              'A 5 V output into a 3.3 V input can destroy it unless the input is marked 5 V tolerant.'),
        ]),
        ('gates', 'Gates', [
            p('Each gate computes one function of its inputs. The symbols, in both the ANSI and IEC styles, '
              f'are in {link("01-symbols", "ics", "Schematic symbols")}.'),
            fig(gates_live(), 'Four gates fed 00, 01, 10 and 11 in turn. Heavy wires carry 1. AND needs every '
                'input 1; OR needs any; XOR needs an odd number; NAND is AND inverted.'),
            eq(r'Y = A \cdot B \qquad Y = A + B \qquad Y = A \oplus B \qquad Y = \overline{A \cdot B}',
               'Logic gates'),
            table(['A', 'B', 'AND', 'OR', 'XOR', 'NAND', 'NOR', 'XNOR'],
                  *[[str(a), str(b), str(a & b), str(a | b), str(a ^ b), str(1 - (a & b)), str(1 - (a | b)),
                     str(1 - (a ^ b))] for a, b in CASES]),
        ]),
        ('algebra', 'Boolean algebra', [
            p('Logic has its own algebra, with AND as multiplication, OR as addition and a bar for NOT. Most '
              'rules look like ordinary algebra; a few do not, such as $A + A = A$.'),
            eq(r'A + 0 = A \qquad A \cdot 1 = A \qquad A + \overline{A} = 1 \qquad A \cdot \overline{A} = 0',
               'Boolean identities'),
            eq(r'A + A B = A \qquad A + \overline{A} B = A + B \qquad A (B + C) = A B + A C'),
            p('De Morgan\'s laws turn an AND into an OR and back by inverting everything:'),
            eq(r'\overline{A \cdot B} = \overline{A} + \overline{B} \qquad \overline{A + B} = \overline{A} \cdot '
               r'\overline{B}', "De Morgan's laws"),
            p('So NAND alone can build every other function, and so can NOR. Chips are built mostly from these, '
              'since in CMOS they take the fewest transistors.'),
            fig(nand_only(), 'NOT is a NAND with its inputs joined; AND is a NAND followed by a NOT; OR is a '
                'NAND of the inverted inputs, by De Morgan.'),
        ]),
        ('kmaps', 'Karnaugh maps', [
            p('To simplify a function of up to four inputs, lay its truth table out as a grid whose rows and '
              'columns count in Gray code, 00, 01, 11, 10, so that neighbouring cells differ in one input. Then '
              'circle rectangles of 1s, each 1, 2, 4 or 8 cells, as large as possible; the edges wrap round. '
              'Each rectangle is one AND term, keeping only the inputs that do not change inside it.'),
            fig(kmap(), 'The function is 1 for inputs 0, 2, 5, 7, 8, 10, 13 and 15. The middle square needs '
                'B = 1 and D = 1; the four corners join up across the edges into one group, B = 0 and D = 0. '
                'Eight terms become two.'),
        ]),
        ('arithmetic', 'Binary arithmetic', [
            p('An $n$-bit number holds $2^n$ values. Signed numbers use two\'s complement: the top bit counts '
              'as $-2^{n-1}$, so the same adder handles positive and negative numbers. To negate, invert every '
              'bit and add 1.'),
            eq(r'-x = \overline{x} + 1 \qquad -2^{n-1} \le x \le 2^{n-1} - 1', "Two's complement"),
            table(['Bits', 'Unsigned', 'Signed', 'Hex'],
                  ['0000', '0', '0', '0'], ['0111', '7', '7', '7'], ['1000', '8', '−8', '8'],
                  ['1111', '15', '−1', 'F']),
            p('A full adder adds two bits and a carry in, giving a sum bit and a carry out:'),
            eq(r'S = A \oplus B \oplus C_{in} \qquad C_{out} = A B + C_{in}\,(A \oplus B)', 'Full adder'),
            fig(full_adder(), 'The first XOR adds A and B; the second adds the carry in. A carry comes out if '
                'A and B are both 1, or if exactly one is and the carry in is 1.'),
            p('Chained, the carry out of each bit feeds the next. The answer is only right once the carry has '
              'rippled all the way through, so an $n$-bit ripple adder takes $n$ carry delays; faster adders '
              'look ahead to compute the carries in parallel.'),
            fig(ripple(), 'Adding 1 to 7: each bit first shows A ⊕ B, then corrects itself as the carry arrives. '
                'Until the last carry lands, the outputs pass through wrong values, a glitch, which is why '
                'circuits sample results only on a clock edge.'),
            eq(r't_{add} \approx n\,t_{carry}', 'Ripple-carry delay'),
        ]),
        ('mux', 'Multiplexers and decoders', [
            p('A multiplexer is a switch made of gates: its select input chooses which data input reaches the '
              'output. A decoder does the opposite, turning an $n$-bit number into one of $2^n$ lines, such as '
              'a chip select.'),
            eq(r'Y = \overline{S}\,D_0 + S\,D_1', 'Multiplexer'),
            fig(mux(), 'With S = 0 the upper AND passes D0; with S = 1 the lower one passes D1. Heavy wires '
                'carry 1.'),
        ]),
        ('memory', 'Latches and flip-flops', [
            p('Feed two gates\' outputs back into each other and the circuit remembers. This SR latch is set by '
              'a pulse on S and reset by a pulse on R; with both low it holds. Both high at once is forbidden: '
              'it forces both outputs to 0, and the state after they are released is unpredictable.'),
            fig(sr_latch(), 'The crossed wires are the memory: each gate\'s output holds the other gate in '
                'place once the inputs return to 0.'),
            table(['S', 'R', 'Q', 'Meaning'],
                  ['0', '0', 'unchanged', 'hold'], ['1', '0', '1', 'set'], ['0', '1', '0', 'reset'],
                  ['1', '1', 'forbidden', 'both outputs 0']),
            p('A D flip-flop copies its D input to Q only at the rising edge of its clock and holds it between '
              'edges. D must be steady from the setup time $t_{su}$ before the edge until the hold time $t_h$ '
              'after it; Q follows a clock-to-output delay $t_{cq}$ later.'),
            fig(flip_flop_timing(), 'Q changes only just after rising clock edges. The short pulse on D between '
                'edges never reaches Q. A change inside a shaded window could leave the flip-flop undecided, '
                'metastable, for a while.'),
            p('Between two flip-flops, the logic in between must settle within one clock period, which sets the '
              'fastest clock; and it must not settle so fast that it upsets the hold time of the next flip-flop:'),
            eq(r'f_{max} = \frac{1}{t_{cq} + t_{pd} + t_{su}} \qquad t_{cq} + t_{pd,min} \ge t_h',
               'Maximum clock frequency'),
            p('A signal from outside, such as a button, is not in step with the clock. Pass it through two '
              'flip-flops in a row, a synchroniser, before using it.'),
        ]),
        ('counters', 'Counters and shift registers', [
            p('Flip-flops that each toggle when the one before falls make a binary counter. Each output runs '
              'at half the frequency of the one before, so a counter is also a frequency divider:'),
            eq(r'f_{Q_k} = \frac{f_{clk}}{2^{k+1}}', 'Counter outputs'),
            fig(counter_timing(), 'Each rising clock edge adds one; read top to bottom, $Q_2 Q_1 Q_0$ is the '
                'count in binary.'),
            p('Flip-flops in a chain, each D fed from the Q before, make a shift register: at each clock edge '
              'every bit moves one place along. The 74HC595 takes bits in one at a time and presents them on '
              'eight outputs, so three pins can drive eight LEDs, or many more with chips chained.'),
            fig(shift_register(), 'Bits enter at SER and march right, one place per clock edge.'),
        ]),
        ('fsm', 'State machines', [
            p('A circuit or program whose behaviour depends on what happened before is a state machine: a set '
              'of states, and rules for moving between them on inputs or time. Draw it as a diagram first; the '
              'code follows directly. In a Moore machine the outputs depend only on the state, in a Mealy '
              'machine on the state and the inputs.'),
            fig(traffic(), 'Three states, each with a time limit; the filled circle is the current state.'),
            p('On a microcontroller the same machine is a table and a function called from the main loop, '
              'without blocking delays, so the program can do other work meanwhile:'),
            code(STATE_MACHINE),
            p('With $n$ flip-flops a hardware state machine has up to $2^n$ states. Debouncing a button, '
              'decoding a protocol and sequencing a power-up are all state machines.'),
            note('Read more: MIT 6.002 lectures 4, 5, 13 and 14 (the digital abstraction, gates, speed, state '
                 'and memory), <em>Lessons in Electric Circuits IV: Digital</em>, and the Logisim guides, all '
                 'in DOCS → CIRCUITS LIBRARY. Logisim itself is a Java desktop program that needs X11, which '
                 'this desktop does not run.'),
        ]),
    ]
