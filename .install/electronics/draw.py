"""SVG drawing kit for the electronics guide: schematic symbols, plots and CSS motion.

Coordinates are SVG user units (CSS pixels). Two-terminal parts are drawn along
the line between their terminals; their text stays upright. Motion is CSS only,
so it pauses with the page's control and stops for reduced motion, leaving the
first frame.
"""
import math
from html import escape


def num(value):
    text = f'{value:.2f}'.rstrip('0').rstrip('.')
    return '0' if text in ('-0', '') else text


def poly(points):
    return 'M ' + ' L '.join(f'{num(x)} {num(y)}' for x, y in points)


def rich(text):
    """SVG text with subscripts and superscripts: _out or _{a b} and ^2 or ^{-1}.

    Without braces a script runs to the end of its letters and digits, or is one
    other character.
    """
    out, i, shift = [], 0, 0
    while i < len(text):
        c = text[i]
        if c in '_^' and i + 1 < len(text):
            if text[i + 1] == '{':
                j = text.index('}', i)
                part, i = text[i + 2:j], j + 1
            else:
                j = i + 1
                while j < len(text) and text[j].isalnum():
                    j += 1
                j = max(j, i + 2)
                part, i = text[i + 1:j], j
            dy = (4 if c == '_' else -6) - shift
            shift += dy
            out.append(f'<tspan dy="{dy}" font-size="72%">{escape(part)}</tspan>')
        else:
            j = i
            while j < len(text) and not (text[j] in '_^' and j + 1 < len(text)):
                j += 1
            chunk = escape(text[i:j])
            if shift:
                out.append(f'<tspan dy="{-shift}">{chunk}</tspan>')
                shift = 0
            else:
                out.append(chunk)
            i = j
    return ''.join(out)


class Figure:
    """One inline SVG; ids are numbered per page so keyframe names stay unique."""
    count = 0

    def __init__(self, width, height, title):
        Figure.count += 1
        self.id = f'f{Figure.count}'
        self.width, self.height, self.title = width, height, title
        self.body, self.css = [], []

    def add(self, *parts):
        self.body.extend(parts)
        return self

    def svg(self):
        style = f'<style>{"".join(self.css)}</style>' if self.css else ''
        return (f'<svg class="figure" viewBox="0 0 {num(self.width)} {num(self.height)}" '
                f'width="{num(self.width)}" height="{num(self.height)}" role="img" '
                f'aria-labelledby="{self.id}-title"><title id="{self.id}-title">{escape(self.title)}</title>'
                f'{style}{"".join(self.body)}</svg>')


# Primitives.

def line(f, x1, y1, x2, y2, cls='w'):
    f.add(f'<path class="{cls}" d="M {num(x1)} {num(y1)} L {num(x2)} {num(y2)}"/>')


def path(f, d, cls='w'):
    f.add(f'<path class="{cls}" d="{d}"/>')


def wire(f, *points, cls='w'):
    f.add(f'<path class="{cls}" d="{poly(points)}"/>')


def dot(f, x, y, r=3.2, cls='fill'):
    f.add(f'<circle class="{cls}" cx="{num(x)}" cy="{num(y)}" r="{num(r)}"/>')


def terminal(f, x, y, r=3.2):
    f.add(f'<circle class="w hollow" cx="{num(x)}" cy="{num(y)}" r="{num(r)}"/>')


def circle(f, x, y, r, cls='w'):
    f.add(f'<circle class="{cls}" cx="{num(x)}" cy="{num(y)}" r="{num(r)}"/>')


def rect(f, x, y, w, h, cls='w', rx=0):
    corner = f' rx="{num(rx)}"' if rx else ''
    f.add(f'<rect class="{cls}" x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{corner}/>')


def text(f, x, y, s, anchor='middle', cls='t'):
    f.add(f'<text class="{cls}" x="{num(x)}" y="{num(y)}" text-anchor="{anchor}">{rich(s)}</text>')


def tip(x, y, angle, size=7):
    """Path data for an arrowhead with its point at (x, y) facing angle (radians)."""
    back, wing = size, size * 0.45
    ax, ay = x - back * math.cos(angle), y - back * math.sin(angle)
    px, py = -math.sin(angle) * wing, math.cos(angle) * wing
    return f'M {num(x)} {num(y)} L {num(ax + px)} {num(ay + py)} L {num(ax - px)} {num(ay - py)} Z'


def head(x, y, angle, size=7, cls='fill'):
    return f'<path class="{cls}" d="{tip(x, y, angle, size)}"/>'


