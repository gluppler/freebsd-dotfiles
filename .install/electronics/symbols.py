from draw import (Figure, _shape, begin, bjt, chassis, chip, common, dff, dot, end, flow, gate, ground, line,
                  mosfet, net, opamp, path, phases, pot, rail, rect, terminal, text, transformer, two, wire)
from page import card, cards, fig, p, table

NAME = '01-symbols'
TITLE = 'Schematic symbols'
LEDE = ('What each part looks like on a schematic, what it does, and the one equation that defines it. Both '
        'drawing styles are shown where they differ: the zigzag and curved-gate style (ANSI and IEEE) and the '
        'box style (IEC).')


def part(kind, title, label=None, value=None, **options):
    """A card figure with one two-terminal part drawn left to right."""
    half = _shape(kind)[2]
    lines = len([s for s in (label, value) if s])
    y = 10 + 14 * lines + half + (6 if lines else 0)
    f = Figure(200, y + max(half, 14) + 10, title)
    two(f, kind, (40, y), (160, y), label, value, **options)
    return f


def pair(first, second, title, labels=('', '')):
    """Two parts that are the same thing, stacked."""
    f = Figure(200, 108, title)
    two(f, first, (40, 34), (160, 34))
    two(f, second, (40, 82), (160, 82))
    text(f, 100, 14, labels[0], 'middle', 't s')
    text(f, 100, 64, labels[1], 'middle', 't s')
    return f


def first_circuit():
    f = Figure(560, 270, 'A switch, resistor and LED on a battery, shown open and closed')
    two(f, 'B2', (80, 92), (80, 172), 'BT1', '3 V', side=-1)
    wire(f, (80, 92), (80, 50), (200, 50))
    wire(f, (260, 50), (400, 50), (400, 80))
    two(f, 'R', (400, 80), (400, 140), 'R1', '330 Ω')
    wire(f, (400, 140), (400, 152))
    two(f, 'LED', (400, 152), (400, 204), 'D1', 'red LED')
    wire(f, (400, 204), (400, 230), (80, 230), (80, 172))
    opened, closed = phases(f, 2, 6, [0, 0.4, 1])
    begin(f, opened)
    two(f, 'SW', (200, 50), (260, 50), 'SW1', 'open', side=-1)
    text(f, 240, 140, 'no closed path:', 'middle', 't s')
    text(f, 240, 156, 'no current', 'middle', 't s')
    end(f)
    begin(f, closed)
    two(f, 'SWon', (200, 50), (260, 50), 'SW1', 'closed', side=-1)
    for points in ([(80, 92), (80, 50), (200, 50)], [(200, 50), (260, 50)], [(260, 50), (400, 50), (400, 80)],
                   [(400, 140), (400, 152)], [(400, 204), (400, 230), (80, 230), (80, 172)]):
        flow(f, points, 1.3)
    for x1, y1, x2, y2 in ((372, 166, 352, 158), (368, 178, 346, 178), (372, 190, 352, 198)):
        line(f, x1, y1, x2, y2, 'w thin')
    text(f, 240, 140, 'current ≈ 3.3 mA', 'middle', 't s')
    text(f, 240, 156, 'LED lit', 'middle', 't s')
    end(f)
    return f


def potentiometer():
    f = Figure(200, 96, 'Potentiometer')
    wiper = pot(f, (40, 36), (160, 36), side=-1)
    wire(f, wiper, (100, 76))
    text(f, 30, 40, '1', 'end', 't s')
    text(f, 170, 40, '3', 'start', 't s')
    text(f, 108, 80, '2 wiper', 'start', 't s')
    return f


def transformer_card():
    f = Figure(200, 96, 'Transformer')
    transformer(f, 100, 48)
    text(f, 66, 52, 'N_1', 'end', 't s')
    text(f, 134, 52, 'N_2', 'start', 't s')
    dot(f, 84, 21, 2.2)
    dot(f, 116, 21, 2.2)
    return f


