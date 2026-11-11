"""Page template and prose helpers for the electronics guide.

Prose is trusted HTML written in the chapters; $...$ marks inline TeX. Pages are
well-formed XML as well as HTML, carry no scripts, and draw everything inline.
"""
import re
from html import escape

from mathml import tex

KEY = []
BOOK = ()
CURRENT = None

CSS = '''
:root { color-scheme: dark; --bg: #000; --fg: #fff; --text: #e8e8e8; --dim: #aaa; --faint: #666; --line: #2e2e2e; }
* { box-sizing: border-box; }
html { background: var(--bg); color: var(--fg); scroll-padding-top: 64px; }
body { margin: 0; font: 15px/1.7 "Azeret Mono", "Noto Sans Math", monospace; }
.bar { position: sticky; top: 0; z-index: 2; display: flex; flex-wrap: wrap; align-items: center; gap: 8px 24px;
  padding: 10px 24px; background: var(--bg); border-bottom: 1px solid var(--faint); font-size: 12px; }
.bar .site { font-family: Michroma, sans-serif; letter-spacing: .14em; text-transform: uppercase; text-decoration: none; }
.bar .grow { flex: 1; }
.bar label { display: inline-flex; align-items: center; gap: 8px; color: var(--dim); }
#still { accent-color: #fff; margin: 0; }
main { max-width: 1000px; margin: 0 auto; padding: 24px 24px 96px; }
h1, h2, h3 { font-family: Michroma, sans-serif; font-weight: 400; letter-spacing: .06em; line-height: 1.4; }
h1 { font-size: 26px; text-transform: uppercase; margin: 28px 0 10px; }
h2 { font-size: 17px; text-transform: uppercase; margin: 64px 0 14px; padding-top: 20px; border-top: 1px solid var(--line); }
h3 { font-size: 13.5px; margin: 34px 0 8px; }
p, li, td { color: var(--text); }
.lede { color: var(--dim); max-width: 760px; }
a { color: var(--fg); text-decoration-color: var(--faint); text-underline-offset: 3px; }
a:hover, a:focus-visible { text-decoration-color: var(--fg); }
:focus-visible { outline: 2px solid var(--fg); outline-offset: 3px; }
math { font-family: "Noto Sans Math", math; font-size: 1.1em; }
.nowrap { white-space: nowrap; }
.eq { overflow-x: auto; padding: 4px 0; }
.eq math { margin: 10px 0; }
.eq .why { display: block; color: var(--dim); font-size: 12.5px; text-align: center; }
.over { border-top: .065em solid currentColor; padding-top: .06em; }
.boxed { border: 1px solid var(--dim); padding: .25em .4em; }
figure { margin: 26px 0; }
figure svg { display: block; max-width: 100%; height: auto; margin: 0 auto; overflow: visible; }
figcaption { color: var(--dim); font-size: 12.5px; margin: 10px auto 0; max-width: 760px; text-align: center; }
table { border-collapse: collapse; margin: 18px 0; font-size: 13px; }
th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }
th { font-family: Michroma, sans-serif; font-weight: 400; font-size: 10.5px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--dim); }
.wide { overflow-x: auto; }
pre { border: 1px solid var(--line); padding: 14px 16px; overflow-x: auto; font: 13px/1.55 "Azeret Mono", monospace; }
code { font-family: "Azeret Mono", monospace; }
kbd { font: 12px "Azeret Mono", monospace; border: 1px solid var(--faint); border-bottom-width: 2px; padding: 0 5px; }
.note { border-left: 2px solid var(--fg); margin: 20px 0; padding: 2px 0 2px 16px; }
.note p { margin: 6px 0; }
.toc { columns: 2 260px; margin: 16px 0 8px; padding: 0; list-style: none; font-size: 13px; }
.toc li { break-inside: avoid; padding: 2px 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; margin: 18px 0; }
.card { border: 1px solid var(--line); padding: 12px 12px 10px; }
.card svg { display: block; margin: 0 auto 6px; max-width: 100%; height: auto; overflow: visible; }
.card h3 { margin: 4px 0; font-size: 11.5px; }
.card p { margin: 4px 0; font-size: 12.5px; line-height: 1.55; }
.card math { font-size: 1em; }
.card .formula { font-size: 14px; margin-top: 8px; }
.formula math { math-style: normal; }
.chapters { list-style: none; padding: 0; }
.chapters li { border-top: 1px solid var(--line); padding: 12px 0; }
.chapters a { font-family: Michroma, sans-serif; font-size: 13px; letter-spacing: .06em; text-transform: uppercase; }
.chapters p { margin: 4px 0 0; color: var(--dim); font-size: 13px; }
.sheet { width: 100%; }
.sheet td { vertical-align: middle; }
.sheet td:first-child { width: 34%; }
.pager { display: flex; justify-content: space-between; gap: 16px; margin-top: 72px; padding-top: 16px;
  border-top: 1px solid var(--faint); font-size: 13px; }
.w { fill: none; stroke: var(--fg); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.w.thin { stroke-width: 1.3; }
.w.heavy { stroke-width: 4.5; stroke-linecap: butt; }
.w.bold { stroke-width: 3.2; }
.w.dim { stroke: var(--dim); }
.w.faint { stroke: var(--faint); }
.w.dash { stroke-dasharray: 5 5; }
.w.dots { stroke-dasharray: 1.5 5; }
.w.solid, .solid { fill: var(--fg); }
.hollow { fill: var(--bg); }
.fill { fill: var(--fg); stroke: none; }
.shade { fill: #1c1c1c; stroke: none; }
.shade2 { fill: #333; stroke: none; }
.grid { stroke: var(--line); stroke-width: 1; fill: none; }
.curve { stroke-width: 2.2; }
.t { fill: var(--fg); font: 13px "Azeret Mono", "Noto Sans Math", monospace; }
body, pre, kbd, .t { font-variant-ligatures: none; }
.t.s { font-size: 11px; fill: var(--dim); }
.t.b { font-size: 15px; }
.t.mark { font-size: 14px; }
.t.inv { fill: var(--bg); }
.t.head { font-family: Michroma, sans-serif; font-size: 10.5px; letter-spacing: .08em; fill: var(--dim); }
.flow, .flow-halo { fill: none; stroke-linecap: round; stroke-dasharray: 0 16;
  animation: flow var(--t, 1.2s) linear infinite; }
.flow { stroke: var(--fg); stroke-width: 4.5; }
.flow-halo { stroke: var(--bg); stroke-width: 9; }
.rev { animation-direction: reverse; }
.flow.hole { stroke-width: 7; }
.flow.hole-in { stroke: var(--bg); stroke-width: 3.4; }
@keyframes flow { to { stroke-dashoffset: -16; } }
.walker { fill: var(--bg); stroke: var(--fg); stroke-width: 3; }
.phase { opacity: 0; }
.phase.first { opacity: 1; }
html:has(#still:checked) *, html:has(#still:checked) *::after { animation-play-state: paused !important; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; } }
@media (max-width: 640px) { main { padding: 16px 16px 64px; } .bar { padding: 8px 16px; } h1 { font-size: 21px; } }
'''