def arrow(f, x1, y1, x2, y2, cls='w thin', size=7):
    angle = math.atan2(y2 - y1, x2 - x1)
    tx, ty = x2 - size * 0.8 * math.cos(angle), y2 - size * 0.8 * math.sin(angle)
    f.add(f'<path class="{cls}" d="M {num(x1)} {num(y1)} L {num(tx)} {num(ty)}"/>', head(x2, y2, angle, size))


def dimension(f, x1, y1, x2, y2, label=None, at=None, anchor='middle'):
    """A dimension line with an arrowhead at each end; its label goes at the point at."""
    angle = math.atan2(y2 - y1, x2 - x1)
    line(f, x1, y1, x2, y2, 'w thin')
    f.add(head(x1, y1, angle + math.pi, 6), head(x2, y2, angle, 6))
    if label:
        lx, ly = at or ((x1 + x2) / 2, (y1 + y2) / 2 - 6)
        text(f, lx, ly, label, anchor, 't s')


def current(f, x, y, direction, label=None, side=1):
    """A current arrowhead on a wire at (x, y) facing r, l, u or d, with its name beside it."""
    angle = {'r': 0, 'd': math.pi / 2, 'l': math.pi, 'u': -math.pi / 2}[direction]
    f.add(head(x + 5 * math.cos(angle), y + 5 * math.sin(angle), angle, 9))
    if label:
        if direction in 'rl':
            text(f, x, y - 9 if side > 0 else y + 19, label)
        else:
            text(f, x + 10 if side > 0 else x - 10, y + 5, label, 'start' if side > 0 else 'end')


def flow(f, points, period=1.2, reverse=False, extra=''):
    """Moving dots along a wire: conventional current, faster for more current."""
    d = poly(points)
    cls = (' rev' if reverse else '') + (' ' + extra if extra else '')
    f.add(f'<path class="flow-halo{cls}" d="{d}" style="--t:{num(period)}s"/>',
          f'<path class="flow{cls}" d="{d}" style="--t:{num(period)}s"/>')


def begin(f, cls='', transform=None, style=None):
    attrs = (f' class="{cls}"' if cls else '') + (f' transform="{transform}"' if transform else '') + \
        (f' style="{style}"' if style else '')
    f.add(f'<g{attrs}>')


def end(f):
    f.add('</g>')


def phases(f, count, period, slots=None):
    """Class names that show one storyboard frame at a time, frame 0 when still."""
    bounds = slots or [k / count for k in range(count + 1)]
    names = []
    for k in range(count):
        name = f'{f.id}p{k}'
        start, stop = 100 * bounds[k], 100 * bounds[k + 1]
        frames = [f'0%{{opacity:{1 if k == 0 else 0}}}']
        if k:
            frames.append(f'{start:.3f}%{{opacity:1}}')
        if stop < 100:
            frames.append(f'{stop:.3f}%{{opacity:0}}')
        frames.append(f'100%{{opacity:{1 if k == count - 1 else 0}}}')
        f.css.append(f'@keyframes {name}{{{"".join(frames)}}}'
                     f'.{name}{{animation:{name} {num(period)}s step-end infinite}}')
        names.append(f'phase {name}' + (' first' if k == 0 else ''))
    return names


def keyframes(f, name, frames, period, timing='linear', base=None):
    """A named animation from (percent, declarations) pairs; returns its class.

    base holds the still state, which reduced motion shows.
    """
    body = ''.join(f'{p:.3f}%{{{decl}}}' for p, decl in frames)
    cls = f'{f.id}{name}'
    still = f'{base};' if base else ''
    f.css.append(f'@keyframes {cls}{{{body}}}.{cls}{{{still}animation:{cls} {num(period)}s {timing} infinite}}')
    return cls


def sampled(f, name, declaration, period, samples=48, base=None, timing='linear'):
    """An animation sampled from declaration(t), t in seconds within the period."""
    frames = [(100 * k / samples, declaration(period * k / samples)) for k in range(samples + 1)]
    return keyframes(f, name, frames, period, timing, base)


def flow_by(f, points, name, distance, period, samples=60, extra=''):
    """Dots along a wire that have moved distance(t) px by time t: their travel is
    the charge that has passed, so they speed up, slow down or reverse with it."""
    cls = sampled(f, name, lambda t: f'stroke-dashoffset:{num(-distance(t))}px', period, samples)
    d = poly(points)
    more = f' {extra}' if extra else ''
    f.add(f'<path class="flow-halo {cls}{more}" d="{d}"/>', f'<path class="flow {cls}{more}" d="{d}"/>')


