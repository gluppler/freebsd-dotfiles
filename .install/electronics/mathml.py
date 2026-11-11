"""A small TeX subset rendered as MathML Core, which qutebrowser draws natively.

Letters are italic variables and digits numbers, as in TeX. A braced sub- or
superscript of two or more ASCII letters with no spaces is a label and stays
upright: V_{out}, I_{DS}. Write x_{i j} for a pair of italic indices.
"""
from html import escape

GREEK = {
    'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ϵ', 'varepsilon': 'ε',
    'zeta': 'ζ', 'eta': 'η', 'theta': 'θ', 'vartheta': 'ϑ', 'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ',
    'mu': 'μ', 'nu': 'ν', 'xi': 'ξ', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ',
    'phi': 'ϕ', 'varphi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω', 'Gamma': 'Γ', 'Delta': 'Δ',
    'Theta': 'Θ', 'Lambda': 'Λ', 'Xi': 'Ξ', 'Pi': 'Π', 'Sigma': 'Σ', 'Phi': 'Φ', 'Psi': 'Ψ',
    'Omega': 'Ω'}
OPERATORS = {
    'cdot': '⋅', 'times': '×', 'div': '÷', 'pm': '±', 'mp': '∓', 'approx': '≈', 'neq': '≠', 'ne': '≠',
    'leq': '≤', 'le': '≤', 'geq': '≥', 'ge': '≥', 'll': '≪', 'gg': '≫', 'to': '→', 'rightarrow': '→',
    'leftarrow': '←', 'Rightarrow': '⇒', 'Leftrightarrow': '⇔', 'leftrightarrow': '↔', 'mapsto': '↦',
    'propto': '∝', 'equiv': '≡', 'sim': '∼', 'in': '∈', 'notin': '∉', 'forall': '∀', 'exists': '∃',
    'oplus': '⊕', 'otimes': '⊗', 'land': '∧', 'wedge': '∧', 'lor': '∨', 'vee': '∨', 'lnot': '¬',
    'neg': '¬', 'cdots': '⋯', 'ldots': '…', 'vdots': '⋮', 'ddots': '⋱', 'parallel': '∥', 'perp': '⊥',
    'triangleq': '≜', 'circ': '∘', 'mid': '∣', 'subset': '⊂', 'cup': '∪', 'cap': '∩',
    'setminus': '∖', 'uparrow': '↑', 'downarrow': '↓', 'langle': '⟨', 'rangle': '⟩', 'lfloor': '⌊',
    'rfloor': '⌋', 'lceil': '⌈', 'rceil': '⌉', '|': '‖', '{': '{', '}': '}', 'angle': '∠', 'star': '⋆',
    'ast': '∗', 'gets': '←', 'top': '⊤', 'dagger': '†', '%': '%', '#': '#', '&': '&', '_': '_',
    'lvert': '|', 'rvert': '|',
}
IDENTIFIERS = {'infty': '∞', 'partial': '∂', 'nabla': '∇', 'emptyset': '∅', 'ell': 'ℓ', 'hbar': 'ℏ',
               'degree': '°', 'ohm': 'Ω', 'Re': 'Re', 'Im': 'Im'}
FUNCTIONS = ('sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh', 'ln', 'log',
             'exp', 'max', 'min', 'det', 'arg', 'sgn', 'atan2', 'rank', 'tr', 'diag')
LIMITS = ('lim', 'argmin', 'argmax')
LARGE = {'sum': '∑', 'prod': '∏', 'int': '∫', 'oint': '∮', 'iint': '∬'}
ACCENTS = {'hat': '^', 'bar': '¯', 'dot': '˙', 'ddot': '¨', 'tilde': '~', 'vec': '→'}
SPACES = {',': '0.1667em', ':': '0.2222em', ';': '0.2778em', ' ': '0.25em', 'quad': '1em',
          'qquad': '2em'}
ENVIRONMENTS = {'bmatrix': ('[', ']'), 'pmatrix': ('(', ')'), 'vmatrix': ('|', '|'), 'matrix': ('', ''),
                'cases': ('{', ''), 'aligned': ('', '')}