OPENING, CLOSING = '(["‘“', '.,;:!?)]’”%'


def mathify(text):
    """Prose with $...$ replaced by inline MathML; \\$ is a literal dollar.

    Brackets and punctuation touching an equation stay on its line.
    """
    parts = text.replace('\\$', '\0').split('$')
    if len(parts) % 2 == 0:
        raise ValueError(f'unbalanced $ in {text[:60]!r}')
    words = [part.replace('\0', '$') for part in parts[0::2]]
    out = [words[0]]
    for k, source in enumerate(parts[1::2]):
        before, after = out[-1], words[k + 1]
        lead = len(before) - len(before.rstrip(OPENING))
        trail = len(after) - len(after.lstrip(CLOSING))
        math = tex(source.replace('\0', '\\$'))
        if lead or trail:
            out[-1] = before[:len(before) - lead]
            math = f'<span class="nowrap">{before[len(before) - lead:]}{math}{after[:trail]}</span>'
        out += [math, after[trail:]]
    return ''.join(out)


def p(text, cls=None):
    attribute = f' class="{cls}"' if cls else ''
    return f'<p{attribute}>{mathify(text)}</p>'


def ul(*items):
    return '<ul>' + ''.join(f'<li>{mathify(item)}</li>' for item in items) + '</ul>'