def sweep(f, name, x0, x1, top, bottom, period):
    """A vertical cursor that crosses from x0 to x1 once a period."""
    start = f'transform:translateX({num(x0)}px)'
    cls = keyframes(f, name, [(0, start), (100, f'transform:translateX({num(x1)}px)')], period, base=start)
    f.add(f'<g class="{cls}"><path class="w thin" d="M 0 {num(top)} V {num(bottom)}"/></g>')


def steps(samples):
    """(x, y) samples of a stepped signal as a polyline with vertical edges."""
    out = [samples[0]]
    for x, y in samples[1:]:
        if y != out[-1][1]:
            out.append((x, out[-1][1]))
        out.append((x, y))
    return out


def trace(f, x, y, scale, changes, length, name, height=24):
    """A logic signal from (time, level) changes over length time units, scale px each."""
    samples = [(x + t * scale, y + (0 if v else height)) for t, v in changes]
    samples.append((x + length * scale, samples[-1][1]))
    wire(f, *steps(samples))
    text(f, x - 14, y + height / 2 + 4, name, 'end', 't s')


def along(points, fraction):
    """The point a fraction of the way along a polyline."""
    lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    goal, total = fraction * sum(lengths), 0
    for (a, b), size in zip(zip(points, points[1:]), lengths):
        if total + size >= goal and size:
            t = (goal - total) / size
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        total += size
    return points[-1]


def travel(f, name, points, period, times=None):
    """A class that moves an element drawn at the origin through points.

    times are the fractions of the period at each point; constant speed if omitted.
    """
    if times is None:
        lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
        total, run, times = sum(lengths), 0, [0]
        for size in lengths:
            run += size
            times.append(run / total)
    frames = [(100 * t, f'transform:translate({num(x)}px,{num(y)}px)') for t, (x, y) in zip(times, points)]
    return keyframes(f, name, frames, period, base=frames[0][1])


# Two-terminal parts, drawn along +x around the origin. Each shape gives the lead
# ends, the half height used to place text, paths as (class, data) and upright marks.

ZIGZAG = 'M -18 0 L -15 -6 L -9 6 L -3 -6 L 3 6 L 9 -6 L 15 6 L 18 0'
COIL = 'M -20 0 a 5 5 0 0 1 10 0 a 5 5 0 0 1 10 0 a 5 5 0 0 1 10 0 a 5 5 0 0 1 10 0'
RING14 = 'M 14 0 A 14 14 0 1 1 -14 0 A 14 14 0 1 1 14 0'
RING13 = 'M 13 0 A 13 13 0 1 1 -13 0 A 13 13 0 1 1 13 0'
DIAMOND = 'M -14 0 L 0 -14 L 14 0 L 0 14 Z'
TRIANGLE = 'M -7 -8 L 7 0 L -7 8 Z'


def _light(inward):
    """Two light arrows over a diode or resistor, into it or out of it."""
    shafts, heads = [], []
    for x in (-3, 5):
        a, b = (x - 4, -11), (x + 4, -20)
        if inward:
            a, b = b, a
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        end = (b[0] - 4 * math.cos(angle), b[1] - 4 * math.sin(angle))
        shafts.append(poly([a, end]))
        heads.append(tip(b[0], b[1], angle, 6))
    return [('thin', ' '.join(shafts)), ('thin solid', ' '.join(heads))]


