import math

from draw import (Figure, Plot, arrow, begin, circle, dimension, dot, end, flow, ground, line, num, path, phases, poly,
                  rect, text, wire)
from page import eq, fig, link, note, ol, p, table

NAME = '10-pcb'
TITLE = 'PCB design'
LEDE = ('From circuit to board: the design steps, layers and stack-ups, how wide a track must be, where return '
        'currents flow, placing decoupling capacitors, controlled impedance, footprints, the files a fab needs, '
        'and bringing a new board to life.')

STEPS = (
    ('schematic', 'Draw the circuit: every part, and which pins connect. That list of connections is the netlist.'),
    ('footprints', "Give each symbol a footprint: the real part's pads and outline, from its datasheet."),
    ('placement', 'Place connectors and fixed parts first, then chips, then decoupling capacitors beside their pins.'),
    ('routing', 'Draw copper tracks for each net: power and fast signals first, over an unbroken ground plane.'),
    ('checks', 'The electrical rules check finds unconnected pins; the design rules check finds tracks too close.'),
    ('Gerbers', 'Export a Gerber file for each layer and a drill file: the fab makes exactly what these show.'),
    ('fabrication', 'The fab etches the copper, drills and plates the holes, then adds solder mask and silkscreen.'),
    ('assembly', 'Paste goes on through a stencil, parts are placed, and an oven melts the solder; or solder by hand.'),
    ('bring-up', 'Check for shorts, power up with a current limit, then test one part of the circuit at a time.'),
)


def workflow():
    f = Figure(900, 220, 'The steps from a circuit to a working board')
    boxes = [(40 + 170 * k, 30) for k in range(5)] + [(720 - 170 * k, 112) for k in range(4)]
    for (x, y), (name, _) in zip(boxes, STEPS):
        rect(f, x, y, 140, 44, 'w thin', 4)
        text(f, x + 70, y + 27, name)
    for (x1, y1), (x2, y2) in zip(boxes, boxes[1:]):
        if y1 != y2:
            arrow(f, x1 + 70, y1 + 48, x2 + 70, y2 - 4)
        elif x2 > x1:
            arrow(f, x1 + 144, y1 + 22, x2 - 4, y2 + 22)
        else:
            arrow(f, x1 - 4, y1 + 22, x2 + 144, y2 + 22)
    for k, cls in enumerate(phases(f, len(STEPS), 2 * len(STEPS))):
        x, y = boxes[k]
        begin(f, cls)
        rect(f, x - 4, y - 4, 148, 52, 'w', 6)
        text(f, 450, 200, f'{k + 1}. {STEPS[k][1]}', 'middle', 't s')
        end(f)
    return f


def section(f, x, y, width, layers, title):
    """A board cut through, top layer first: layers are (kind, height, label) with kind signal,
    plane or dielectric. A plated via joins the outer layers and passes the planes by."""
    tracks, via = ((0.04, 0.2), (0.3, 0.42), (0.74, 0.92)), x + 0.58 * width
    rows, top = [], y
    for kind, height, label in layers:
        rows.append((kind, top, height, label))
        top += height
    bottom = top
    rect(f, x, y, width, bottom - y, 'shade')
    for kind, top, height, label in rows:
        if kind == 'signal':
            for a, b in tracks:
                rect(f, x + a * width, top, (b - a) * width, height, 'fill')
            rect(f, via - 12, top, 24, height, 'fill')
        elif kind == 'plane':
            rect(f, x, top, via - 14 - x, height, 'fill')
            rect(f, via + 14, top, x + width - via - 14, height, 'fill')
        text(f, x + width + 10, top + height / 2 + 4, label, 'start', 't s')
    rect(f, via - 4, y, 8, bottom - y, 'hollow')
    for side in (-6, 4):
        rect(f, via + side, y, 2, bottom - y, 'fill')
    pad = x + tracks[0][0] * width, x + tracks[0][1] * width
    silk = x + 0.76 * width, x + 0.9 * width
    rect(f, x, y - 3, pad[0] - 3 - x, 3, 'shade2')
    rect(f, pad[1] + 3, y - 3, x + width - pad[1] - 3, 3, 'shade2')
    rect(f, x, bottom, width, 3, 'shade2')
    rect(f, silk[0], y - 6, silk[1] - silk[0], 3, 'fill')
    rect(f, x, y - 3, width, bottom - y + 6, 'w thin faint')
    for at, name in ((sum(pad) / 2, 'pad'), (via, 'via'), (sum(silk) / 2, 'silkscreen')):
        text(f, at, y - 14, name, 'middle', 't s')
    text(f, x + width / 2, 284, title, 'middle', 't head')