def relay():
    f = Figure(200, 104, 'Relay')
    rect(f, 30, 38, 36, 26)
    path(f, 'M 34 62 L 62 40', 'w thin')
    wire(f, (48, 38), (48, 18))
    wire(f, (48, 64), (48, 88))
    path(f, 'M 66 51 H 118', 'w thin dash')
    two(f, 'SW', (110, 51), (170, 51))
    text(f, 48, 101, 'coil', 'middle', 't s')
    text(f, 140, 80, 'contact', 'middle', 't s')
    return f


def sources_cell():
    f = Figure(200, 112, 'Cell and battery')
    two(f, 'B', (40, 40), (160, 40))
    two(f, 'B2', (40, 94), (160, 94))
    text(f, 100, 12, 'one cell', 'middle', 't s')
    text(f, 100, 66, 'battery of cells', 'middle', 't s')
    return f


def meters():
    f = Figure(200, 100, 'Voltmeter and ammeter')
    two(f, 'Vm', (40, 34), (160, 34))
    two(f, 'Am', (40, 82), (160, 82))
    text(f, 100, 13, 'across a part', 'middle', 't s')
    text(f, 100, 61, 'in the current path', 'middle', 't s')
    return f


def transistor(kind):
    titles = {'npn': 'NPN transistor', 'pnp': 'PNP transistor', 'nmos': 'N-channel MOSFET',
              'pmos': 'P-channel MOSFET'}
    f = Figure(200, 92, titles[kind])
    if kind in ('npn', 'pnp'):
        pins = bjt(f, 100, 46, pnp=kind == 'pnp')
        names = {'B': 'base', 'C': 'collector', 'E': 'emitter'}
    else:
        pins = mosfet(f, 100, 46, p=kind == 'pmos')
        names = {'G': 'gate', 'D': 'drain', 'S': 'source'}
    for pin, name in names.items():
        x, y = pins[pin]
        if pin in 'BG':
            text(f, x - 6, y + 4, name, 'end', 't s')
        else:
            text(f, x + 8, y + (6 if y > 46 else 4), name, 'start', 't s')
    return f


def opamp_card():
    f = Figure(200, 92, 'Operational amplifier')
    pins = opamp(f, 96, 46, supplies=True)
    text(f, pins['-'][0] - 5, pins['-'][1] + 4, 'v_−', 'end', 't s')
    text(f, pins['+'][0] - 5, pins['+'][1] + 4, 'v_+', 'end', 't s')
    text(f, pins['out'][0] + 5, pins['out'][1] + 4, 'v_out', 'start', 't s')
    text(f, 104, 14, 'V+', 'start', 't s')
    text(f, 104, 86, 'V−', 'start', 't s')
    return f


def flipflop():
    f = Figure(200, 92, 'D flip-flop')
    pins = dff(f, 100, 48, label=None)
    text(f, pins['CLK'][0] - 5, pins['CLK'][1] + 4, 'clock', 'end', 't s')
    return f


def integrated():
    f = Figure(200, 112, 'Integrated circuit')
    chip(f, 56, 26, 88, 76, None, left=['VDD', 'GND', 'INT'], right=['SDA', 'SCL', 'ADDR'], pitch=22)
    text(f, 100, 18, 'U1')
    for i, number in enumerate(('1', '2', '3')):
        text(f, 40, 38 + 22 * i, number, 'end', 't s')
    for i, number in enumerate(('6', '5', '4')):
        text(f, 160, 38 + 22 * i, number, 'start', 't s')
    return f


def grounds():
    f = Figure(200, 84, 'Ground symbols')
    for x, draw, name in ((40, ground, 'ground'), (100, chassis, 'chassis'), (160, common, 'signal')):
        wire(f, (x, 14), (x, 30))
        draw(f, x, 30)
        text(f, x, 76, name, 'middle', 't s')
    return f


def rails():
    f = Figure(200, 92, 'Supply rail and net label')
    rail(f, 50, 40, '+3V3')
    two(f, 'R', (50, 40), (50, 84), side=-1)
    wire(f, (96, 62), (124, 62))
    net(f, 124, 62, 'SDA')
    return f