def _shape(kind):
    if kind == 'R':
        return -18, 18, 8, [('', ZIGZAG)], []
    if kind == 'Riec':
        return -18, 18, 8, [('', 'M -18 -6 H 18 V 6 H -18 Z')], []
    if kind == 'Rvar':
        return -18, 18, 13, [('', ZIGZAG), ('thin', 'M -13 10 L 9.8 -7.5'),
                             ('thin solid', tip(13, -10, math.atan2(-20, 26), 6))], []
    if kind == 'LDR':
        return -18, 18, 22, [('', ZIGZAG)] + _light(True), []
    if kind == 'NTC':
        return -18, 18, 13, [('', ZIGZAG), ('thin', 'M -19 11 H -13 L 13 -11')], [('text:−t°', 22, 13)]
    if kind == 'C':
        return -4, 4, 13, [('', 'M -4 -12 V 12 M 4 -12 V 12')], []
    if kind == 'Cpol':
        return -4, 4.5, 13, [('', 'M -4 -12 V 12 M 8 -12 Q 1 0 8 12')], [('+', -10, -9)]
    if kind == 'L':
        return -20, 20, 8, [('', COIL)], []
    if kind == 'Lcore':
        return -20, 20, 13, [('', COIL), ('thin', 'M -20 -9 H 20 M -20 -12 H 20')], []
    if kind == 'V':
        return -14, 14, 16, [('', RING14)], [('+', -7, 0), ('-', 7, 0)]
    if kind == 'AC':
        return -14, 14, 16, [('', RING14)], [('sine', 0, 0)]
    if kind == 'I':
        return -14, 14, 16, [('', RING14), ('thin', 'M -8 0 H 3'), ('thin solid', 'M 9 0 L 2 -4 L 2 4 Z')], []
    if kind == 'Vdep':
        return -14, 14, 16, [('', DIAMOND)], [('+', -6, 0), ('-', 6, 0)]
    if kind == 'Idep':
        return -14, 14, 16, [('', DIAMOND), ('thin', 'M -7 0 H 3'), ('thin solid', 'M 8 0 L 2 -4 L 2 4 Z')], []
    if kind == 'B':
        return -4, 4, 14, [('', 'M -4 -12 V 12'), ('heavy', 'M 4 -6 V 6')], [('+', -10, -14)]
    if kind == 'B2':
        return -14, 14, 14, [('', 'M -14 -12 V 12 M 6 -12 V 12 M -6 0 H 6'),
                             ('heavy', 'M -6 -6 V 6 M 14 -6 V 6')], [('+', -20, -14)]
    if kind == 'D':
        return -7, 7, 10, [('solid', TRIANGLE), ('', 'M 7 -8 V 8')], []
    if kind == 'Z':
        return -7, 7, 10, [('solid', TRIANGLE), ('', 'M 4 -10 L 7 -8 V 8 L 10 10')], []
    if kind == 'Sch':
        return -7, 7, 10, [('solid', TRIANGLE), ('', 'M 11 -4 V -8 H 7 V 8 H 3 V 4')], []
    if kind == 'LED':
        return -7, 7, 21, [('solid', TRIANGLE), ('', 'M 7 -8 V 8')] + _light(False), []
    if kind == 'PD':
        return -7, 7, 21, [('solid', TRIANGLE), ('', 'M 7 -8 V 8')] + _light(True), []
    if kind == 'SW':
        return -12, 12, 12, [('', 'M -12 0 L 10 -11')], [('o', -12, 0), ('o', 12, 0)]
    if kind == 'SWon':
        return -12, 12, 12, [('', 'M -12 0 L 12 0')], [('o', -12, 0), ('o', 12, 0)]
    if kind == 'PB':
        return -12, 12, 18, [('', 'M -14 -7 H 14 M 0 -7 V -15 M -5 -15 H 5')], [('o', -12, 0), ('o', 12, 0)]
    if kind == 'PBon':
        return -12, 12, 18, [('', 'M -14 -1 H 14 M 0 -1 V -9 M -5 -9 H 5')], [('o', -12, 0), ('o', 12, 0)]
    if kind == 'F':
        return -14, 14, 8, [('', 'M -14 -5 H 14 V 5 H -14 Z M -14 0 H 14')], []
    if kind == 'lamp':
        return -10, 10, 12, [('', 'M 10 0 A 10 10 0 1 1 -10 0 A 10 10 0 1 1 10 0 M -7 -7 L 7 7 M -7 7 L 7 -7')], []
    if kind in ('M', 'Vm', 'Am', 'G'):
        return -13, 13, 15, [('', RING13)], [('letter:' + {'M': 'M', 'Vm': 'V', 'Am': 'A', 'G': 'G'}[kind], 0, 0)]
    if kind == 'X':
        return -8, 8, 13, [('', 'M -8 -9 V 9 M 8 -9 V 9 M -4 -12 H 4 V 12 H -4 Z')], []
    if kind == 'FB':
        return -12, 12, 9, [('', 'M -12 0 H 12'), ('solid', 'M -9 -11 L 3 7 L 9 3 L -3 -15 Z')], []
    raise ValueError(kind)


def _mark(kind, x, y):
    if kind == '+':
        return f'<path class="w thin" d="M {num(x - 3.5)} {num(y)} H {num(x + 3.5)} M {num(x)} {num(y - 3.5)} V {num(y + 3.5)}"/>'
    if kind == '-':
        return f'<path class="w thin" d="M {num(x - 3.5)} {num(y)} H {num(x + 3.5)}"/>'
    if kind == 'sine':
        return (f'<path class="w thin" d="M {num(x - 8)} {num(y)} C {num(x - 5)} {num(y - 10)} {num(x - 3)} '
                f'{num(y - 10)} {num(x)} {num(y)} S {num(x + 5)} {num(y + 10)} {num(x + 8)} {num(y)}"/>')
    if kind == 'o':
        return f'<circle class="w hollow" cx="{num(x)}" cy="{num(y)}" r="2.6"/>'
    if kind.startswith('letter:'):
        return f'<text class="t mark" x="{num(x)}" y="{num(y + 5)}" text-anchor="middle">{escape(kind[7:])}</text>'
    if kind.startswith('text:'):
        return f'<text class="t s" x="{num(x)}" y="{num(y + 4)}" text-anchor="middle">{escape(kind[5:])}</text>'
    raise ValueError(kind)


