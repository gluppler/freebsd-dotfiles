from html import escape

import page
from mathml import tex

NAME = '12-formulas'
TITLE = 'Formula sheet'
LEDE = ('Every named equation in the guide, chapter by chapter. Each name links to the place it is explained, '
        'beside its figures.')


def sections():
    out = []
    for chapter in page.BOOK:
        rows = [(key, source) for owner, key, source in page.KEY if owner is chapter]
        if rows:
            body = ''.join(f'<tr><td><a href="{chapter.NAME}.html#{page.anchor(key)}">{escape(key)}</a></td>'
                           f'<td>{tex(source, display=True)}</td></tr>' for key, source in rows)
            out.append((chapter.NAME[3:], chapter.TITLE, [f'<table class="sheet"><tbody>{body}</tbody></table>']))
    return out