def stackup():
    f = Figure(900, 300, 'Cross-sections of a two-layer and a four-layer board')
    section(f, 40, 70, 250, (('signal', 6, 'top copper'), ('dielectric', 150, 'FR-4 core 1.5 mm'),
                             ('signal', 6, 'bottom copper')), 'TWO LAYERS')
    section(f, 470, 70, 250, (('signal', 6, 'L1: signals'), ('dielectric', 30, 'prepreg 0.2 mm'),
                              ('plane', 6, 'L2: ground'), ('dielectric', 90, 'core 1.1 mm'),
                              ('plane', 6, 'L3: power'), ('dielectric', 30, 'prepreg 0.2 mm'),
                              ('signal', 6, 'L4: signals')), 'FOUR LAYERS')
    return f


def track_width(current, rise=10, k=0.048, ounces=1):
    """The track width in mm to carry a current with a given temperature rise, by IPC-2221."""
    area = (current / (k * rise ** 0.44)) ** (1 / 0.725)
    return area / (1.378 * ounces) * 0.0254


WIDTHS = (('outer layer, 10 °C rise', 10, 0.048, 'w curve'), ('outer layer, 20 °C rise', 20, 0.048, 'w curve dash'),
          ('inner layer, 10 °C rise', 10, 0.024, 'w curve dots'))


def widths():
    f = Figure(900, 280, 'The track width needed to carry a current in 1 oz copper, from IPC-2221')
    plot = Plot(f, 110, 30, 520, 200, (0, 5), (0, 4))
    plot.axes('I', 'w', [(k, f'{k} A' if k else '0') for k in range(6)],
              [(k, f'{k} mm') for k in range(1, 5)], grid=True)
    for k, (name, rise, factor, cls) in enumerate(WIDTHS):
        plot.curve(lambda current: track_width(current, rise, factor), cls)
        line(f, 670, 60 + 26 * k, 710, 60 + 26 * k, cls)
        text(f, 720, 64 + 26 * k, name, 'start', 't s')
    plot.mark(4, track_width(4), f'4 A: {track_width(4):.2f} mm', 'end', -8, -8)
    return f


def return_paths():
    f = Figure(900, 330, 'Where the return current of a signal flows in the ground plane beneath it')
    rect(f, 40, 20, 820, 250, 'shade')
    text(f, 56, 40, 'ground plane, on the layer below', 'start', 't s')
    track = [(130, 170), (130, 60), (770, 60), (770, 170)]
    under = [(710, 215), (756, 180), (756, 74), (144, 74), (144, 180), (190, 215)]
    detour = under[:3] + [(466, 74), (466, 212), (434, 212), (434, 74)] + under[3:]
    states = (
        ([[(710, 215), (190, 215)], [(710, 215), (600, 172), (300, 172), (190, 215)],
          [(710, 215), (600, 252), (300, 252), (190, 215)]], False,
         'At DC the return current spreads out and takes the paths of least resistance,',
         'straight between the two ground connections.'),
        ([under], False, 'At high frequency it crowds beneath the track, the path of least inductance,',
         'which keeps the loop of signal and return as small as it can be.'),
        ([detour], True, 'A slot cut in the plane forces the return current around it. The larger loop',
         'radiates and picks up noise: never route a fast signal across a gap in its plane.'))
    for cls, (paths, slot, *words) in zip(phases(f, 3, 12), states):
        begin(f, cls)
        if slot:
            rect(f, 440, 20, 20, 180, 'hollow')
            text(f, 450, 236, 'slot in the plane', 'middle', 't s')
        for points in paths:
            rings(f, points, 1.6)
        for k, words_line in enumerate(words):
            text(f, 450, 300 + 18 * k, words_line, 'middle', 't s')
        end(f)
    wire(f, *track, cls='w bold')
    flow(f, track, 1.6)
    text(f, 620, 50, 'track, on the top layer', 'middle', 't s')
    for x, via, name in ((90, 190, 'U1'), (730, 710, 'U2')):
        rect(f, x, 170, 80, 60, 'w hollow')
        text(f, x + 40, 205, name)
        wire(f, (x if via > x else x + 80, 215), (via, 215))
        circle(f, via, 215, 5)
    return f