def two(f, kind, a, b, label=None, value=None, side=1, flip=False, cls='w'):
    """A two-terminal part from a to b; a is the + or anode end. Returns the body's centre."""
    (x1, y1), (x2, y2) = a, b
    left, right, half, paths, marks = _shape(kind)
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    angle = math.degrees(math.atan2(uy, ux))
    f.add(f'<path class="{cls}" d="{poly([(x1, y1), (cx + ux * left, cy + uy * left)])}"/>',
          f'<path class="{cls}" d="{poly([(cx + ux * right, cy + uy * right), (x2, y2)])}"/>')
    mirror = ' scale(1 -1)' if flip else ''
    body = ''.join(f'<path class="{cls}{" " + extra if extra else ""}" d="{d}"/>' for extra, d in paths)
    f.add(f'<g transform="translate({num(cx)} {num(cy)}) rotate({num(angle)}){mirror}">{body}</g>')
    for mark, lx, ly in marks:
        ly = -ly if flip else ly
        f.add(_mark(mark, cx + lx * ux - ly * uy, cy + lx * uy + ly * ux))
    _labels(f, cx, cy, ux, uy, half, label, value, side)
    return cx, cy


def _labels(f, cx, cy, ux, uy, half, label, value, side):
    lines = [s for s in (label, value) if s]
    if not lines:
        return
    if abs(ux) >= abs(uy):
        if side > 0:
            ys = [cy - half - 6 - 15 * (len(lines) - 1 - i) for i in range(len(lines))]
        else:
            ys = [cy + half + 15 + 15 * i for i in range(len(lines))]
        for s, y in zip(lines, ys):
            text(f, cx, y, s)
    else:
        x = cx + side * (half + 6)
        anchor = 'start' if side > 0 else 'end'
        top = cy + 4 - 7.5 * (len(lines) - 1)
        for i, s in enumerate(lines):
            text(f, x, top + 15 * i, s, anchor)


def pot(f, a, b, label=None, value=None, side=1):
    """A potentiometer from a to b with its wiper arrow on one side; returns the wiper end."""
    cx, cy = two(f, 'R', a, b, label, value, -side)
    (x1, y1), (x2, y2) = a, b
    length = math.hypot(x2 - x1, y2 - y1)
    nx, ny = (y2 - y1) / length * side, -(x2 - x1) / length * side
    start = (cx + nx * 24, cy + ny * 24)
    arrow(f, start[0], start[1], cx + nx * 7, cy + ny * 7, 'w', 8)
    return start


def transformer(f, x, y, core=True):
    """Primary on the left, secondary on the right; returns the four lead ends."""
    path(f, f'M {num(x - 26)} {num(y - 20)} H {num(x - 10)} '
            f'a 5 5 0 0 1 0 10 a 5 5 0 0 1 0 10 a 5 5 0 0 1 0 10 a 5 5 0 0 1 0 10 H {num(x - 26)} '
            f'M {num(x + 26)} {num(y - 20)} H {num(x + 10)} '
            f'a 5 5 0 0 0 0 10 a 5 5 0 0 0 0 10 a 5 5 0 0 0 0 10 a 5 5 0 0 0 0 10 H {num(x + 26)}')
    if core:
        path(f, f'M {num(x - 2)} {num(y - 22)} V {num(y + 22)} M {num(x + 2)} {num(y - 22)} V {num(y + 22)}', 'w thin')
    return {'P1': (x - 26, y - 20), 'P2': (x - 26, y + 20), 'S1': (x + 26, y - 20), 'S2': (x + 26, y + 20)}


# Rails and references.

def ground(f, x, y, lead=10):
    f.add(f'<path class="w" d="M {num(x)} {num(y)} V {num(y + lead)} M {num(x - 11)} {num(y + lead)} H {num(x + 11)} '
          f'M {num(x - 7)} {num(y + lead + 4.5)} H {num(x + 7)} M {num(x - 3)} {num(y + lead + 9)} H {num(x + 3)}"/>')


def chassis(f, x, y, lead=10):
    f.add(f'<path class="w" d="M {num(x)} {num(y)} V {num(y + lead)} M {num(x - 11)} {num(y + lead)} H {num(x + 11)} '
          f'M {num(x - 11)} {num(y + lead)} l -5 7 M {num(x)} {num(y + lead)} l -5 7 M {num(x + 11)} {num(y + lead)} l -5 7"/>')