# Characters TeX prints differently: the minus sign is U+2212.
SYMBOLS = {'-': '−', '*': '∗'}
SCRIPT = {'L': 'ℒ', 'F': 'ℱ', 'Z': '𝒵', 'O': '𝒪', 'R': 'ℛ', 'H': 'ℋ', 'N': '𝒩', 'C': '𝒞'}
DOUBLE = {'R': 'ℝ', 'N': 'ℕ', 'Z': 'ℤ', 'C': 'ℂ', 'Q': 'ℚ'}
# Brackets keep their size unless \left and \right ask them to stretch, as in TeX.
BRACKETS = set('()[]|‖⟨⟩⌊⌋⌈⌉{}')
SMALL_GREEK = 'αβγδεζηθικλμνξοπρςστυφχψω'


def bold(text):
    """Unicode mathematical bold, upright, which a math font carries."""
    out = []
    for c in text:
        if 'A' <= c <= 'Z':
            out.append(chr(0x1D400 + ord(c) - 65))
        elif 'a' <= c <= 'z':
            out.append(chr(0x1D41A + ord(c) - 97))
        elif '0' <= c <= '9':
            out.append(chr(0x1D7CE + ord(c) - 48))
        elif c in SMALL_GREEK:
            out.append(chr(0x1D6C2 + SMALL_GREEK.index(c)))
        else:
            out.append(c)
    return ''.join(out)


def names(text):
    """\\Omega and friends inside \\text and \\mathrm arguments."""
    out, i = [], 0
    while i < len(text):
        if text[i] == '\\':
            j = i + 1
            while j < len(text) and text[j].isalpha():
                j += 1
            name = text[i + 1:j]
            symbol = GREEK.get(name) or IDENTIFIERS.get(name) or OPERATORS.get(name)
            if symbol is None:
                raise ValueError(f'unknown name \\{name} in {text!r}')
            out.append(symbol)
            i = j
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def operator(symbol):
    stretch = ' stretchy="false"' if symbol in BRACKETS else ''
    return f'<mo{stretch}>{escape(symbol)}</mo>'


def wrap(items, always=False):
    items = [item for item in items if item]
    if len(items) == 1 and not always:
        return items[0]
    return '<mrow>' + ''.join(items) + '</mrow>'