def ol(*items):
    return '<ol>' + ''.join(f'<li>{mathify(item)}</li>' for item in items) + '</ol>'


def m(source):
    return tex(source)


def anchor(key):
    """The id of a keyed equation, from its name."""
    return 'eq-' + re.sub('[^a-z0-9]+', '-', key.lower()).strip('-')


def eq(source, key=None, why=None):
    """A displayed equation; key files it on the formula sheet under that name."""
    attribute = ''
    if key:
        KEY.append((CURRENT, key, source))
        attribute = f' id="{anchor(key)}"'
    note = f'<span class="why">{mathify(why)}</span>' if why else ''
    return f'<div class="eq"{attribute}>{tex(source, display=True)}{note}</div>'


def fig(figure, caption):
    return f'<figure>{figure.svg()}<figcaption>{mathify(caption)}</figcaption></figure>'


def table(head, *rows, wide=False):
    cells = ''.join(f'<th>{mathify(h)}</th>' for h in head)
    body = ''.join('<tr>' + ''.join(f'<td>{mathify(c)}</td>' for c in row) + '</tr>' for row in rows)
    out = f'<table><thead><tr>{cells}</tr></thead><tbody>{body}</tbody></table>'
    return f'<div class="wide">{out}</div>' if wide else out


def code(source):
    return f'<pre><code>{escape(source.strip(chr(10)))}</code></pre>'


def note(*paragraphs):
    return '<div class="note">' + ''.join(p(text) for text in paragraphs) + '</div>'


def h3(title):
    return f'<h3>{mathify(title)}</h3>'


def card(figure, title, *paragraphs):
    """A symbol card; a paragraph that starts with an equation is set as a formula."""
    return (f'<div class="card">{figure.svg()}<h3>{mathify(title)}</h3>' +
            ''.join(p(text, 'formula' if text.startswith('$') else None) for text in paragraphs) + '</div>')


def cards(*items):
    return '<div class="cards">' + ''.join(items) + '</div>'


def library(entry, title):
    """Where to read further in the docs menu."""
    return f'<em>DOCS → {escape(entry)} → {escape(title)}</em>'


def link(name, anchor=None, label=None):
    target = f'{name}.html' + (f'#{anchor}' if anchor else '')
    return f'<a href="{target}">{escape(label or name)}</a>'


def render(chapter, index, chapters):
    """One chapter as a complete page."""
    global BOOK, CURRENT
    BOOK, CURRENT = chapters, chapter
    sections = chapter.sections()
    toc = ''.join(f'<li><a href="#{sid}">{mathify(title)}</a></li>' for sid, title, _ in sections)
    body = ''.join(f'<section id="{sid}"><h2>{mathify(title)}</h2>{"".join(parts)}</section>'
                   for sid, title, parts in sections)
    previous = chapters[index - 1] if index else None
    following = chapters[index + 1] if index + 1 < len(chapters) else None
    pager = ('<nav class="pager">' +
             (f'<a href="{previous.NAME}.html">← {escape(previous.TITLE)}</a>' if previous else '<span></span>') +
             (f'<a href="{following.NAME}.html">{escape(following.TITLE)} →</a>' if following else '<span></span>') +
             '</nav>')
    nav = ''
    if previous:
        nav += f'<a href="{previous.NAME}.html">← previous</a>'
    if following:
        nav += f'<a href="{following.NAME}.html">next →</a>'
    toc_html = f'<ul class="toc">{toc}</ul>' if len(sections) > 1 and getattr(chapter, 'TOC', True) else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta name="color-scheme" content="dark"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"/>
<title>{escape(chapter.TITLE)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="bar"><a class="site" href="00-contents.html">Electronics guide</a><span class="grow"></span>{nav}<label><input type="checkbox" id="still"/>Pause motion</label></header>
<main>
<h1>{escape(chapter.TITLE)}</h1>
<p class="lede">{mathify(chapter.LEDE)}</p>
{toc_html}
{body}
{pager}
</main>
</body>
</html>
'''