def common(f, x, y, lead=10):
    f.add(f'<path class="w" d="M {num(x)} {num(y)} V {num(y + lead)} M {num(x - 9)} {num(y + lead)} '
          f'H {num(x + 9)} L {num(x)} {num(y + lead + 10)} Z"/>')


def rail(f, x, y, label, lead=10):
    f.add(f'<path class="w" d="M {num(x)} {num(y)} V {num(y - lead)} M {num(x - 9)} {num(y - lead)} H {num(x + 9)}"/>')
    text(f, x, y - lead - 7, label)


def net(f, x, y, label, direction='r'):
    """A net label flag on a wire end at (x, y), pointing r or l."""
    width = 9 + 7.8 * len(label)
    sign = 1 if direction == 'r' else -1
    path(f, f'M {num(x)} {num(y)} l {num(sign * 7)} -8 h {num(sign * width)} v 16 h {num(-sign * width)} Z', 'w thin')
    text(f, x + sign * (7 + width / 2), y + 4.5, label, 'middle', 't s')


# Three-terminal and larger parts. Each returns its pins.

def bjt(f, x, y, pnp=False, label=None, ring=True):
    pins = {'B': (x - 22, y), 'C': (x + 8, y - 24), 'E': (x + 8, y + 24)}
    if pnp:
        pins['C'], pins['E'] = pins['E'], pins['C']
    if ring:
        circle(f, x + 1, y, 17, 'w thin')
    path(f, f'M {num(x - 22)} {num(y)} H {num(x - 6)} M {num(x - 6)} {num(y - 11)} V {num(y + 11)} '
            f'M {num(x - 6)} {num(y - 5)} L {num(x + 8)} {num(y - 14)} V {num(y - 24)} '
            f'M {num(x - 6)} {num(y + 5)} L {num(x + 8)} {num(y + 14)} V {num(y + 24)}')
    # The emitter arrow points out of an NPN and into a PNP.
    if pnp:
        f.add(head(x - 3.2, y - 6.8, math.atan2(9, -14), 7))
    else:
        f.add(head(x + 6, y + 12.7, math.atan2(9, 14), 7))
    if label:
        text(f, x + 22, y + 4, label, 'start')
    return pins


def mosfet(f, x, y, p=False, label=None):
    """Enhancement MOSFET with its body tied to the source."""
    if p:
        pins = {'G': (x - 22, y - 8), 'S': (x + 8, y - 24), 'D': (x + 8, y + 24)}
    else:
        pins = {'G': (x - 22, y + 8), 'D': (x + 8, y - 24), 'S': (x + 8, y + 24)}
    gate_y = pins['G'][1]
    path(f, f'M {num(x - 22)} {num(gate_y)} H {num(x - 9)} M {num(x - 9)} {num(y - 10)} V {num(y + 10)} '
            f'M {num(x - 4)} {num(y - 12)} V {num(y - 5)} M {num(x - 4)} {num(y - 3.5)} V {num(y + 3.5)} '
            f'M {num(x - 4)} {num(y + 5)} V {num(y + 12)} '
            f'M {num(x - 4)} {num(y - 8.5)} H {num(x + 8)} V {num(y - 24)} '
            f'M {num(x - 4)} {num(y + 8.5)} H {num(x + 8)} V {num(y + 24)} '
            f'M {num(x - 4)} {num(y)} H {num(x + 8)} V {num(y + (-8.5 if p else 8.5))}')
    # The body arrow points into the channel for N, out of it for P.
    f.add(head(x + 7, y, 0, 7) if p else head(x - 3.5, y, math.pi, 7))
    if label:
        text(f, x + 18, y + 4, label, 'start')
    return pins


def opamp(f, x, y, plus_top=False, label=None, supplies=False):
    """Triangle from x-20 to x+24; inputs at y±12; returns pins at the lead ends."""
    path(f, f'M {num(x - 20)} {num(y - 26)} L {num(x + 24)} {num(y)} L {num(x - 20)} {num(y + 26)} Z')
    top, bottom = ('+', '-') if plus_top else ('-', '+')
    path(f, f'M {num(x - 32)} {num(y - 12)} H {num(x - 20)} M {num(x - 32)} {num(y + 12)} H {num(x - 20)} '
            f'M {num(x + 24)} {num(y)} H {num(x + 36)}')
    f.add(_mark(top, x - 13, y - 12), _mark(bottom, x - 13, y + 12))
    pins = {top: (x - 32, y - 12), bottom: (x - 32, y + 12), 'out': (x + 36, y)}
    if supplies:
        path(f, f'M {num(x)} {num(y - 16)} V {num(y - 30)} M {num(x)} {num(y + 16)} V {num(y + 30)}')
        pins['V+'], pins['V-'] = (x, y - 30), (x, y + 30)
    if label:
        text(f, x - 2, y + 4, label, 'middle', 't s')
    return pins


