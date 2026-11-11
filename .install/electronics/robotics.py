import heapq
import inspect
import math
import random

from draw import (Figure, Plot, arrow, begin, circle, dot, end, head, keyframes, line, num, path, phases, poly,
                  rect, sampled, steps, sweep, text, trace, wire)
from page import code, eq, fig, link, note, p, table

NAME = '08-robotics'
TITLE = 'Robotics mathematics'
LEDE = ('Frames, rotations and transforms; arm kinematics forwards and backwards; wheeled robots and odometry; '
        'motors, encoders, servos and steppers; fusing sensors and the Kalman filter; and planning a path with A*.')


def moving(f, name, place, period, samples=60):
    """A class that moves an element drawn at the origin to place(t) = (x, y)."""
    def move(t):
        x, y = place(t)
        return f'transform:translate({num(x)}px,{num(y)}px)'
    return sampled(f, name, move, period, samples, base=move(0))


def arc(f, cx, cy, r, a0, a1, cls='w thin'):
    """An arc counterclockwise from angle a0 to a1, in degrees, y up."""
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy - r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy - r * math.sin(math.radians(a1))
    large = 1 if a1 - a0 > 180 else 0
    path(f, f'M {num(x0)} {num(y0)} A {r} {r} 0 {large} 0 {num(x1)} {num(y1)}', cls)
    return x1, y1


def frames():
    f = Figure(900, 280, 'A point carried by a body frame as the frame turns, in body and world coordinates')
    ox, oy, scale = 90, 250, 36

    def screen(x, y):
        return ox + scale * x, oy - scale * y
    t, body = (6, 2), (3, 1)
    arrow(f, ox, oy, ox + 170, oy, 'w', 8)
    arrow(f, ox, oy, ox, oy - 170, 'w', 8)
    text(f, ox + 180, oy + 4, 'x_0', 'start')
    text(f, ox, oy - 180, 'y_0')
    tx, ty = screen(*t)
    arrow(f, ox, oy, tx - 4, ty + 2, 'w thin dash', 7)
    text(f, (ox + tx) / 2 - 6, (oy + ty) / 2 - 6, 't', 'end', 't b')
    for cls, degrees in zip(phases(f, 4, 12), (0, 30, 60, 90)):
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        rx, ry = c * body[0] - s * body[1], s * body[0] + c * body[1]
        px, py = screen(rx + t[0], ry + t[1])
        begin(f, cls)
        line(f, px, py, px, oy, 'w thin faint')
        line(f, px, py, ox, py, 'w thin faint')
        for ux, uy, name in ((c, s, 'x_1'), (-s, c, 'y_1')):
            arrow(f, tx, ty, *screen(t[0] + 3.4 * ux, t[1] + 3.4 * uy), 'w', 8)
            lx, ly = screen(t[0] + 3.9 * ux, t[1] + 3.9 * uy)
            text(f, lx, ly + 4, name)
        wire(f, (tx, ty), screen(t[0] + body[0] * c, t[1] + body[0] * s), (px, py), cls='w thin dash')
        dot(f, px, py, 5)
        text(f, px + 9, py - 7, 'p', 'start', 't b')
        rows = (f'θ = {degrees}°', 'p_1 = (3, 1) in the body frame', 'p_0 = R(θ) p_1 + t',
                f'= ({rx:.2f}, {ry:.2f}) + (6, 2)', f'= ({rx + t[0]:.2f}, {ry + t[1]:.2f}) in the world frame')
        for k, words in enumerate(rows):
            text(f, 560, 80 + 26 * k, words, 'start', 't b' if k == 0 else 't s')
        end(f)
    dot(f, tx, ty, 3)
    return f