def rings(f, points, period):
    """Moving rings: return current in a plane, beneath the tracks drawn above it."""
    d = poly(points)
    style = f' style="--t:{num(period)}s"'
    f.add(f'<path class="flow-halo" d="{d}"{style}/>', f'<path class="flow hole" d="{d}"{style}/>',
          f'<path class="flow hole-in" d="{d}"{style}/>')


def via(f, x, y):
    """A via down to the ground plane."""
    circle(f, x, y, 5)
    ground(f, x, y + 5, 6)


def placement():
    f = Figure(900, 250, 'A decoupling capacitor placed far from a chip, and beside its pins')
    for ox, close in ((30, False), (480, True)):
        rect(f, ox + 40, 40, 120, 150)
        text(f, ox + 100, 120, 'IC')
        for y, name in ((88, 'VDD'), (110, 'GND')):
            rect(f, ox + 160, y, 18, 10, 'fill')
            text(f, ox + 154, y + 9, name, 'end', 't s')
        cap = ox + (205 if close else 350)
        top = 88 if close else 128
        rect(f, cap - 10, top - 4, 20, 40, 'w thin dim')
        rect(f, cap - 7, top, 14, 10, 'fill')
        rect(f, cap - 7, top + 22, 14, 10, 'fill')
        if close:
            text(f, cap, top - 10, '100 nF', 'middle', 't s')
        else:
            text(f, cap + 16, top + 20, '100 nF', 'start', 't s')
        if close:
            wire(f, (ox + 178, 93), (cap - 7, 93), cls='w bold')
            wire(f, (ox + 178, 115), (cap - 7, 115), cls='w bold')
            wire(f, (cap + 7, 115), (cap + 22, 115), cls='w bold')
            via(f, cap + 27, 115)
            flow(f, [(cap - 7, 93), (ox + 178, 93)])
            flow(f, [(ox + 178, 115), (cap - 7, 115)])
            text(f, ox + 210, 24, 'BESIDE THE PINS: A SHORT PATH', 'middle', 't head')
        else:
            wire(f, (ox + 178, 93), (cap, 93), (cap, top), cls='w bold')
            wire(f, (cap, top + 32), (cap, top + 50), cls='w bold')
            via(f, cap, top + 55)
            wire(f, (ox + 178, 115), (ox + 192, 115), cls='w bold')
            via(f, ox + 197, 115)
            flow(f, [(cap, top), (cap, 93), (ox + 178, 93)])
            flow(f, [(ox + 178, 115), (ox + 192, 115)])
            flow(f, [(cap, top + 50), (cap, top + 32)])
            text(f, ox + 210, 24, 'FAR AWAY: A LONG PATH', 'middle', 't head')
    return f


def impedance(width, height=0.2, permittivity=4.3, thickness=0.035):
    """Microstrip impedance in ohms, by the IPC-2141 approximation; lengths in mm."""
    return 87 / math.sqrt(permittivity + 1.41) * math.log(5.98 * height / (0.8 * width + thickness))


def width_for(ohms, height, permittivity=4.3, thickness=0.035):
    """The track width in mm that gives a microstrip impedance, from the same approximation."""
    return (5.98 * height * math.exp(-ohms * math.sqrt(permittivity + 1.41) / 87) - thickness) / 0.8


def effective(width, height, permittivity=4.3):
    """The effective permittivity a microstrip's signal sees, part in the board and part in air."""
    return (permittivity + 1) / 2 + (permittivity - 1) / 2 / math.sqrt(1 + 12 * height / width)