_GATE = {
    'AND': ('M -18 -16 H 0 A 16 16 0 0 1 0 16 H -18 Z', -18, 16),
    'OR': ('M -20 -16 Q 4 -16 16 0 Q 4 16 -20 16 Q -12 0 -20 -16 Z', -17, 16),
    'XOR': ('M -20 -16 Q 4 -16 16 0 Q 4 16 -20 16 Q -12 0 -20 -16 Z M -25 -16 Q -17 0 -25 16', -22, 16),
    'BUF': ('M -14 -13 L 14 0 L -14 13 Z', -14, 14),
}
_IEC = {'AND': '&amp;', 'OR': '≥1', 'XOR': '=1', 'BUF': '1'}


def gate(f, kind, x, y, iec=False, inputs=2, label=None):
    """A logic gate centred at (x, y); NAND, NOR, XNOR and NOT add the bubble."""
    base = {'NAND': 'AND', 'NOR': 'OR', 'XNOR': 'XOR', 'NOT': 'BUF'}.get(kind, kind)
    inverted = kind in ('NAND', 'NOR', 'XNOR', 'NOT')
    if iec:
        rect(f, x - 16, y - 18, 32, 36)
        f.add(f'<text class="t mark" x="{num(x)}" y="{num(y - 3)}" text-anchor="middle">{_IEC[base]}</text>')
        back, front = -16, 16
    else:
        shape, back, front = _GATE[base]
        f.add(f'<g transform="translate({num(x)} {num(y)})"><path class="w" d="{shape}"/></g>')
    if inverted:
        circle(f, x + front + 3, y, 3, 'w hollow')
    out = front + (6 if inverted else 0)
    ys = [0] if base == 'BUF' or inputs == 1 else [-8, 8] if inputs == 2 else [-10, 0, 10]
    pins = {}
    for name, dy in zip('ABC', ys):
        path(f, f'M {num(x - 30)} {num(y + dy)} H {num(x + back)}')
        pins[name] = (x - 30, y + dy)
    path(f, f'M {num(x + out)} {num(y)} H {num(x + 30)}')
    pins['Y'] = (x + 30, y)
    if label:
        text(f, x, y - 24, label)
    return pins


def dff(f, x, y, label='D flip-flop'):
    rect(f, x - 24, y - 30, 48, 60)
    path(f, f'M {num(x - 24)} {num(y + 12)} L {num(x - 16)} {num(y + 17)} L {num(x - 24)} {num(y + 22)}')
    pins = {'D': (x - 38, y - 15), 'CLK': (x - 38, y + 17), 'Q': (x + 38, y - 15), 'Qn': (x + 38, y + 15)}
    path(f, f'M {num(x - 38)} {num(y - 15)} H {num(x - 24)} M {num(x - 38)} {num(y + 17)} H {num(x - 24)} '
            f'M {num(x + 24)} {num(y - 15)} H {num(x + 38)} M {num(x + 24)} {num(y + 15)} H {num(x + 38)}')
    for s, px, py, anchor in (('D', x - 20, y - 11, 'start'), ('Q', x + 20, y - 11, 'end')):
        f.add(f'<text class="t s" x="{num(px)}" y="{num(py)}" text-anchor="{anchor}">{s}</text>')
    f.add(f'<text class="t s" x="{num(x + 20)}" y="{num(y + 19)}" text-anchor="end">'
          f'<tspan text-decoration="overline">Q</tspan></text>')
    if label:
        text(f, x, y - 38, label)
    return pins


def chip(f, x, y, w, h, name, left=(), right=(), top=(), bottom=(), pitch=20):
    """A box with named pins; each side lists pin names, evenly spaced; '' leaves a gap."""
    rect(f, x, y, w, h)
    if name:
        text(f, x + w / 2, y + h / 2 + 4, name)
    pins = {}

    def side(names, origin, length, fixed, horizontal, outward):
        start = origin + (length - pitch * (len(names) - 1)) / 2
        for i, pin in enumerate(names):
            if not pin:
                continue
            pos = start + pitch * i
            if horizontal:
                path(f, f'M {num(pos)} {num(fixed)} V {num(fixed + outward * 12)}')
                pins[pin] = (pos, fixed + outward * 12)
                f.add(f'<text class="t s" x="{num(pos)}" y="{num(fixed - outward * 7 + (4 if outward > 0 else 0))}" '
                      f'text-anchor="middle">{rich(pin)}</text>')
            else:
                path(f, f'M {num(fixed)} {num(pos)} H {num(fixed + outward * 12)}')
                pins[pin] = (fixed + outward * 12, pos)
                f.add(f'<text class="t s" x="{num(fixed - outward * 5)}" y="{num(pos + 4)}" '
                      f'text-anchor="{"start" if outward < 0 else "end"}">{rich(pin)}</text>')
    side(left, y, h, x, False, -1)
    side(right, y, h, x + w, False, 1)
    side(top, x, w, y, True, -1)
    side(bottom, x, w, y + h, True, 1)
    return pins


