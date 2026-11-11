#!/usr/bin/env python3
"""Write the electronics guide to docs/electronics, or --check that it is current."""
import sys
from pathlib import Path

import draw
import page
import contents
import symbols
import dc
import ac
import semiconductors
import opamps
import digital
import signals
import robotics
import interfaces
import pcb
import badges
import formulas

OUT = Path(__file__).resolve().parents[2] / 'docs/electronics'
CHAPTERS = (contents, symbols, dc, ac, semiconductors, opamps, digital, signals, robotics, interfaces, pcb,
            badges, formulas)


def render():
    page.KEY.clear()
    files = {}
    for index, chapter in enumerate(CHAPTERS):
        draw.Figure.count = 0
        files[f'{chapter.NAME}.html'] = page.render(chapter, index, CHAPTERS)
    return files


def main(args):
    if args not in ([], ['--check']):
        print('Use build.py [--check].', file=sys.stderr)
        return 2
    files = render()
    current = {path.name: path.read_text(encoding='utf-8') for path in OUT.glob('*.html')}
    if args:
        stale = sorted(name for name in set(files) | set(current) if files.get(name) != current.get(name))
        for name in stale:
            print(f'Out of date: docs/electronics/{name}', file=sys.stderr)
        return 1 if stale else 0
    OUT.mkdir(exist_ok=True)
    for name in current:
        if name not in files:
            (OUT / name).unlink()
    for name, text in files.items():
        if current.get(name) != text:
            (OUT / name).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