def connector():
    f = Figure(200, 108, 'Connector')
    chip(f, 100, 24, 30, 78, None, left=['1', '2', '3', '4'], pitch=18)
    text(f, 115, 16, 'J1')
    for i, name in enumerate(('VCC', 'GND', 'SDA', 'SCL')):
        text(f, 80, 40 + 18 * i, name, 'end', 't s')
    return f


def test_point():
    f = Figure(200, 70, 'Test point')
    wire(f, (40, 46), (100, 46), (100, 30))
    terminal(f, 100, 26, 4)
    text(f, 112, 30, 'TP1', 'start', 't s')
    return f


def junctions():
    f = Figure(200, 84, 'Joined and crossing wires')
    wire(f, (20, 40), (88, 40))
    wire(f, (54, 14), (54, 66))
    dot(f, 54, 40)
    wire(f, (112, 40), (180, 40))
    wire(f, (146, 14), (146, 66))
    text(f, 54, 80, 'joined', 'middle', 't s')
    text(f, 146, 80, 'not joined', 'middle', 't s')
    return f


def gate_table():
    rows = []
    for kind, expression, truth, meaning in (
            ('AND', r'$Y = A \cdot B$', '0 0 0 1', 'high only when every input is high'),
            ('OR', r'$Y = A + B$', '0 1 1 1', 'high when any input is high'),
            ('NOT', r'$Y = \overline{A}$', '1 0', 'the opposite of its input'),
            ('NAND', r'$Y = \overline{A \cdot B}$', '1 1 1 0', 'low only when every input is high'),
            ('NOR', r'$Y = \overline{A + B}$', '1 0 0 0', 'high only when every input is low'),
            ('XOR', r'$Y = A \oplus B$', '0 1 1 0', 'high when the inputs differ'),
            ('XNOR', r'$Y = \overline{A \oplus B}$', '1 0 0 1', 'high when the inputs match')):
        ansi = Figure(84, 44, f'{kind} gate, ANSI')
        gate(ansi, kind, 42, 22, inputs=1 if kind == 'NOT' else 2)
        iec = Figure(84, 44, f'{kind} gate, IEC')
        gate(iec, kind, 42, 22, iec=True, inputs=1 if kind == 'NOT' else 2)
        rows.append([kind, ansi.svg(), iec.svg(), expression, truth, meaning])
    return table(['Gate', 'ANSI', 'IEC', 'Output', 'Truth table', 'Meaning'], *rows, wide=True)