def microstrip():
    f = Figure(900, 280, 'A microstrip track over its ground plane, and its impedance against width')
    rect(f, 60, 120, 300, 80, 'shade')
    rect(f, 60, 200, 300, 8, 'fill')
    rect(f, 175, 112, 70, 8, 'fill')
    for x in (190, 210, 230):
        line(f, x, 122, x, 198, 'w thin dim')
    path(f, 'M 175 118 Q 120 122 100 198', 'w thin dim')
    path(f, 'M 245 118 Q 300 122 320 198', 'w thin dim')
    path(f, 'M 177 120 Q 150 130 145 198', 'w thin dim')
    path(f, 'M 243 120 Q 270 130 275 198', 'w thin dim')
    dimension(f, 175, 96, 245, 96, 'w', (210, 88))
    dimension(f, 44, 120, 44, 200, 'h', (36, 164), 'end')
    line(f, 249, 112, 262, 112, 'w thin faint')
    line(f, 249, 120, 262, 120, 'w thin faint')
    text(f, 268, 120, 't', 'start', 't s')
    text(f, 340, 140, 'ε_r', 'end')
    text(f, 210, 228, 'ground plane', 'middle', 't s')
    text(f, 210, 248, 'field lines from track to plane', 'middle', 't s')
    plot = Plot(f, 500, 30, 340, 190, (0.05, 5), (30, 160), xlog=True)
    plot.axes('w', 'Z_0', [(v, f'{v:g}') for v in (0.05, 0.1, 0.2, 0.5, 1, 2)] + [(5, '5 mm')],
              [(50, '50 Ω'), (100, '100 Ω'), (150, '150 Ω')], grid=True)
    plot.curve([(0.05, 50), (5, 50)], 'w thin dash')
    for k, (height, cls) in enumerate(((0.2, 'w curve'), (1.6, 'w curve dash'))):
        data = plot.points(lambda width: impedance(width, height), max(0.05, 0.1 * height), 2 * height)
        plot.curve(data, cls)
        target = width_for(50, height)
        plot.mark(target, 50)
        text(f, plot.X(target), plot.Y(50) + 16, f'{target:.2f} mm', 'middle', 't s')
        line(f, 500 + 190 * k, 266, 530 + 190 * k, 266, cls)
        text(f, 538 + 190 * k, 270, f'{height:g} mm above the plane', 'start', 't s')
    return f


MM = 12

FOOTPRINTS = (
    ('DIP-8', '2.54 mm', 100, (9.8, 6.35), 'dip'),
    ('SOIC-8', '1.27 mm', 228, (4.9, 3.9), [(x, y, 0.6, 1.55) for x in (-1.905, -0.635, 0.635, 1.905)
                                             for y in (-2.7, 2.7)]),
    ('QFN-32', '0.5 mm', 338, (5, 5), [(x, y, 0.25, 0.75) for x in [0.5 * k - 1.75 for k in range(8)]
                                        for y in (-2.4, 2.4)] +
     [(y, x, 0.75, 0.25) for x in [0.5 * k - 1.75 for k in range(8)] for y in (-2.4, 2.4)] +
     [(0, 0, 3.3, 3.3)]),
    ('SOT-23', '0.95 mm', 438, (2.9, 1.3), [(-0.95, 1.0, 0.6, 1.1), (0.95, 1.0, 0.6, 1.1), (0, -1.0, 0.6, 1.1)]),
    ('1206', '3.2×1.6', 530, (3.2, 1.6), [(x, 0, 1.15, 1.8) for x in (-1.475, 1.475)]),
    ('0805', '2.0×1.25', 612, (2.0, 1.25), [(x, 0, 1.0, 1.45) for x in (-0.95, 0.95)]),
    ('0603', '1.6×0.8', 684, (1.6, 0.8), [(x, 0, 0.8, 0.95) for x in (-0.825, 0.825)]),
    ('0402', '1.0×0.5', 746, (1.0, 0.5), [(x, 0, 0.6, 0.6) for x in (-0.5, 0.5)]),
)


def footprints():
    f = Figure(900, 230, 'Common footprints drawn to scale: copper pads in white, part outlines dim')
    cy = 104
    for name, pitch, cx, (bw, bh), pads in FOOTPRINTS:
        if pads == 'dip':
            for k, x in enumerate((-3.81, -1.27, 1.27, 3.81)):
                for y in (-3.81, 3.81):
                    if k == 0 and y > 0:
                        rect(f, cx + (x - 0.8) * MM, cy + (y - 0.8) * MM, 1.6 * MM, 1.6 * MM, 'fill')
                    else:
                        dot(f, cx + x * MM, cy + y * MM, 0.8 * MM)
                    dot(f, cx + x * MM, cy + y * MM, 0.4 * MM, 'hollow')
            path(f, f'M {num(cx - bw / 2 * MM)} {num(cy - 9)} A 9 9 0 0 1 {num(cx - bw / 2 * MM)} {num(cy + 9)}',
                 'w thin dim')
        else:
            for x, y, w, h in pads:
                rect(f, cx + (x - w / 2) * MM, cy + (y - h / 2) * MM, w * MM, h * MM, 'fill')
        rect(f, cx - bw / 2 * MM, cy - bh / 2 * MM, bw * MM, bh * MM, 'w thin dim')
        text(f, cx, 190, name, 'middle')
        text(f, cx, 208, pitch, 'middle', 't s')
    dimension(f, 800, 160, 860, 160, '5 mm', (830, 150))
    text(f, 830, 190, 'scale', 'middle')
    text(f, 830, 208, '12 px per mm', 'middle', 't s')
    return f


