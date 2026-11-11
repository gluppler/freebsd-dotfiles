from draw import Figure, arrow, dot, flow, ground, rail, terminal, text, two, wire
import page
from page import fig, link, mathify, p, table, ul

NAME = '00-contents'
TITLE = 'Electronics guide'
LEDE = ('Circuits, electronics, digital logic, control, robotics and board design, drawn: what each symbol '
        'means, what the laws say, and how current and signals move. Every figure is drawn in the page; '
        'moving dots show conventional current, faster where more current flows.')


def chapters():
    rows = []
    for chapter in page.BOOK[1:]:
        rows.append(f'<li><a href="{chapter.NAME}.html">{chapter.TITLE}</a><p>{mathify(chapter.LEDE)}</p></li>')
    return '<ul class="chapters">' + ''.join(rows) + '</ul>'


def legend():
    f = Figure(720, 250, 'How the figures are drawn')
    # Junctions and crossings.
    wire(f, (30, 60), (170, 60))
    wire(f, (100, 60), (100, 120))
    dot(f, 100, 60)
    text(f, 100, 140, 'dot: joined')
    wire(f, (30, 190), (170, 190))
    wire(f, (100, 160), (100, 225))
    text(f, 100, 244, 'no dot: not joined', 'middle', 't s')
    # Conventional current.
    two(f, 'B', (250, 60), (250, 140))
    wire(f, (250, 60), (250, 40), (420, 40), (420, 70))
    two(f, 'R', (420, 70), (420, 150), label='R', value='load', side=1)
    wire(f, (420, 150), (420, 180), (250, 180), (250, 140))
    flow(f, [(250, 60), (250, 40), (420, 40), (420, 70)], 1.1)
    flow(f, [(420, 150), (420, 180), (250, 180), (250, 140)], 1.1)
    text(f, 335, 222, 'current leaves + and returns to −')
    # Rails and ground.
    rail(f, 560, 70, '+3V3')
    wire(f, (560, 70), (560, 100))
    two(f, 'R', (560, 100), (560, 160), label='R1', side=1)
    ground(f, 560, 160)
    terminal(f, 660, 110)
    arrow(f, 660, 160, 660, 120)
    text(f, 660, 190, 'terminal', 'middle', 't s')
    text(f, 560, 214, 'named rail, ground', 'middle', 't s')
    return f


def sections():
    return [
        ('chapters', 'Chapters', [chapters()]),
        ('reading', 'Reading the figures', [
            fig(legend(), 'A dot joins crossing wires; without one they pass. Dots moving along a wire are '
                'conventional current, from the positive terminal through the circuit and back.'),
            p('Current is drawn as conventional current: positive charge leaving the + terminal of the source '
              'and returning to its − terminal. In metal wires the electrons actually drift the other way; '
              'every law here works the same either way as long as one direction is used throughout.'),
            p('A voltage is always between two points. A + and − beside a part mark the reference direction: '
              '$v$ is the potential at + minus the potential at −. With the current arrow entering the + '
              'terminal (the passive sign convention) the power $p = vi$ is the power the part absorbs; a '
              'negative result means the part delivers power, as a source does.'),
            p('Ground is the node every other voltage is measured from, 0 V by definition. A rail symbol such '
              'as +3V3 names a supply node; every symbol with that name is the same wire.'),
        ]),
        ('units', 'Units and prefixes', [
            table(['Quantity', 'Symbol', 'Unit', 'In base units'],
                  ['Charge', '$q$', 'coulomb, C', 'A·s'],
                  ['Current', '$i$, $I$', 'ampere, A', 'C/s'],
                  ['Voltage', '$v$, $V$', 'volt, V', 'J/C'],
                  ['Resistance', '$R$', 'ohm, Ω', 'V/A'],
                  ['Conductance', '$G$', 'siemens, S', 'A/V'],
                  ['Capacitance', '$C$', 'farad, F', 'C/V'],
                  ['Inductance', '$L$', 'henry, H', 'V·s/A'],
                  ['Power', '$P$', 'watt, W', 'J/s = V·A'],
                  ['Energy', '$W$, $E$', 'joule, J', 'W·s'],
                  ['Frequency', '$f$', 'hertz, Hz', '1/s'],
                  ['Angular frequency', '$\\omega = 2\\pi f$', 'rad/s', '1/s']),
            table(['Prefix', 'Factor', 'Example'],
                  ['p (pico)', '$10^{-12}$', '22 pF crystal load capacitor'],
                  ['n (nano)', '$10^{-9}$', '100 nF decoupling capacitor; 10 ns gate delay'],
                  ['µ (micro)', '$10^{-6}$', '10 µF bulk capacitor; 5 µA sleep current'],
                  ['m (milli)', '$10^{-3}$', '20 mA LED current; 1 ms debounce'],
                  ['k (kilo)', '$10^{3}$', '10 kΩ pull-up resistor'],
                  ['M (mega)', '$10^{6}$', '1 MΩ input resistance; 16 MHz clock'],
                  ['G (giga)', '$10^{9}$', '2.4 GHz radio']),
            p('Lower-case letters are values that change with time, $v(t)$ and $i(t)$; capitals are steady '
              '(DC) values or amplitudes.'),
        ]),
        ('keys', 'Reading with the keyboard', [
            ul('<kbd>j</kbd> and <kbd>k</kbd> scroll; <kbd>gg</kbd> and <kbd>G</kbd> go to the top and bottom.',
               '<kbd>f</kbd> labels every link and control; type a label to follow it. <kbd>H</kbd> and '
               '<kbd>L</kbd> go back and forward.',
               '<kbd>/</kbd> searches the page; <kbd>n</kbd> and <kbd>N</kbd> step through matches.',
               '<kbd>+</kbd>, <kbd>-</kbd> and <kbd>=</kbd> zoom in, out and back; the figures stay sharp.',
               '<em>Pause motion</em> at the top of every page freezes every figure where it is. With '
               'reduced motion preferred, the figures stay on their first frame.'),
            p('The DOCS menu reaches every chapter under ELECTRONICS GUIDE. For depth, the library entries '
              'CIRCUITS LIBRARY (MIT 6.002, Lessons in Electric Circuits, the Logisim manual), ROBOTICS '
              'LIBRARY and PCB AND BADGES open the books these chapters summarize. Start with ' +
              link('01-symbols', label='Schematic symbols') + ' or ' + link('02-dc', label='DC circuits') + '.'),
        ]),
    ]