def sections():
    return [
        ('reading', 'Reading a schematic', [
            p('A schematic shows what connects to what, not where parts sit on the board. Each line is a '
              'conductor of no resistance; everything joined by lines is one <em>node</em> at one voltage. '
              'Parts carry a reference designator (R1, C3, U2) that matches the board and the parts list, '
              'and a value.'),
            fig(first_circuit(), 'The same circuit with the switch open, then closed. With no closed path there '
                'is no current anywhere. Closed, current leaves the battery at +, passes the resistor and the '
                r'LED, and returns: $I = (3\,\mathrm{V} - 1.9\,\mathrm{V})/330\,\Omega \approx 3.3\,\mathrm{mA}$.'),
            p('Signals usually flow left to right and higher voltages sit at the top, so supply rails run along '
              'the top and ground along the bottom.'),
        ]),
        ('passive', 'Resistors, capacitors and inductors', [cards(
            card(pair('R', 'Riec', 'Resistor in both styles', ('ANSI', 'IEC')), 'Resistor · R',
                 'Sets how much current a voltage drives and turns that energy into heat. The current is '
                 'proportional to the voltage across it.',
                 r'$v = iR \qquad p = i^2 R$'),
            card(potentiometer(), 'Potentiometer · RV',
                 'A resistor with a sliding contact, the wiper. Its voltage moves between the two ends as you '
                 'turn it: knobs, joysticks, servo position sensing.',
                 r'$V_2 = x\,V_{13}$ for travel $x$ from 0 to 1, unloaded'),
            card(part('Rvar', 'Variable resistor'), 'Trimmer or rheostat · RV',
                 'A resistance you adjust, usually once, to calibrate a circuit.'),
            card(part('NTC', 'Thermistor'), 'Thermistor · RT',
                 'Its resistance falls as it warms (NTC). The β model fits most parts, with $T$ in kelvin:',
                 r'$R = R_0\, e^{\beta (1/T - 1/T_0)}$'),
            card(part('LDR', 'Light-dependent resistor'), 'Photoresistor · R',
                 'Resistance falls with more light. Slow, tens of milliseconds, but simple light sensing.'),
            card(part('C', 'Capacitor'), 'Capacitor · C',
                 'Two plates and an insulator. It stores charge, passes changes in voltage and blocks a steady '
                 'DC voltage once charged.',
                 r'$q = Cv \qquad i = C\,\frac{dv}{dt}$'),
            card(part('Cpol', 'Polarized capacitor'), 'Electrolytic capacitor · C',
                 'A large value in a small part, but polarized: + must stay the more positive lead, or it '
                 'fails, sometimes violently.'),
            card(part('L', 'Inductor'), 'Inductor · L',
                 'A coil. It stores energy in its magnetic field and resists any change in its current.',
                 r'$v = L\,\frac{di}{dt}$'),
            card(part('Lcore', 'Inductor with a core'), 'Cored inductor · L',
                 'The lines mark an iron or ferrite core: more inductance in less space, until the core '
                 'saturates and the inductance collapses.'),
            card(transformer_card(), 'Transformer · T',
                 'Two coils on one core. AC in one induces AC in the other; dots mark the ends that rise '
                 'together. Ideal:',
                 r'$\frac{v_2}{v_1} = \frac{N_2}{N_1} = \frac{i_1}{i_2}$'),
            card(part('X', 'Crystal'), 'Crystal · Y',
                 'A quartz resonator. With an amplifier it oscillates at one precise frequency: 32.768 kHz for '
                 'clocks, 8 to 40 MHz for processors.'),
            card(part('F', 'Fuse'), 'Fuse · F',
                 'A conductor that melts and opens the circuit when the current stays above its rating.'),
            card(part('FB', 'Ferrite bead'), 'Ferrite bead · FB',
                 'A lossy inductor: it passes DC and turns high-frequency noise on a supply line into heat.'),
        )]),
        ('sources', 'Sources', [cards(
            card(part('V', 'Voltage source'), 'Voltage source · V',
                 'Holds its voltage $V_S$ whatever current flows; + marks the higher terminal.',
                 r'$v = V_S$'),
            card(sources_cell(), 'Cell and battery · BT',
                 'The long plate is +. An alkaline cell gives 1.5 V; a lithium-ion cell 3.6 to 3.7 V nominal, '
                 '4.2 V full.'),
            card(part('AC', 'AC voltage source'), 'AC source · V',
                 r'A sinusoid of peak $V_p$ and frequency $f$, with $\omega = 2\pi f$:',
                 r'$v(t) = V_p \sin(\omega t)$'),
            card(part('I', 'Current source'), 'Current source · I',
                 'Drives current $I_S$ in the arrow\'s direction whatever the voltage across it.',
                 r'$i = I_S$'),
            card(part('Vdep', 'Dependent voltage source'), 'Controlled voltage source',
                 'The diamond means its value follows another voltage or current in the circuit. These model '
                 'amplifiers:',
                 r'$v = A\,v_x$ or $v = r\,i_x$'),
            card(part('Idep', 'Dependent current source'), 'Controlled current source',
                 'A current set by another quantity; the model of a transistor:',
                 r'$i = g_m v_x$ or $i = \beta\, i_x$'),
        )]),
        ('switches', 'Switches, relays and loads', [cards(
            card(part('SW', 'Switch'), 'Switch · SW',
                 'Open: no current. Closed: a connection of almost no resistance.'),
            card(part('PB', 'Push button'), 'Push button · SW',
                 'Momentary and normally open: it connects only while pressed. Contacts bounce for a few '
                 'milliseconds, which logic must ignore.'),
            card(relay(), 'Relay · K',
                 'Current in the coil pulls the contact over. A small signal switches a separate, larger '
                 'circuit; the coil needs a diode across it when switched off.'),
            card(part('M', 'Motor'), 'Motor · M',
                 'A DC motor\'s speed rises with voltage and its torque with current.',
                 r'$\tau = k_t\, i \qquad e = k_e\, \omega$'),
            card(part('lamp', 'Lamp'), 'Lamp · DS',
                 'An incandescent indicator or bulb; its cold resistance is several times lower than hot.'),
            card(meters(), 'Meters',
                 'A voltmeter goes across a part and draws almost no current; an ammeter goes in series, in the '
                 'current path, and drops almost no voltage.'),
        )]),
        ('semiconductors', 'Diodes and transistors', [cards(
            card(part('D', 'Diode'), 'Diode · D',
                 'Conducts from anode to cathode, the way the arrow points, once the anode is about 0.6 to 0.7 V '
                 'higher (silicon); blocks the other way. The bar is the cathode, banded on the part.'),
            card(part('Z', 'Zener diode'), 'Zener diode · D',
                 'Conducts backwards at its Zener voltage $V_Z$ and holds it there: a simple reference.'),
            card(part('Sch', 'Schottky diode'), 'Schottky diode · D',
                 'Lower forward drop, 0.15 to 0.45 V, and fast: power paths and protection.'),
            card(part('LED', 'Light-emitting diode'), 'LED · D',
                 'A diode that emits light, dropping 1.8 V (red) to 3 V (blue, white). Its current must be '
                 'limited, usually with a resistor:',
                 r'$R = \frac{V_S - V_F}{I_F}$'),
            card(part('PD', 'Photodiode'), 'Photodiode · D',
                 'Light makes a reverse current proportional to its brightness: fast light sensing.'),
            card(transistor('npn'), 'NPN transistor · Q',
                 'A small base current lets a current $\\beta$ times larger flow from collector to emitter. The '
                 'arrow on the emitter points out.',
                 r'$i_C = \beta\, i_B \qquad v_{BE} \approx 0.7\,\mathrm{V}$'),
            card(transistor('pnp'), 'PNP transistor · Q',
                 'The mirror image: pulling the base below the emitter turns it on, and current flows from '
                 'emitter to collector. The arrow points in.'),
            card(transistor('nmos'), 'N-channel MOSFET · Q',
                 'The gate is insulated. A gate-to-source voltage above the threshold $V_{th}$ opens a channel '
                 'from drain to source; the gate draws no steady current. Switches loads to ground.'),
            card(transistor('pmos'), 'P-channel MOSFET · Q',
                 'On when the gate is pulled below the source by more than $|V_{th}|$. Switches loads from '
                 'the supply.'),
        )]),
        ('ics', 'Amplifiers, logic and chips', [
            cards(
                card(opamp_card(), 'Op-amp · U',
                     'A differential amplifier of enormous gain $A$, around $10^5$ or more. Feedback from the '
                     'output to the − input sets the useful gain.',
                     r'$v_{out} = A\,(v_+ - v_-)$'),
                card(flipflop(), 'D flip-flop · U',
                     'Copies D to Q at each rising clock edge and holds it in between: one bit of memory. '
                     'The wedge marks the clock input.'),
                card(integrated(), 'Integrated circuit · U',
                     'A box with named, numbered pins grouped by function rather than by package position. '
                     'Pin 1 is marked on the package by a dot or notch.'),
            ),
            p('Logic gates have two drawing styles. The ANSI shapes are the common ones; IEC boxes carry a '
              'symbol for the function. A small circle on an output, or input, means inversion. The truth '
              'table lists the output for inputs AB = 00, 01, 10, 11 (NOT: A = 0, 1).'),
            gate_table(),
        ]),
        ('connections', 'Grounds, rails and connectors', [cards(
            card(grounds(), 'Ground · GND',
                 'The 0 V reference every voltage is measured from. Chassis is the metal case; the triangle '
                 'often marks a separate signal or analog ground.'),
            card(rails(), 'Rails and net labels',
                 'Every rail symbol or net label with the same name is the same wire, so a schematic need not '
                 'draw every connection.'),
            card(junctions(), 'Junctions',
                 'A dot joins wires; crossing lines without one do not connect. Avoid four-way junctions, '
                 'where a missing dot is easy to miss.'),
            card(connector(), 'Connector · J',
                 'Pins that leave the board: headers, USB, battery and sensor leads. Pin 1 is marked on the '
                 'footprint.'),
            card(test_point(), 'Test point · TP',
                 'A pad or loop for a probe or a test fixture.'),
        )]),
        ('designators', 'Reference designators', [
            table(['Prefix', 'Part'],
                  ['R, RV, RN, RT', 'resistor; variable resistor or potentiometer; resistor network; thermistor'],
                  ['C', 'capacitor'],
                  ['L, FB', 'inductor; ferrite bead'],
                  ['D', 'diode, including LEDs (some boards use LED)'],
                  ['Q', 'transistor'],
                  ['U, IC', 'integrated circuit'],
                  ['J, P', 'connector: jack (the fixed side), plug'],
                  ['SW, S', 'switch or button'],
                  ['K', 'relay'],
                  ['F', 'fuse'],
                  ['Y, X', 'crystal or resonator'],
                  ['T', 'transformer'],
                  ['BT', 'battery'],
                  ['M', 'motor'],
                  ['LS, BZ', 'loudspeaker; buzzer'],
                  ['TP', 'test point'],
                  ['JP', 'jumper or solder jumper'],
                  ['H, MH', 'mounting hole']),
        ]),
        ('values', 'Reading part values', [
            p('Through-hole resistors carry colour bands: two or three digits, a multiplier, and a tolerance '
              'band set a little apart.'),
            table(['Colour', 'Digit', 'Multiplier', 'Tolerance'],
                  ['black', '0', '$\\times 1$', ''],
                  ['brown', '1', '$\\times 10$', '±1%'],
                  ['red', '2', '$\\times 10^2$', '±2%'],
                  ['orange', '3', '$\\times 10^3$', ''],
                  ['yellow', '4', '$\\times 10^4$', ''],
                  ['green', '5', '$\\times 10^5$', '±0.5%'],
                  ['blue', '6', '$\\times 10^6$', '±0.25%'],
                  ['violet', '7', '$\\times 10^7$', '±0.1%'],
                  ['grey', '8', '$\\times 10^8$', '±0.05%'],
                  ['white', '9', '$\\times 10^9$', ''],
                  ['gold', '', '$\\times 0.1$', '±5%'],
                  ['silver', '', '$\\times 0.01$', '±10%']),
            p('Brown, black, orange, gold reads 1, 0, ×1000: 10 kΩ ±5%. Five bands give three digits: '
              'brown, black, black, red, brown is 100 × 100 = 10 kΩ ±1%.'),
            p('Surface-mount parts print digits instead. Three digits are two figures and a power of ten, so a '
              'resistor marked 103 is 10 × 10³ = 10 kΩ; four digits are three figures and a power, so 1002 is '
              'also 10 kΩ. R marks the decimal point: 4R7 is 4.7 Ω. A 0 or 000 resistor is a jumper. '
              'Capacitor codes count picofarads: 104 is 10 × 10⁴ pF = 100 nF; 225 is 2.2 µF.'),
            p('Values come from the E series, spaced evenly on a logarithmic scale so that each step is about '
              'one tolerance apart. Every decade repeats them: 4.7 Ω, 47 Ω, 470 Ω, 4.7 kΩ.'),
            table(['Series', 'Tolerance', 'Values in each decade'],
                  ['E6', '±20%', '1.0 1.5 2.2 3.3 4.7 6.8'],
                  ['E12', '±10%', '1.0 1.2 1.5 1.8 2.2 2.7 3.3 3.9 4.7 5.6 6.8 8.2'],
                  ['E24', '±5%', '1.0 1.1 1.2 1.3 1.5 1.6 1.8 2.0 2.2 2.4 2.7 3.0 3.3 3.6 3.9 4.3 4.7 5.1 '
                   '5.6 6.2 6.8 7.5 8.2 9.1'], wide=True),
        ]),
    ]