def solve(x, y, l1, l2, elbow=1):
    """Joint angles, in radians, that put the tip of a two-link arm at (x, y)."""
    c = (x * x + y * y - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    if abs(c) > 1:
        raise ValueError('out of reach')
    t2 = math.atan2(elbow * math.sqrt(1 - c * c), c)
    t1 = math.atan2(y, x) - math.atan2(l2 * math.sin(t2), l1 + l2 * math.cos(t2))
    return t1, t2


def arm():
    f = Figure(900, 300, 'A two-link arm: its angles and lengths, and the arm following a circle by inverse kinematics')
    bx, by, l1, l2 = 100, 250, 130, 100
    t1, t2 = 35, 70
    jx, jy = bx + l1 * math.cos(math.radians(t1)), by - l1 * math.sin(math.radians(t1))
    ex, ey = jx + l2 * math.cos(math.radians(t1 + t2)), jy - l2 * math.sin(math.radians(t1 + t2))
    rect(f, bx - 18, by, 36, 10, 'shade')
    line(f, bx - 24, by, bx + 160, by, 'w thin faint')
    line(f, jx, jy, jx + 60 * math.cos(math.radians(t1)), jy - 60 * math.sin(math.radians(t1)), 'w thin dash')
    arc(f, bx, by, 44, 0, t1)
    arc(f, jx, jy, 32, t1, t1 + t2)
    wire(f, (bx, by), (jx, jy), (ex, ey), cls='w bold')
    circle(f, bx, by, 6, 'walker')
    circle(f, jx, jy, 5, 'walker')
    dot(f, ex, ey, 5)
    text(f, bx + 56, by - 10, 'θ_1', 'start')
    text(f, jx + 22, jy - 40, 'θ_2', 'start')
    text(f, (bx + jx) / 2 - 10, (by + jy) / 2 - 8, 'l_1', 'end')
    text(f, (jx + ex) / 2 - 12, (jy + ey) / 2 + 4, 'l_2', 'end')
    text(f, ex + 10, ey - 6, '(x, y)', 'start')
    bx, by, period = 640, 262, 10
    cx, cy, r = 120, 110, 50

    def target(t):
        a = 2 * math.pi * t / period
        return cx + r * math.cos(a), cy + r * math.sin(a)
    edge = math.degrees(math.asin((f.height - by) / (l1 + l2)))
    arc(f, bx, by, l1 + l2, -edge, 180 + edge, 'w thin faint')
    circle(f, bx + cx, by - cy, r, 'w thin dash')
    text(f, bx + 92, 36, 'edge of reach', 'start', 't s')
    text(f, bx + cx + r + 10, by - cy + 4, 'path', 'start', 't s')
    rect(f, bx - 18, by, 36, 10, 'shade')
    line(f, bx - 120, by, bx + 240, by, 'w thin faint')
    goal = moving(f, 'target', lambda t: (bx + target(t)[0], by - target(t)[1]), period, 72)
    f.add(f'<g class="{goal}"><circle class="walker" r="10"/></g>')

    def joint(k):
        def turn(t):
            return f'transform:rotate({num(-math.degrees(solve(*target(t), l1, l2, -1)[k]))}deg)'
        return turn
    shoulder = sampled(f, 'shoulder', joint(0), period, 72, base=joint(0)(0))
    elbow = sampled(f, 'elbow', joint(1), period, 72, base=joint(1)(0))
    f.add(f'<g transform="translate({bx} {by})"><g class="{shoulder}"><path class="w bold" d="M 0 0 H {l1}"/>'
          f'<g transform="translate({l1} 0)"><g class="{elbow}"><path class="w bold" d="M 0 0 H {l2}"/>'
          f'<circle class="fill" cx="{l2}" cy="0" r="5"/></g><circle class="walker" r="5"/></g></g>'
          f'<circle class="walker" r="6"/></g>')
    return f


def drive():
    f = Figure(900, 300, 'The geometry of a differential-drive robot turning, and a robot driving a loop by odometry')
    x, y, half, radius, k = 300, 190, 40, 120, 0.75
    icc = x - radius
    line(f, icc, y, x + half, y, 'w thin dash')
    rect(f, x - half + 4, y - 25, 2 * half - 8, 50)
    path(f, f'M {x - 8} {y - 14} L {x} {y - 22} L {x + 8} {y - 14}', 'w thin')
    for wx in (x - half, x + half):
        rect(f, wx - 4, y - 13, 8, 26, 'fill')
    for wx, name in ((x - half, 'v_l'), (x, 'v'), (x + half, 'v_r')):
        length = k * (wx - icc)
        arrow(f, wx, y, wx, y - length, 'w', 8)
        text(f, wx - 6, y - length - 2, name, 'end')
    line(f, icc, y, x + half + 16, y - k * (radius + half + 16), 'w thin faint')
    dot(f, icc, y, 4)
    text(f, icc, y + 22, 'ICC')
    hx, hy = arc(f, icc, y, 24, -60, 60)
    f.add(head(hx, hy, math.atan2(-math.cos(math.radians(60)), -math.sin(math.radians(60))), 7))
    text(f, icc + 20, y - 26, 'ω', 'start')
    for x1, x2, yy, name in ((icc, x, y + 44, 'R'), (x - half, x + half, y + 70, 'L')):
        arrow(f, (x1 + x2) / 2, yy, x1, yy, 'w thin', 6)
        arrow(f, (x1 + x2) / 2, yy, x2, yy, 'w thin', 6)
        text(f, (x1 + x2) / 2, yy - 6, name, 'middle', 't s')
    v, track, bend, side = 80, 24, 40, 160
    plan = [(side / v, v, v), (math.pi / 2 * bend / v, v * (1 - track / 2 / bend), v * (1 + track / 2 / bend))] * 4
    poses, dt, px, py, heading = [], 0.001, 600.0, 272.0, 0.0
    for seconds, left, right in plan:
        for _ in range(round(seconds / dt)):
            poses.append((px, py, heading))
            ds, turn = (left + right) / 2 * dt, (right - left) / track * dt
            px += ds * math.cos(heading + turn / 2)
            py -= ds * math.sin(heading + turn / 2)
            heading += turn
    assert math.dist((px, py), poses[0][:2]) < 0.5 and abs(heading - 2 * math.pi) < 0.01
    period = len(poses) * dt
    f.add(f'<path class="w thin dash" d="{poly([q[:2] for q in poses[::40]] + [poses[0][:2]])}"/>')

    def pose(t):
        px, py, heading = poses[min(round(t / dt), len(poses) - 1)] if t < period else (*poses[0][:2], 2 * math.pi)
        return f'transform:translate({num(px)}px,{num(py)}px) rotate({num(-math.degrees(heading))}deg)'
    robot = sampled(f, 'drive', pose, period, 160, base=pose(0))
    bounds, run = [0], 0
    for seconds, _, _ in plan:
        run += seconds
        bounds.append(run / period)
    bounds[-1] = 1
    stages = phases(f, len(plan), period, bounds)
    f.add(f'<g class="{robot}">')
    rect(f, -11, -9, 22, 18)
    path(f, 'M 2 -5 L 8 0 L 2 5', 'w thin')
    rect(f, -7, -15, 14, 4, 'fill')
    rect(f, -7, 11, 14, 4, 'fill')
    for cls, (_, left, right) in zip(stages, plan):
        begin(f, cls)
        arrow(f, 9, -13, 9 + 0.3 * left, -13, 'w thin', 5)
        arrow(f, 9, 13, 9 + 0.3 * right, 13, 'w thin', 5)
        end(f)
    f.add('</g>')
    for cls, (_, left, right) in zip(stages, plan):
        begin(f, cls)
        text(f, 680, 148, 'straight' if left == right else 'turning left', 'middle', 't s')
        text(f, 680, 166, 'v_l = v_r' if left == right else 'v_r > v_l', 'middle', 't s')
        end(f)
    return f


ODOMETRY = '''
/* Called every control period with the encoder counts since the last call. */
void odometry(int32_t left, int32_t right)
{
    float dl = left * METRES_PER_COUNT, dr = right * METRES_PER_COUNT;
    float ds = (dr + dl) / 2, dtheta = (dr - dl) / TRACK;

    x += ds * cosf(theta + dtheta / 2);    /* along the average heading */
    y += ds * sinf(theta + dtheta / 2);
    theta += dtheta;
}
'''


def motor():
    f = Figure(900, 280, 'Speed, current, output power and efficiency of a DC motor against its load torque')
    i0 = 0.05
    plot = Plot(f, 80, 40, 480, 190, (0, 1), (0, 1.08))
    plot.axes('torque', None, [(0, '0'), (0.5, '½ τ_stall'), (1, 'τ_stall')], [(1, 'max')], grid=True)

    def speed(x):
        return 1 - x

    def power(x):
        return 4 * x * (1 - x)
    plot.curve(speed)
    plot.curve(lambda x: i0 + (1 - i0) * x, 'w curve dash')
    plot.curve(power, 'w curve dots')
    plot.curve(lambda x: x * (1 - x) * (1 - i0) ** 2 / (i0 + (1 - i0) * x), 'w thin')
    rows = ('solid: speed, ω_0 with no load', 'dashed: current, I_0 with no load', 'dotted: output power',
            'thin: efficiency, best at light load')
    for k, words in enumerate(rows):
        text(f, 610, 90 + 20 * k, words, 'start', 't s')
    period = 8

    def load(t):
        return 0.5 - 0.42 * math.cos(2 * math.pi * t / period)
    cursor = moving(f, 'load', lambda t: (plot.X(load(t)), 0), period)
    f.add(f'<g class="{cursor}"><path class="w thin dash" d="M 0 {plot.y} V {plot.y + plot.h}"/></g>')
    for name, curve in (('speed', speed), ('power', power)):
        cls = moving(f, name, lambda t, curve=curve: (plot.X(load(t)), plot.Y(curve(load(t)))), period)
        f.add(f'<g class="{cls}"><circle class="walker" r="6"/></g>')
    return f


SEQUENCE = ((0, 0), (1, 0), (1, 1), (0, 1))


def quadrature_table():
    """The decoder table: previous AB state in bits 3 and 2, new state in bits 1 and 0."""
    out = [0] * 16
    for k, (a, b) in enumerate(SEQUENCE):
        na, nb = SEQUENCE[(k + 1) % 4]
        out[(a << 3 | b << 2) | (na << 1 | nb)] = 1
        out[(na << 3 | nb << 2) | (a << 1 | b)] = -1
    return out


def quadrature():
    f = Figure(900, 260, 'Quadrature encoder signals turning forwards then backwards, and the count they give')
    x0, scale = 120, 46
    events = [(0.25 + 0.5 * k, k + 1) for k in range(16)] + [(8.25 + 0.5 * k, 15 - k) for k in range(16)]
    for bit, y, name in ((0, 50, 'A'), (1, 104, 'B')):
        trace(f, x0, y, scale, [(0, 0)] + [(t, SEQUENCE[n % 4][bit]) for t, n in events], 16, name)
    base, step = 236, 4
    stairs = [(x0, base)] + [(x0 + t * scale, base - n * step) for t, n in events] + [(x0 + 16 * scale, base)]
    wire(f, *steps(stairs), cls='w thin')
    text(f, x0 - 14, base - 30, 'count', 'end', 't s')
    text(f, x0 + 8 * scale, base - 16 * step - 8, '16', 'middle', 't s')
    line(f, x0 + 8 * scale, 30, x0 + 8 * scale, base, 'w thin faint')
    text(f, x0 + 4 * scale, 30, 'forwards: A leads B, count rises', 'middle', 't s')
    text(f, x0 + 12 * scale, 30, 'backwards: B leads A, count falls', 'middle', 't s')
    sweep(f, 'cursor', x0, x0 + 16 * scale, 40, base, 16)
    return f


def servo():
    f = Figure(900, 220, 'A servo signal at three pulse widths and the horn angle each one sets')
    x0, scale, high = 80, 20, 70
    cx, cy = 760, 120
    rect(f, cx - 70, cy - 40, 140, 80)
    arc(f, cx, cy, 74, 45, 135, 'w thin faint')
    text(f, cx, cy + 66, 'servo', 'middle', 't s')
    for cls, (width, angle) in zip(phases(f, 3, 9), ((1.0, -45), (1.5, 0), (2.0, 45))):
        begin(f, cls)
        trace(f, x0, high, scale, [(0, 1), (width, 0), (20, 1), (20 + width, 0)], 25, 'signal', 50)
        text(f, x0 + width * scale + 6, high - 8, f'{width} ms', 'start', 't b')
        a = math.radians(angle)
        wire(f, (cx, cy), (cx + 62 * math.sin(a), cy - 62 * math.cos(a)), cls='w bold')
        text(f, cx + 90, cy - 30, f'{"+" if angle > 0 else ""}{angle}°'.replace('-', '−'), 'start', 't b')
        end(f)
    circle(f, cx, cy, 9, 'walker')
    arrow(f, x0 + 10 * scale, high + 82, x0, high + 82, 'w thin', 6)
    arrow(f, x0 + 10 * scale, high + 82, x0 + 20 * scale, high + 82, 'w thin', 6)
    text(f, x0 + 10 * scale, high + 76, '20 ms, 50 Hz', 'middle', 't s')
    return f


def stepper():
    f = Figure(900, 240, 'A stepper motor taking four full steps as its coils are switched in turn')
    cx, cy = 170, 120
    circle(f, cx, cy, 86)
    poles = {'A+': 0, 'B+': 90, 'A−': 180, 'B−': 270}

    def pole(angle, cls):
        a = math.radians(angle)
        ux, uy, vx, vy = math.cos(a), -math.sin(a), math.sin(a), math.cos(a)
        corners = [(cx + ux * r + vx * w, cy + uy * r + vy * w) for r, w in ((50, -13), (86, -13), (86, 13), (50, 13))]
        f.add(f'<path class="{cls}" d="{poly(corners)} Z"/>')
    for angle in poles.values():
        pole(angle, 'w')
    for name, angle in (('A', 0), ('B', 90), ('A', 180), ('B', 270)):
        a = math.radians(angle)
        text(f, cx + 102 * math.cos(a), cy - 102 * math.sin(a) + 5, name, 'middle', 't b')
    circle(f, cx, cy, 30)
    x0, scale = 470, 90
    rows = (('I_A', (1, 0, -1, 0), 70), ('I_B', (0, 1, 0, -1), 160))
    for name, levels, y in rows:
        line(f, x0, y, x0 + 4 * scale, y, 'w thin faint')
        text(f, x0 - 14, y + 4, name, 'end', 't s')
        points = [(x0 + k * scale, y - 26 * v) for k, v in enumerate(levels)] + [(x0 + 4 * scale, y - 26 * levels[-1])]
        stepped = [points[0]]
        for px, py in points[1:]:
            stepped += [(px, stepped[-1][1]), (px, py)]
        wire(f, *stepped)
    for k, name in enumerate(poles):
        text(f, x0 + (k + 0.5) * scale, 214, name, 'middle', 't s')
    for cls, (name, angle) in zip(phases(f, 4, 8), poles.items()):
        begin(f, cls)
        pole(angle, 'fill')
        pole(angle + 180, 'fill')
        a = math.radians(angle)
        arrow(f, cx - 22 * math.cos(a), cy + 22 * math.sin(a), cx + 26 * math.cos(a), cy - 26 * math.sin(a), 'w bold', 9)
        text(f, 300, cy + 5, f'{name}: rotor at {angle}°', 'start', 't s')
        end(f)
    sweep(f, 'cursor', x0, x0 + 4 * scale, 30, 196, 8)
    return f


def tilt(t):
    """The true tilt in degrees: up to 30, over to −20 and back to level."""
    def ease(a, b):
        u = min(max((t - a) / (b - a), 0), 1)
        return u * u * (3 - 2 * u)
    return 30 * ease(1, 2.5) - 50 * ease(5, 6.5) + 20 * ease(8, 9.5)


def fusion_data(dt=0.01, seconds=10, alpha=0.98, bias=1.5):
    """Tilt from a gyro with bias and noise, a noisy accelerometer, and both fused."""
    rng = random.Random(11)
    gyro = fused = 0.0
    rows = []
    for n in range(round(seconds / dt) + 1):
        t = n * dt
        rate = (tilt(t + dt) - tilt(t)) / dt + bias + rng.gauss(0, 0.5)
        accel = tilt(t) + rng.gauss(0, 3)
        gyro += rate * dt
        fused = alpha * (fused + rate * dt) + (1 - alpha) * accel
        rows.append((t, tilt(t), accel, gyro, fused))
    return rows


def rms(errors):
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def fusion(rows):
    f = Figure(900, 280, 'Tilt from a gyro alone, an accelerometer alone, and the two fused')
    plot = Plot(f, 70, 40, 560, 200, (0, 10), (-35, 45))
    plot.axes('t (s)', 'tilt', [(k, str(k)) for k in range(0, 11, 2)], [(-20, '−20°'), (0, '0°'), (30, '30°')],
              grid=True)
    plot.curve([(t, a) for t, _, a, _, _ in rows[::2]], 'w thin dim')
    plot.curve([(t, g) for t, _, _, g, _ in rows], 'w curve dots')
    plot.curve([(t, v) for t, v, _, _, _ in rows], 'w thin dash')
    plot.curve([(t, x) for t, _, _, _, x in rows])
    legend = ('thin: accelerometer, noisy', 'dotted: gyro integrated, drifting', 'dashed: true tilt',
              'solid: complementary filter')
    for k, words in enumerate(legend):
        text(f, 660, 90 + 20 * k, words, 'start', 't s')
    sweep(f, 'cursor', plot.X(0), plot.X(10), plot.y, plot.y + plot.h, 10)
    return f


COMPLEMENTARY = '''
/* Tilt from a gyro and an accelerometer, run every dt seconds. Angles in radians. */
static float angle;

void update(float gyro_rate, float accel_y, float accel_z, float dt)
{
    float tilt = atan2f(accel_y, accel_z);    /* only right when not accelerating */
    angle = 0.98f * (angle + gyro_rate * dt) + 0.02f * tilt;
}
'''


def kalman(readings, q, r, x=0.0, p=1000.0):
    """A one-variable Kalman filter: the estimate and its variance after each reading."""
    out = []
    for z in readings:
        p += q                  # predict: the value may have drifted
        k = p / (p + r)         # gain: how far to trust the new reading
        x += k * (z - x)        # update: move towards it
        p *= 1 - k              # and become more certain
        out.append((x, p))
    return out


def kalman_figure():
    f = Figure(900, 270, 'A Kalman filter estimating a drifting value from noisy readings')
    rng = random.Random(5)
    truth = [20 + 0.02 * n for n in range(120)]
    readings = [v + rng.gauss(0, 1) for v in truth]
    estimates = kalman(readings, q=0.01, r=1.0)
    plot = Plot(f, 70, 40, 600, 190, (0, 120), (16.5, 25.5))
    plot.axes('n', None, [(k, str(k)) for k in range(0, 121, 20)], [(18, '18'), (20, '20'), (22, '22'), (24, '24')],
              grid=True)

    def clamp(v):
        return min(max(v, plot.yr[0]), plot.yr[1])
    upper = [(plot.X(n), plot.Y(clamp(x + 2 * math.sqrt(v)))) for n, (x, v) in enumerate(estimates)]
    lower = [(plot.X(n), plot.Y(clamp(x - 2 * math.sqrt(v)))) for n, (x, v) in enumerate(estimates)]
    f.add(f'<path class="fill" fill-opacity="0.22" d="{poly(upper + lower[::-1])} Z"/>')
    for n, z in enumerate(readings):
        if plot.yr[0] < z < plot.yr[1]:
            dot(f, plot.X(n), plot.Y(z), 2.2)
    plot.curve(list(enumerate(truth)), 'w thin dash')
    plot.curve([(n, x) for n, (x, _) in enumerate(estimates)])
    legend = ('dots: readings, σ = 1', 'dashed: true value', 'solid: estimate', 'band: estimate ± 2σ')
    for k, words in enumerate(legend):
        text(f, 700, 90 + 20 * k, words, 'start', 't s')
    return f, estimates[-1][1] / 1.0     # the gain settles at P / R


MAP = (
    '.....................',
    '.....................',
    '......#####..........',
    '..........#..........',
    '..........#....#.....',
    '..........#....#.....',
    'S.........#....#....G',
    '..........#....#.....',
    '..........#....#.....',
    '..........#..........',
    '......#####..........',
    '.....................',
    '.....................',
)


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(walls, size, start, goal, h):
    """The shortest 4-connected path across a grid, and the cells expanded, in order."""
    frontier = [(h(start, goal), h(start, goal), start)]
    came_from, cost, closed, order = {start: None}, {start: 0}, set(), []
    while frontier:
        _, _, cell = heapq.heappop(frontier)
        if cell in closed:
            continue            # already expanded by a cheaper route
        closed.add(cell)
        order.append(cell)
        if cell == goal:
            break
        x, y = cell
        for near in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            inside = 0 <= near[0] < size[0] and 0 <= near[1] < size[1]
            if inside and near not in walls and cost[cell] + 1 < cost.get(near, math.inf):
                cost[near], came_from[near] = cost[cell] + 1, cell
                heapq.heappush(frontier, (cost[near] + h(near, goal), h(near, goal), near))
    if goal not in came_from:
        return None, order
    route, cell = [], goal
    while cell is not None:
        route.append(cell)
        cell = came_from[cell]
    return route[::-1], order


def search(h):
    cells = {(x, y): c for y, row in enumerate(MAP) for x, c in enumerate(row)}
    walls = {cell for cell, c in cells.items() if c == '#'}
    start = next(cell for cell, c in cells.items() if c == 'S')
    goal = next(cell for cell, c in cells.items() if c == 'G')
    return walls, start, goal, astar(walls, (len(MAP[0]), len(MAP)), start, goal, h)


def planning():
    f = Figure(900, 300, "Dijkstra's algorithm and A* searching the same grid for the shortest path")
    size, period, buckets = 17, 12, 12
    results = []
    for gx, name, h in ((40, 'Dijkstra', lambda a, b: 0), (500, 'A*', manhattan)):
        walls, start, goal, (route, order) = search(h)
        results.append((name, len(order), len(route) - 1))
        x0, y0 = gx, 52
        text(f, x0, 36, f'{name}: {len(order)} cells expanded', 'start', 't b')
        for k in range(buckets):
            cls = keyframes(f, f'{name[0]}{k}', [(0, 'opacity:0'), (60 * (k + 1) / buckets, 'opacity:1'),
                                                  (100, 'opacity:1')], period, 'step-end', base='opacity:1')
            cells = order[len(order) * k // buckets:len(order) * (k + 1) // buckets]
            f.add(f'<g class="{cls}">' + ''.join(
                f'<rect class="fill" fill-opacity="0.24" x="{x0 + cx * size}" y="{y0 + cy * size}" '
                f'width="{size}" height="{size}"/>' for cx, cy in cells) + '</g>')
        for cx, cy in walls:
            rect(f, x0 + cx * size, y0 + cy * size, size, size, 'fill')
        for k in range(len(MAP[0]) + 1):
            line(f, x0 + k * size, y0, x0 + k * size, y0 + len(MAP) * size, 'grid')
        for k in range(len(MAP) + 1):
            line(f, x0, y0 + k * size, x0 + len(MAP[0]) * size, y0 + k * size, 'grid')
        shown = keyframes(f, f'{name[0]}path', [(0, 'opacity:0'), (60, 'opacity:1'), (100, 'opacity:1')], period,
                          'step-end', base='opacity:1')
        centre = [(x0 + (cx + 0.5) * size, y0 + (cy + 0.5) * size) for cx, cy in route]
        f.add(f'<path class="w bold {shown}" d="{poly(centre)}"/>')
        circle(f, *centre[0], 6, 'walker')
        dot(f, *centre[-1], 6)
    assert results[0][2] == results[1][2] and results[1][1] < results[0][1]
    return f, results


def sections():
    fused = fusion_data()
    gyro_error = abs(fused[-1][3] - fused[-1][1])
    accel_error = rms([a - v for _, v, a, _, _ in fused])
    fused_error = rms([x - v for _, v, _, _, x in fused])
    estimate_figure, gain = kalman_figure()
    plan_figure, results = planning()
    (_, dijkstra, length), (_, astar_count, _) = results
    return [
        ('frames', 'Frames and rotations', [
            p('A robot is a chain of coordinate frames: one fixed to the world, one to its body, one to each joint '
              'and sensor. Every measurement is made in some frame, and most robotics mathematics is moving '
              'points from one frame to another.'),
            p('Turning a frame by $\\theta$ turns every point in it. In two dimensions:'),
            eq(r'R(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix} '
               r'\qquad p_0 = R(\theta)\,p_1 + t', 'Rotation matrix',
               'a point $p_1$ in a frame turned by $\\theta$ and moved by $t$'),
            fig(frames(), 'The point keeps its body coordinates, (3, 1), as the body frame turns; its world '
                'coordinates come from rotating them and adding the frame\'s position.'),
            p('Rotation and translation fit into one matrix if each point gets a third coordinate, always 1. '
              'Then moving through several frames is a single product of matrices:'),
            eq(r'T = \begin{bmatrix} \cos\theta & -\sin\theta & t_x \\ \sin\theta & \cos\theta & t_y \\ 0 & 0 & 1 '
               r'\end{bmatrix} \qquad \begin{bmatrix} x_0 \\ y_0 \\ 1 \end{bmatrix} = T \begin{bmatrix} x_1 \\ '
               r'y_1 \\ 1 \end{bmatrix}', 'Homogeneous transform'),
            eq(r'{}^{0}T_{2} = {}^{0}T_{1}\;{}^{1}T_{2} \qquad R^{-1} = R^{T}', 'Chained transforms',
               'read right to left: frame 2 into frame 1, then frame 1 into frame 0'),
            p('A rotation matrix\'s inverse is its transpose, so undoing a rotation costs nothing. The order of '
              'transforms matters: turning then moving is not moving then turning.'),
        ]),
        ('three-d', 'Rotations in three dimensions', [
            p('In three dimensions there is one basic rotation about each axis. Aircraft and drones describe '
              'their attitude as roll $\\phi$ about the forward axis, pitch $\\theta$ about the sideways axis '
              'and yaw $\\psi$ about the vertical, applied in that order:'),
            eq(r'R_x(\phi) = \begin{bmatrix} 1 & 0 & 0 \\ 0 & \cos\phi & -\sin\phi \\ 0 & \sin\phi & \cos\phi '
               r'\end{bmatrix} \quad R_y(\theta) = \begin{bmatrix} \cos\theta & 0 & \sin\theta \\ 0 & 1 & 0 \\ '
               r'-\sin\theta & 0 & \cos\theta \end{bmatrix} \quad R_z(\psi) = \begin{bmatrix} \cos\psi & -\sin\psi '
               r'& 0 \\ \sin\psi & \cos\psi & 0 \\ 0 & 0 & 1 \end{bmatrix}', 'Rotations about the axes'),
            eq(r'R = R_z(\psi)\,R_y(\theta)\,R_x(\phi)', 'Roll, pitch and yaw'),
            p('Angles are easy to read but have a flaw: at a pitch of ±90° roll and yaw turn about the same axis, '
              'one degree of freedom is lost, and the angles jump. This is gimbal lock. Flight controllers and '
              'IMU libraries store attitude as a unit quaternion instead, four numbers that encode a rotation by '
              '$\\theta$ about a unit axis $\\hat{u}$:'),
            eq(r"q = \left( \cos\frac{\theta}{2},\ \hat{u}\sin\frac{\theta}{2} \right) \qquad v' = q\,v\,q^{*}",
               'Quaternion rotation', '$q^*$ is $q$ with its vector part negated'),
            eq(r'q_1 q_2 = \left( w_1 w_2 - \mathbf{v}_1 \cdot \mathbf{v}_2,\ w_1 \mathbf{v}_2 + w_2 \mathbf{v}_1 '
               r'+ \mathbf{v}_1 \times \mathbf{v}_2 \right)', 'Quaternion product',
               'writing $q = (w, \\mathbf{v})$'),
            p('Multiplying quaternions chains rotations, as with matrices. Rounding errors slowly stretch a '
              'quaternion, so divide it by its length now and then; and to blend smoothly between two '
              'orientations, interpolate along the sphere of unit quaternions, which is called slerp.'),
        ]),
        ('arms', 'Arm kinematics', [
            p('Forward kinematics gives the position of an arm\'s tip from its joint angles: follow the links '
              'from the base, adding each one turned by the sum of the angles before it.'),
            eq(r'x = l_1 \cos\theta_1 + l_2 \cos(\theta_1 + \theta_2) \qquad y = l_1 \sin\theta_1 + l_2 '
               r'\sin(\theta_1 + \theta_2)', 'Two-link forward kinematics'),
            p('Inverse kinematics runs the other way: which angles put the tip at $(x, y)$? For two links the law '
              'of cosines answers it. The sign chooses between the two solutions, elbow up and elbow down; past '
              '$l_1 + l_2$ there is none.'),
            eq(r'\cos\theta_2 = \frac{x^2 + y^2 - l_1^2 - l_2^2}{2 l_1 l_2}', 'Two-link inverse kinematics'),
            eq(r'\theta_2 = \operatorname{atan2}\left( \pm\sqrt{1 - \cos^2\theta_2},\ \cos\theta_2 \right) \qquad '
               r'\theta_1 = \operatorname{atan2}(y, x) - \operatorname{atan2}(l_2 \sin\theta_2,\ l_1 + l_2 '
               r'\cos\theta_2)'),
            fig(arm(), 'Left: the angles and lengths. Right: the arm following a circle; each frame of the motion '
                'is the code below solving for the two joint angles.'),
            code(inspect.getsource(solve)),
            p('Use atan2, not arctan: it takes $y$ and $x$ separately and returns the angle in the correct '
              'quadrant. Arms with more joints rarely have such a formula and are solved numerically, with the '
              'Jacobian below.'),
        ]),
        ('jacobian', 'Velocities, forces and singularities', [
            p('The Jacobian $J$ turns joint speeds into tip velocity. Its transpose turns a force at the tip into '
              'the torque each joint must supply.'),
            eq(r'\begin{bmatrix} \dot{x} \\ \dot{y} \end{bmatrix} = J \begin{bmatrix} \dot\theta_1 \\ '
               r'\dot\theta_2 \end{bmatrix} \qquad J = \begin{bmatrix} -l_1 s_1 - l_2 s_{12} & -l_2 s_{12} \\ '
               r'l_1 c_1 + l_2 c_{12} & l_2 c_{12} \end{bmatrix}', 'Jacobian',
               '$s_1 = \\sin\\theta_1$, $c_{12} = \\cos(\\theta_1 + \\theta_2)$'),
            eq(r'\tau = J^{T} F \qquad \det J = l_1 l_2 \sin\theta_2', 'Joint torques and singularity'),
            p('Where $\\det J = 0$, here with the arm straight or folded back, the arm is at a singularity: it '
              'cannot move its tip in some direction however fast the joints turn, and solving for joint speeds '
              'divides by zero. Plan paths that stay clear of them.'),
            p('Longer chains are described link by link with four Denavit–Hartenberg parameters each, which '
              'build each link\'s transform:'),
            table(['Parameter', 'Meaning'],
                  ['$\\theta_i$, theta', 'joint angle, about the previous $z$ axis'],
                  ['$d_i$', 'link offset, along the previous $z$ axis'],
                  ['$a_i$', 'link length, along the new $x$ axis'],
                  ['$\\alpha_i$, alpha', 'link twist, an angle about the new $x$ axis']),
            eq(r'A_i = \begin{bmatrix} \cos\theta_i & -\sin\theta_i\cos\alpha_i & \sin\theta_i\sin\alpha_i & '
               r'a_i\cos\theta_i \\ \sin\theta_i & \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & '
               r'a_i\sin\theta_i \\ 0 & \sin\alpha_i & \cos\alpha_i & d_i \\ 0 & 0 & 0 & 1 \end{bmatrix}',
               'Denavit–Hartenberg transform', 'the tip is $A_1 A_2 \\cdots A_n$ times the origin'),
        ]),
        ('wheels', 'Wheeled robots and odometry', [
            p('A differential-drive robot steers by running its two wheels at different speeds. It turns about '
              'a point on the line of its axle, the instantaneous centre of curvature:'),
            eq(r'v = \frac{v_r + v_l}{2} \qquad \omega = \frac{v_r - v_l}{L} \qquad R = \frac{L}{2}\,'
               r'\frac{v_r + v_l}{v_r - v_l}', 'Differential drive', '$L$ is the distance between the wheels'),
            fig(drive(), 'Left: each wheel moves at a speed proportional to its distance from the centre of the '
                'turn. Right: a robot driving straight, then turning left with its right wheel faster; its path '
                'is computed from the wheel speeds alone, by the odometry below.'),
            p('Odometry keeps track of where the robot is by adding up its wheel movements, read from encoders. '
              'Each control period:'),
            eq(r'\Delta s = \frac{d_r + d_l}{2} \quad \Delta\theta = \frac{d_r - d_l}{L} \quad x \leftarrow x + '
               r'\Delta s \cos\left( \theta + \frac{\Delta\theta}{2} \right) \quad y \leftarrow y + \Delta s '
               r'\sin\left( \theta + \frac{\Delta\theta}{2} \right)', 'Odometry'),
            code(ODOMETRY),
            p('Wheel slip, uneven floors and small errors in the wheel diameter or track width add up without '
              'limit, so odometry drifts. Robots correct it against something absolute: a compass, beacons, a '
              'map, or a camera.'),
        ]),
        ('motors', 'DC motors', [
            p('A brushed DC motor is a coil turning in a magnetic field. The torque is proportional to the current, '
              'and as it spins it generates a back-EMF proportional to its speed, which opposes the supply:'),
            eq(r'V = I R + k_e\,\omega \qquad \tau = k_t\,I', 'DC motor',
               'in SI units $k_e = k_t$, in V·s/rad and N·m/A'),
            eq(r'\omega = \frac{V}{k_e} - \frac{R}{k_e k_t}\,\tau \qquad \tau_{stall} = \frac{k_t V}{R} \qquad '
               r'P_{max} = \frac{\tau_{stall}\,\omega_0}{4}', 'Speed and torque'),
            fig(motor(), 'As the load torque rises the motor slows in a straight line and draws more current. '
                'Output power peaks at half the stall torque; efficiency peaks at a much lighter load.'),
            p('At stall the current is $V/R$, often ten times the running current: size the driver, fuse and '
              'battery for it. A gearbox trades speed for torque, minus some friction:'),
            eq(r'\tau_{out} = \eta\,N\,\tau_{in} \qquad \omega_{out} = \frac{\omega_{in}}{N}', 'Gearing',
               '$N$ is the gear ratio, $\\eta$ its efficiency'),
            p(f'Speed is set with PWM through an H-bridge ({link("04-semiconductors", "hbridge", "Diodes and transistors")}), '
              'and held under changing load with a PID loop on the encoder speed.'),
        ]),
        ('encoders', 'Encoders', [
            p('An incremental encoder gives two square waves, A and B, a quarter of a cycle apart. Which one '
              'leads gives the direction. Counting every edge of both gives four counts per cycle.'),
            fig(quadrature(), 'The same shaft turning forwards, then backwards. The order of the edges reverses, '
                'and the count follows.'),
            eq(r'\omega = \frac{2\pi\,\Delta n}{N\,\Delta t}', 'Encoder speed',
               '$\\Delta n$ counts in $\\Delta t$, $N$ counts per revolution'),
            p('A table indexed by the previous and new states decodes it, and ignores impossible jumps. '
              'This table is generated from the state sequence when this page is built:'),
            code('/* Index: previous AB in bits 3 and 2, new AB in bits 1 and 0. */\n'
                 'static const int8_t step[16] = { '
                 + ', '.join(str(v) for v in quadrature_table()) + ' };\n\n'
                 'static uint8_t last;\nstatic int32_t count;\n\n'
                 'void encoder_changed(void)    /* from a pin-change interrupt on A and B */\n{\n'
                 '    uint8_t now = read_a() << 1 | read_b();\n\n'
                 '    count += step[last << 2 | now];\n    last = now;\n}'),
            p('Many microcontrollers decode quadrature in a timer peripheral, which never misses an edge. At low '
              'speed, measure the time between edges instead of counting edges in a fixed time.'),
        ]),
        ('servos', 'Servos and steppers', [
            p('A hobby servo contains a motor, gears, a position sensor and a controller. It reads the width of '
              'a pulse repeated every 20 ms: 1.5 ms is the centre, and 1 ms and 2 ms the ends of the standard '
              'range, about 90° apart on many servos. Many accept 0.5 to 2.5 ms for nearly 180°; check the '
              'datasheet, and stay off the end stops.'),
            fig(servo(), 'The pulse width alone sets the angle; the 20 ms period need not be exact.'),
            p('A timer makes the pulses: with a 1 MHz count, a period of 20 000 and a compare value equal to the '
              'pulse width in microseconds.'),
            p('A stepper motor moves in fixed steps as its coils are switched in sequence, so it needs no sensor '
              'to know where it is, as long as it never misses a step. Real steppers have toothed rotors, giving '
              '200 steps a revolution, 1.8° each.'),
            fig(stepper(), 'Energising each coil pair in turn pulls the rotor round a step at a time. Energising '
                'both coils at once gives more torque; alternating one and two gives half steps.'),
            eq(r'\theta_{step} = \frac{360^\circ}{N} \qquad \text{rpm} = \frac{60\,f_{step}}{N\,m}',
               'Stepper speed', '$N$ steps per revolution, $m$ microsteps per step'),
            eq(r'I_A = I\cos\theta_e \qquad I_B = I\sin\theta_e', 'Microstepping',
               'currents for an electrical angle $\\theta_e$ between full steps'),
            p('Stepper drivers such as the A4988, DRV8825 and TMC2209 do this, regulating the coil current by '
              'chopping; they take one pulse per step on a STEP pin and a level on DIR. Ramp the step rate up '
              'and down, since a motor asked to start at full speed stalls and loses its position.'),
        ]),
        ('fusion', 'Fusing sensors', [
            p('An IMU combines an accelerometer and a gyroscope. The accelerometer measures gravity, so it gives '
              'tilt directly, but every vibration and acceleration disturbs it. The gyro measures rate of turn: '
              'integrated it is smooth, but any small bias grows into a drift.'),
            eq(r'\theta_{acc} = \operatorname{atan2}(a_y,\ a_z) \qquad \theta_{gyro} = \theta_0 + \int \omega\,dt',
               'Tilt from an IMU'),
            p('A complementary filter takes the short-term from the gyro and the long-term from the '
              'accelerometer:'),
            eq(r'\hat\theta_k = \alpha\left( \hat\theta_{k-1} + \omega_k\,\Delta t \right) + (1 - \alpha)\,'
               r'\theta_{acc,k} \qquad \tau = \frac{\alpha\,\Delta t}{1 - \alpha}', 'Complementary filter',
               'below the time constant $\\tau$ the accelerometer wins, above it the gyro'),
            fig(fusion(fused), f'Simulated at 100 Hz with $\\alpha = 0.98$, so $\\tau \\approx 0.5$ s. The '
                f'accelerometer alone is off by {accel_error:.1f}° RMS; the gyro alone has drifted '
                f'{gyro_error:.0f}° after ten seconds; fused, the error is {fused_error:.1f}° RMS.'),
            code(COMPLEMENTARY),
        ]),
        ('kalman', 'The Kalman filter', [
            p('A Kalman filter weighs a prediction against each new measurement by how uncertain each is, and '
              'tracks its own uncertainty as it goes. For a single value, with process noise $Q$ and measurement '
              'noise $R$:'),
            eq(r'P^{-} = P + Q \quad K = \frac{P^{-}}{P^{-} + R} \quad \hat{x} \leftarrow \hat{x} + K\,(z - '
               r'\hat{x}) \quad P = (1 - K)\,P^{-}', 'Kalman filter, one variable'),
            fig(estimate_figure, 'The estimate starts at the first reading, very unsure, and the band narrows as '
                f'readings arrive, until each new reading moves it about {gain * 100:.0f}% of the way. A larger '
                '$Q$ follows changes faster but smooths less.'),
            code(inspect.getsource(kalman)),
            p('With several variables, such as position and velocity, the same steps use matrices: $F$ predicts '
              'the next state from the last, $B$ adds the effect of the control input $u$, and $H$ gives what '
              'the sensors would read in a state. A subscript $k|k-1$ marks a prediction for step $k$ made at '
              'step $k-1$.'),
            eq(r'\hat{x}_{k|k-1} = F\,\hat{x}_{k-1} + B\,u_k \qquad P_{k|k-1} = F P_{k-1} F^{T} + Q',
               'Kalman filter, predict'),
            eq(r'K = P_{k|k-1} H^{T} \left( H P_{k|k-1} H^{T} + R \right)^{-1} \quad \hat{x}_k = \hat{x}_{k|k-1} + '
               r'K \left( z_k - H\hat{x}_{k|k-1} \right) \quad P_k = (I - K H)\,P_{k|k-1}', 'Kalman filter, update'),
        ]),
        ('planning', 'Path planning with A*', [
            p('To find the shortest route across a map, divide it into cells and search outwards from the start. '
              'Dijkstra\'s algorithm always expands the cell nearest the start, so it spreads evenly in all '
              'directions. A* expands the cell with the lowest estimated total, cost so far plus a guess at the '
              'cost to go:'),
            eq(r'f(n) = g(n) + h(n) \qquad h(n) = \left| x_n - x_{goal} \right| + \left| y_n - y_{goal} \right|',
               'A* search', 'the guess $h$ must never overestimate, or the path may not be the shortest'),
            fig(plan_figure, f'Shaded cells were expanded, in order. Both find a path of {length} steps; A* '
                f'expanded {astar_count} cells to Dijkstra\'s {dijkstra}, since its guess steers it towards the '
                f'goal. It still searches the pocket in the wall before it finds the way around.'),
            code(inspect.getsource(manhattan) + '\n\n' + inspect.getsource(astar)),
            p('With $h = 0$ the same code is Dijkstra\'s algorithm. Real planners add diagonal moves, costs for '
              'rough ground, and a margin around obstacles for the robot\'s width.'),
            note('Read more, in DOCS → ROBOTICS LIBRARY: <em>A Mathematical Introduction to Robotic '
                 'Manipulation</em> by Murray, Li and Sastry for frames, kinematics and Jacobians; '
                 '<em>Introduction to Autonomous Robots</em> by Correll and others for wheeled robots, sensors '
                 'and the Kalman filter; <em>Planning Algorithms</em> by LaValle for search and motion planning; '
                 'and <em>Feedback Systems</em> by Åström and Murray for control.'),
        ]),
    ]