def sections():
    one_amp, two_amps = track_width(1), track_width(2)
    sheet = 1.72e-8 / 35e-6
    squares = 100 / 0.25
    w50, w50_thick = width_for(50, 0.2), width_for(50, 1.6)
    speed = 299.792458 / math.sqrt(effective(w50, 0.2))
    inner = 299.792458 / math.sqrt(4.3)
    return [
        ('workflow', 'From circuit to board', [
            p('A printed circuit board, PCB, holds the parts and joins them with copper. Designing one is a '
              'sequence of steps, each checked before the next; a PCB design program such as KiCad, which is '
              'free, handles all of them.'),
            fig(workflow(), 'Each step in turn. Most errors are cheap to fix at the first four steps and costly '
                'after the fifth.'),
            p('The schematic is the source of truth: the board is checked against it. Keep it readable, with '
              'inputs on the left, outputs on the right and named nets instead of long wires '
              f'({link("01-symbols", label="Schematic symbols")}).'),
        ]),
        ('stackup', 'Layers and stack-up', [
            p('A board is a stack of insulating layers, usually the glass-fibre epoxy called FR-4, with copper '
              'between them. A two-layer board has copper on both faces of one core. A four-layer board adds '
              'two inner layers, normally used as solid ground and power planes, and is the easiest way to '
              'make a fast or radio circuit work.'),
            fig(stackup(), 'Not to scale: the copper is far thinner than drawn. Grey is solder mask, which '
                'covers the copper except where parts are soldered; the white block on top is silkscreen. '
                'The via, a plated hole, joins the outer layers and passes the planes through clearance '
                'gaps.'),
            table(['Term', 'Meaning'],
                  ['1 oz copper', '35 µm thick: one ounce of copper spread over a square foot; 2 oz is 70 µm'],
                  ['FR-4', 'glass-fibre epoxy; relative permittivity about 4.3, standard board 1.6 mm thick'],
                  ['core and prepreg', 'core is cured board with copper on both sides; prepreg is the bonding '
                   'layer pressed between cores'],
                  ['via', 'a plated hole joining layers; through-hole vias run through the whole board'],
                  ['solder mask', 'the coloured coating; its openings, over pads, are where solder goes'],
                  ['silkscreen', 'printed text and part outlines'],
                  ['surface finish', 'the coating on exposed copper: HASL, solder dipped, or ENIG, flat '
                   'nickel and gold']),
        ]),
        ('tracks', 'Track width and current', [
            p('A track heats up as current flows in it. The older IPC-2221 standard gives the current a track '
              'carries for a temperature rise, from its cross-section:'),
            eq(r'I = k\,\Delta T^{0.44}\,A^{0.725}', 'Track current (IPC-2221)',
               '$A$ in square mils, 1 mil = 0.0254 mm; $k = 0.048$ on outer layers and 0.024 on inner layers; '
               '$\\Delta T$ in °C'),
            fig(widths(), 'Inner layers are surrounded by insulation and need wider tracks. The newer IPC-2152 '
                'charts also count the board thickness and nearby copper; either way, wider is safer.'),
            table(['Current', 'Outer, 10 °C', 'Outer, 20 °C', 'Inner, 10 °C'],
                  *[[f'{i:g} A', f'{track_width(i):.2f} mm', f'{track_width(i, 20):.2f} mm',
                     f'{track_width(i, 10, 0.024):.2f} mm'] for i in (0.25, 0.5, 1, 2, 3, 5)]),
            p(f'So 1 A needs about {one_amp:.2f} mm on an outer layer and 2 A about {two_amps:.2f} mm. Signal '
              'tracks carry microamps to milliamps: 0.15 to 0.25 mm is usual. Use wide tracks or filled areas '
              'of copper, pours, for power.'),
            eq(r'R = \frac{\rho\,L}{w\,t} = R_s\,\frac{L}{w} \qquad R_s = \frac{\rho}{t} \approx '
               r'0.5\,\mathrm{m\Omega}', 'Track resistance',
               'for 1 oz copper; $L/w$ counts the squares along the track'),
            p(f'A track 0.25 mm wide and 100 mm long is {squares:.0f} squares: '
              f'{squares * sheet * 1e3:.0f} mΩ, which drops {squares * sheet:.2f} V at 1 A. Copper\'s resistance '
              'also rises by 0.4% for each degree.'),
        ]),
        ('returns', 'Return currents and ground planes', [
            p('Every current returns to its source. On a board with a ground plane, the return current of each '
              'signal flows in the plane, and where it flows depends on frequency:'),
            fig(return_paths(), 'Solid dots: current along the track; rings: its return in the plane below. The '
                'high-frequency return flows directly beneath the track; it is drawn beside it here to be '
                'seen.'),
            p('The rules that follow: keep one unbroken ground plane under all signals, on a four-layer board '
              'the layer next to the signals. Do not split it into separate analog and digital grounds unless '
              'a datasheet insists. Where a signal changes layers, put a ground via beside its via so the '
              'return current can change layers too.'),
        ]),
        ('decoupling', 'Placing decoupling capacitors', [
            p('A decoupling capacitor supplies the sudden current a chip draws when its logic switches '
              f'({link("09-interfaces", "decoupling", "Microcontroller hardware")}). The current flows from '
              'the capacitor to the supply pin, through the chip, and back to the capacitor through the '
              'ground. Every millimetre of that path adds inductance, roughly 1 nH per millimetre of thin '
              'track, and inductance resists sudden changes of current:'),
            eq(r'\Delta V = L\,\frac{di}{dt}', 'Supply bounce',
               '50 nH of path and a 100 mA step in 10 ns: the supply at the pin dips by 0.5 V'),
            fig(placement(), 'Left: the current from the capacitor travels a long track to the chip, and its '
                'ground runs through two vias and the plane. Right: the capacitor sits across the pins, with '
                'its via beside its ground pad.'),
            p('Put the smallest capacitor nearest the pin, with short, wide tracks and the via right at the '
              'pad. Larger bulk capacitors can sit further away.'),
        ]),
        ('impedance', 'Controlled impedance', [
            p('A fast signal sees a track as a transmission line with a characteristic impedance $Z_0$, set by '
              'the track width, its height above the plane and the board material. If the impedance changes '
              'along the way, part of the signal reflects back, causing ringing. Radio needs 50 Ω tracks; USB '
              '90 Ω and Ethernet 100 Ω between the two tracks of a differential pair.'),
            fig(microstrip(), 'Left: a microstrip, a track on an outer layer over its plane. Right: its '
                'impedance on FR-4 for 1 oz copper; the dots are 50 Ω. A thin four-layer prepreg makes a 50 Ω '
                'track a sensible width; on a two-layer board it is about 3 mm wide.'),
            eq(r'Z_0 \approx \frac{87}{\sqrt{\varepsilon_r + 1.41}} \ln\frac{5.98\,h}{0.8\,w + t}',
               'Microstrip impedance', 'IPC-2141, for $0.1 < w/h < 2$; lengths in the same units'),
            eq(r'v = \frac{c}{\sqrt{\varepsilon_{eff}}} \qquad \varepsilon_{eff} \approx \frac{\varepsilon_r + 1}{2} '
               r'+ \frac{\varepsilon_r - 1}{2} \frac{1}{\sqrt{1 + 12\,h/w}}', 'Signal speed on a board',
               'part of the field is in air, so a microstrip is faster than an inner track'),
            p(f'For the 50 Ω track above, {w50:.2f} mm wide, a signal travels about {speed:.0f} mm per '
              f'nanosecond; on an inner layer, about {inner:.0f}. A common rule of thumb: treat a track as a '
              'transmission line, with matched impedance and termination, once its delay is more than about '
              'a sixth of the signal\'s rise time. Fabs publish the widths for their stack-ups; use their '
              f'numbers rather than the approximation, which gives {w50_thick:.1f} mm for a 1.6 mm board.'),
        ]),
        ('footprints', 'Parts and footprints', [
            p('A footprint is the set of copper pads a part is soldered to, with its outline. Through-hole '
              'parts have leads through plated holes; surface-mount parts sit on pads on one face. Imperial '
              'size codes name small parts by length and width in hundredths of an inch: an 0805 is '
              '0.08 × 0.05 inch, 2.0 × 1.25 mm.'),
            fig(footprints(), 'The square pad marks pin 1 of the DIP. The pads are typical; use the land '
                'pattern in each part\'s datasheet.'),
            table(['Package', 'Pin pitch', 'By hand'],
                  ['DIP, through-hole', '2.54 mm', 'easy; can go in a socket'],
                  ['SOIC, SOT-23', '1.27 mm, 0.95 mm', 'easy with a fine tip'],
                  ['0805 and 0603 passives', '–', 'easy with tweezers; 0603 needs care'],
                  ['0402 passives', '–', 'hard; for reflow'],
                  ['TSSOP, QFP', '0.65 mm, 0.5 mm', 'drag soldering with plenty of flux'],
                  ['QFN', '0.5 mm or less', 'pads underneath: hot air or reflow'],
                  ['BGA', 'balls under the part', 'reflow only, X-ray to inspect']),
        ]),
        ('fab', 'Design rules and the files a fab needs', [
            p('Before routing, enter the fab\'s limits in the design rules so the checker enforces them. These '
              'are safe starting values that low-cost fabs accept:'),
            table(['Rule', 'Safe value'],
                  ['track width and spacing', '0.15 mm, 6 mil'],
                  ['via', '0.3 mm drill, 0.6 mm pad'],
                  ['copper to board edge', '0.3 mm'],
                  ['silkscreen', 'lines 0.15 mm, text at least 1 mm high'],
                  ['board thickness', '1.6 mm; 1.0 mm or 0.8 mm for small badges and add-ons']),
            p('Then export the outputs. Gerber files describe each layer; an Excellon file lists the holes:'),
            table(['Layer', 'KiCad name', 'What it shows'],
                  ['copper', 'F.Cu, B.Cu, In1.Cu…', 'tracks, pads and planes'],
                  ['solder mask', 'F.Mask, B.Mask', 'the openings in the mask, not the mask itself'],
                  ['silkscreen', 'F.Silkscreen, B.Silkscreen', 'printed text and outlines'],
                  ['paste', 'F.Paste, B.Paste', 'stencil openings for solder paste; assembly only'],
                  ['outline', 'Edge.Cuts', 'the board shape and any cut-outs'],
                  ['drill', 'Excellon .drl', 'every hole, plated and unplated']),
            p('Check the Gerbers in a viewer before ordering: it shows what the fab will build. For assembly '
              'the fab also needs a bill of materials, BOM, and a placement file, CPL, with each part\'s '
              'position and rotation.'),
        ]),
        ('bringup', 'Bringing up a new board', [
            ol('Before soldering, look over the bare board and measure the resistance between each supply and '
               'ground: it must not be close to zero.',
               'After assembly, inspect fine-pitch pins for bridges under magnification, and measure each supply '
               'to ground again.',
               'Power it from a bench supply with the current limit set low, 50 to 100 mA. A short shows as the '
               'supply hitting its limit; switch off and find it.',
               'Measure every supply rail, then check the reset line, the clock and the programming connection.',
               'Load the smallest program that proves life: blink an LED, print over the UART.',
               'Bring up one part of the circuit at a time, and note what works. Watch for parts running hot.'),
            table(['Symptom', 'Common cause'],
                  ['a chip runs hot, the supply current is high', 'the part rotated or its footprint mirrored'],
                  ['a regulator gives the wrong voltage', 'a pinout mix-up: SOT-23 regulators vary'],
                  ['no serial output', 'TX and RX swapped, or the wrong baud rate'],
                  ['I2C devices do not answer', 'missing pull-ups, or the wrong address'],
                  ['USB is not detected', 'D+ and D− swapped, or the CC resistors missing on USB-C'],
                  ['the crystal does not start', 'wrong load capacitors, or long tracks to it']),
            note('Read more: the PCB Design Tutorial in DOCS → PCB AND BADGES covers layout in depth, and the '
                 'Tildagon, Communicator and Vectorscope documents there are complete boards to study. '
                 f'{link("11-badges", label="Badges and projects")} puts these steps to work.'),
        ]),
    ]