class Parser:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        i = 0
        while i < len(source):
            c = source[i]
            if c == '\\':
                j = i + 1
                if j < len(source) and source[j].isalpha():
                    while j < len(source) and source[j].isalpha():
                        j += 1
                    self.tokens.append(('command', source[i + 1:j], i, j))
                else:
                    j = i + 2
                    self.tokens.append(('command', source[i + 1:j], i, j))
            elif c.isdigit() or (c == '.' and source[i + 1:i + 2].isdigit()):
                j = i
                while j < len(source) and (source[j].isdigit() or source[j] == '.'):
                    j += 1
                self.tokens.append(('number', source[i:j], i, j))
            elif c.isspace():
                j = i
                while j < len(source) and source[j].isspace():
                    j += 1
                self.tokens.append(('space', ' ', i, j))
            else:
                j = i + 1
                self.tokens.append(('char', c, i, j))
            i = j
        self.at = 0

    def skip(self):
        while self.at < len(self.tokens) and self.tokens[self.at][0] == 'space':
            self.at += 1

    def peek(self):
        self.skip()
        return self.tokens[self.at][:2] if self.at < len(self.tokens) else (None, None)

    def take(self):
        token = self.peek()
        self.at += 1
        return token

    def fail(self, message):
        raise ValueError(f'{message} in TeX {self.source!r}')

    def expect(self, kind, value):
        if self.take() != (kind, value):
            self.fail(f'expected {value!r}')

    def group_span(self):
        """Token range and source text inside the braces that open here."""
        self.skip()
        if self.peek() != ('char', '{'):
            return None
        depth = 0
        for j in range(self.at, len(self.tokens)):
            if self.tokens[j][:2] == ('char', '{'):
                depth += 1
            elif self.tokens[j][:2] == ('char', '}'):
                depth -= 1
                if not depth:
                    start, end = self.tokens[self.at][3], self.tokens[j][2]
                    return j, self.source[start:end]
        self.fail('unclosed brace')

    def raw(self):
        """The literal text of an argument, spaces kept, for \\text and friends."""
        span = self.group_span()
        if span is None:
            kind, value = self.take()
            return value
        self.at = span[0] + 1
        return span[1]

    def script(self):
        span = self.group_span()
        if span and len(span[1]) >= 2 and span[1].isascii() and span[1].isalpha():
            self.at = span[0] + 1
            return f'<mi>{span[1]}</mi>'
        return self.argument()

    def argument(self):
        """A braced group, or else one token, as in TeX: x_0^t has 0 below and t above."""
        if self.peek() == ('char', '{'):
            self.take()
            body = self.sequence(until='}')
            self.expect('char', '}')
            return wrap(body)
        return self.atom()

    def sequence(self, until=None, stop=()):
        items = []
        while True:
            kind, value = self.peek()
            if kind is None:
                if until:
                    self.fail(f'missing {until!r}')
                break
            if (kind, value) == ('char', until) or (kind, value) in stop:
                break
            if (kind, value) in (('command', 'right'), ('command', 'end'), ('char', '&'), ('command', '\\')):
                self.fail(f'unexpected {value!r}')
            item, function = self.scripted()
            items.append(item)
            # A function name is followed by a thin space unless parentheses follow.
            if function and self.peek() not in (('char', '('), ('command', 'left'), (None, None)):
                items.append('<mspace width="0.1667em"></mspace>')
        return items

    def scripted(self):
        """One atom with its sub- and superscripts; also whether it names a function."""
        kind, value = self.peek()
        function = kind == 'command' and value in FUNCTIONS
        limits = kind == 'command' and value in LIMITS + ('sum', 'prod')
        base = self.atom()
        sub = sup = None
        while self.peek() in (('char', '_'), ('char', '^'), ('char', "'")):
            kind, value = self.take()
            if value == "'":
                sup = '<mo>′</mo>'
            elif value == '_':
                sub = self.script()
            else:
                sup = self.script()
        if sub and sup:
            tag = 'munderover' if limits else 'msubsup'
            return f'<{tag}>{base}{sub}{sup}</{tag}>', function
        if sub:
            tag = 'munder' if limits else 'msub'
            return f'<{tag}>{base}{sub}</{tag}>', function
        if sup:
            tag = 'mover' if limits else 'msup'
            return f'<{tag}>{base}{sup}</{tag}>', function
        return base, function

    def atom(self):
        kind, value = self.take()
        if kind == 'number':
            return f'<mn>{value}</mn>'
        if kind == 'char':
            if value == '{':
                body = self.sequence(until='}')
                self.expect('char', '}')
                return wrap(body, always=True)
            if value.isalpha():
                return f'<mi>{escape(value)}</mi>'
            if value in '}&_^':
                self.fail(f'unexpected {value!r}')
            return operator(SYMBOLS.get(value, value))
        if kind != 'command':
            self.fail('unexpected end')
        if value in GREEK:
            # Capital Greek letters are upright, as in TeX.
            letter = GREEK[value]
            return f'<mi mathvariant="normal">{letter}</mi>' if value[0].isupper() else f'<mi>{letter}</mi>'
        if value in OPERATORS:
            return operator(OPERATORS[value])
        if value in IDENTIFIERS:
            text = IDENTIFIERS[value]
            return f'<mi mathvariant="normal">{text}</mi>' if len(text) == 1 else f'<mi>{text}</mi>'
        if value in FUNCTIONS:
            return f'<mi>{value}</mi>'
        if value in LIMITS:
            return f'<mo movablelimits="true">{"lim" if value == "lim" else value[:3] + " " + value[3:]}</mo>'
        if value in LARGE:
            return f'<mo largeop="true">{LARGE[value]}</mo>'
        if value in SPACES:
            return f'<mspace width="{SPACES[value]}"></mspace>'
        if value == '!':
            return ''
        if value in ('frac', 'dfrac', 'tfrac'):
            top = self.argument()
            style = {'frac': '', 'dfrac': ' displaystyle="true"', 'tfrac': ' displaystyle="false"'}[value]
            return f'<mfrac{style}>{top}{self.argument()}</mfrac>'
        if value == 'sqrt':
            if self.peek() == ('char', '['):
                self.take()
                index = wrap(self.sequence(until=']'))
                self.expect('char', ']')
                return f'<mroot>{self.argument()}{index}</mroot>'
            return f'<msqrt>{self.argument()}</msqrt>'
        if value in ('text', 'mbox'):
            return f'<mtext>{escape(names(self.raw()))}</mtext>'
        if value in ('mathrm', 'operatorname', 'mathsf'):
            text = names(self.raw()).strip()
            if len(text) == 1:
                return f'<mi mathvariant="normal">{escape(text)}</mi>'
            return f'<mi>{escape(text)}</mi>'
        if value == 'mathbf':
            return f'<mi>{escape(bold(names(self.raw())))}</mi>'
        if value == 'mathcal':
            return f'<mi>{escape("".join(SCRIPT.get(c, c) for c in self.raw()))}</mi>'
        if value == 'mathbb':
            return f'<mi>{escape("".join(DOUBLE.get(c, c) for c in self.raw()))}</mi>'
        if value in ACCENTS:
            return f'<mover accent="true">{self.argument()}<mo>{ACCENTS[value]}</mo></mover>'
        if value == 'overline':
            return f'<mrow class="over">{self.argument()}</mrow>'
        if value in ('overset', 'underset'):
            mark = self.argument()
            tag = 'mover' if value == 'overset' else 'munder'
            return f'<{tag}>{self.argument()}{mark}</{tag}>'
        if value == 'left':
            opening = self.fence()
            body = self.sequence(stop=(('command', 'right'),))
            self.expect('command', 'right')
            return wrap([opening, *body, self.fence()], always=True)
        if value == 'begin':
            return self.environment(self.raw())
        if value == 'boxed':
            return f'<mrow class="boxed">{self.argument()}</mrow>'
        self.fail(f'unknown command \\{value}')

    def fence(self):
        kind, value = self.take()
        if (kind, value) == ('char', '.'):
            return ''
        if kind == 'command':
            value = OPERATORS.get(value, value)
        return f'<mo>{escape(value)}</mo>'

    def environment(self, name):
        if name not in ENVIRONMENTS:
            self.fail(f'unknown environment {name}')
        rows, row = [], []
        stop = (('char', '&'), ('command', '\\'), ('command', 'end'))
        while True:
            row.append(self.sequence(stop=stop))
            kind, value = self.take()
            if (kind, value) == ('char', '&'):
                continue
            rows.append(row)
            row = []
            if (kind, value) == ('command', 'end'):
                if self.raw() != name:
                    self.fail(f'\\end does not close {name}')
                break
        if rows and rows[-1] == [[]]:
            rows.pop()
        aligned = name in ('cases', 'aligned')
        body = []
        for cells in rows:
            tds = []
            for column, items in enumerate(cells):
                side = 'left' if name == 'cases' or column % 2 else 'right'
                style = f' style="text-align: {side}"' if aligned else ''
                tds.append(f'<mtd{style}>{wrap(items)}</mtd>')
            body.append('<mtr>' + ''.join(tds) + '</mtr>')
        table = '<mtable>' + ''.join(body) + '</mtable>'
        left, right = ENVIRONMENTS[name]
        if not left and not right:
            return table
        return wrap([f'<mo>{escape(left)}</mo>' if left else '', table,
                     f'<mo>{escape(right)}</mo>' if right else ''], always=True)


def tex(source, display=False):
    """MathML for a TeX source string."""
    parser = Parser(source)
    body = parser.sequence()
    if parser.peek() != (None, None):
        parser.fail('trailing input')
    mode = ' display="block"' if display else ''
    return f'<math{mode}>{"".join(body)}</math>'