# Plots.

class Plot:
    """Axes in a figure; X and Y map data to user units, optionally on log scales."""

    def __init__(self, f, x, y, w, h, xr, yr, xlog=False, ylog=False):
        self.f, self.x, self.y, self.w, self.h = f, x, y, w, h
        self.xr, self.yr, self.xlog, self.ylog = xr, yr, xlog, ylog

    def X(self, v):
        a, b = self.xr
        if self.xlog:
            return self.x + (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) * self.w
        return self.x + (v - a) / (b - a) * self.w

    def Y(self, v):
        a, b = self.yr
        if self.ylog:
            return self.y + self.h - (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) * self.h
        return self.y + self.h - (v - a) / (b - a) * self.h

    def axes(self, xlabel=None, ylabel=None, xticks=(), yticks=(), grid=False, xzero=None, yzero=None):
        f = self.f
        y0 = self.Y(yzero) if yzero is not None else self.y + self.h
        x0 = self.X(xzero) if xzero is not None else self.x
        if grid:
            for value, _ in xticks:
                line(f, self.X(value), self.y, self.X(value), self.y + self.h, 'grid')
            for value, _ in yticks:
                line(f, self.x, self.Y(value), self.x + self.w, self.Y(value), 'grid')
        arrow(f, self.x, y0, self.x + self.w + 10, y0, 'w thin', 6)
        arrow(f, x0, self.y + self.h, x0, self.y - 10, 'w thin', 6)
        for value, name in xticks:
            px = self.X(value)
            line(f, px, y0, px, y0 + 4, 'w thin')
            if name:
                f.add(f'<text class="t s" x="{num(px)}" y="{num(y0 + 16)}" text-anchor="middle">{rich(name)}</text>')
        for value, name in yticks:
            py = self.Y(value)
            line(f, x0 - 4, py, x0, py, 'w thin')
            if name:
                f.add(f'<text class="t s" x="{num(x0 - 7)}" y="{num(py + 4)}" text-anchor="end">{rich(name)}</text>')
        if xlabel:
            text(f, self.x + self.w + 14, y0 + 4, xlabel, 'start')
        if ylabel:
            text(f, x0, self.y - 18, ylabel)

    def points(self, fn, a=None, b=None, samples=240):
        a = self.xr[0] if a is None else a
        b = self.xr[1] if b is None else b
        out = []
        for i in range(samples + 1):
            if self.xlog:
                v = 10 ** (math.log10(a) + (math.log10(b) - math.log10(a)) * i / samples)
            else:
                v = a + (b - a) * i / samples
            out.append((v, fn(v)))
        return out

    def curve(self, data, cls='w curve', clip=True):
        """A polyline through (x, y) data or a function of x, cut off where it leaves
        the y range; returns the drawn points."""
        if callable(data):
            data = list(self.points(data))
        runs = [data] if not clip else []
        if clip:
            lo, hi = sorted(self.yr)
            for (x1, y1), (x2, y2) in zip(data, data[1:]):
                dy = y2 - y1
                if dy:
                    t0, t1 = sorted(((lo - y1) / dy, (hi - y1) / dy))
                    t0, t1 = max(t0, 0), min(t1, 1)
                elif lo <= y1 <= hi:
                    t0, t1 = 0, 1
                else:
                    continue
                if t0 > t1:
                    continue
                a = (x1 + (x2 - x1) * t0, y1 + dy * t0)
                b = (x1 + (x2 - x1) * t1, y1 + dy * t1)
                if runs and runs[-1][-1] == a:
                    runs[-1].append(b)
                else:
                    runs.append([a, b])
        screen = [[(self.X(vx), self.Y(vy)) for vx, vy in run] for run in runs]
        self.f.add(f'<path class="{cls}" d="{" ".join(poly(run) for run in screen)}"/>')
        return [point for run in screen for point in run]

    def mark(self, vx, vy, label=None, anchor='start', dx=6, dy=-6):
        dot(self.f, self.X(vx), self.Y(vy), 3)
        if label:
            text(self.f, self.X(vx) + dx, self.Y(vy) + dy, label, anchor, 't s')
