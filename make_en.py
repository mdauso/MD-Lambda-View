#!/usr/bin/env python3
"""
MD-Lambda-View — generate the English PWA pages from the German originals.

Usage:  python3 make_en.py [--pwa DIR] [--report]

Reads  <pwa>/index.html, 2d.html, 3d.html
Writes <pwa>/index-en.html, 2d-en.html, 3d-en.html

Replacement is deliberately conservative: a German string is only swapped
when it matches a table entry EXACTLY (after trimming) and sits in one of
these places:
  * a text node outside <script> / <style>
  * a title / placeholder / alt / aria-label attribute value
  * a complete JavaScript string literal  ('…' "…" `…` without ${})

Anything not covered by the table is listed in the report so new German
text can never slip through unnoticed.
"""

import re, json, sys, os
from pathlib import Path

HERE = Path(__file__).parent
PWA  = Path(sys.argv[sys.argv.index('--pwa') + 1]) if '--pwa' in sys.argv else HERE.parent / 'pwa'

TR = json.load(open(HERE / 'translations.json', encoding='utf-8'))
TR = {k: v for k, v in TR.items() if not k.startswith('_')}

# German pages → English page names
PAGE_MAP = {
    'index.html': 'index-en.html',
    '2d.html':    '2d-en.html',
    '3d.html':    '3d-en.html',
}

GERMAN_HINT = re.compile(r'[ÄÖÜäöüß]|\b(der|die|das|und|oder|für|mit|nicht|keine|wird|werden|'
                         r'zum|zur|von|bei|auf|aus|eine|einen|einem|ist|sind|dann|noch|auch|'
                         r'Datei|Daten|Werte|Punkte|Bereich|laden|wählen|Fehler|Ziel|Grenze|'
                         r'Schritt|Anzeige|zeigen|anzeigen)\b', re.I)

# Strings that look German but are code / data we must never touch
SAFE_SKIP = re.compile(r'^(de-DE|sw\.js|[.#][\w-]+|[a-z][a-zA-Z0-9]*|rgba?\(|linear-gradient|'
                       r'translateY|scene\.camera|text/csv|image/|application/)')


class Report:
    def __init__(self):
        self.untranslated = {}   # file → set of strings
        self.used = set()

    def miss(self, fn, s):
        self.untranslated.setdefault(fn, set()).add(s)

    def hit(self, s):
        self.used.add(s)


def translate_exact(s, rep, fn):
    """Return the translation of a complete string, or None."""
    stripped = s.strip()
    if not stripped:
        return None
    if stripped in TR:
        rep.hit(stripped)
        out = TR[stripped]
        # preserve surrounding whitespace of the original
        lead = s[:len(s) - len(s.lstrip())]
        tail = s[len(s.rstrip()):]
        return lead + out + tail
    # Not in the table — flag it if it looks like German prose
    if GERMAN_HINT.search(stripped) and not SAFE_SKIP.match(stripped):
        rep.miss(fn, stripped)
    return None


def process_blocks(html, rep, fn):
    """Replace whole HTML fragments (table keys that contain markup).

    Needed wherever a sentence is broken up by inline tags — English word
    order does not follow the German split, so the fragment is swapped as
    one piece.
    """
    for de, en in TR.items():
        if '<' not in de:
            continue
        if de in html:
            html = html.replace(de, en)
            rep.hit(de)
    return html


def process_dynamic_templates(html, rep, fn):
    """Translate exact template-literal fragments containing ${...}.

    The ordinary quoted-string matcher cannot recognize interpolations whose
    expressions contain quoted strings (e.g. `${x ? 'a' : 'b'}`). Process known,
    fully specified fragments first. Longest-first prevents nested fragments
    from shadowing each other. No generic word replacement is performed.
    """
    entries = sorted(((de, en) for de, en in TR.items() if '${' in de),
                     key=lambda pair: len(pair[0]), reverse=True)
    for de, en in entries:
        if de in html:
            html = html.replace(de, en)
            rep.hit(de)
    return html


def process_markup(html, rep, fn):
    """Translate text nodes + attributes, leaving <script>/<style> alone."""
    # Protect script and style blocks
    blocks = []
    def stash(m):
        blocks.append(m.group(0))
        return f'\x00BLOCK{len(blocks)-1}\x00'
    html = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', stash, html)

    # --- text nodes ---
    def fix_text(m):
        pre, body, post = m.group(1), m.group(2), m.group(3)
        if '\x00BLOCK' in body:
            return m.group(0)
        new = translate_exact(body, rep, fn)
        return f'{pre}{new if new is not None else body}{post}'
    html = re.sub(r'(>)([^<>]+)(<)', fix_text, html)

    # --- attributes ---
    def fix_attr(m):
        name, val = m.group(1), m.group(2)
        new = translate_exact(val, rep, fn)
        return f'{name}="{new if new is not None else val}"'
    html = re.sub(r'\b(title|placeholder|alt|aria-label|label)="([^"]*)"', fix_attr, html)

    # Restore blocks
    html = re.sub(r'\x00BLOCK(\d+)\x00', lambda m: blocks[int(m.group(1))], html)
    return html


def process_scripts(html, rep, fn):
    """Translate complete string literals inside our own <script> blocks."""
    def fix_script(m):
        code = m.group(1)
        if len(code) > 400_000:       # inlined third-party library — never touch
            return m.group(0)

        def fix_literal(lm):
            quote, body = lm.group(1), lm.group(2)
            if '\x00' in body:
                return lm.group(0)
            if '${' in body:
                # interpolated template literal: only an exact full match
                # (placeholders included) from the table is swapped
                if body in TR:
                    rep.hit(body)
                    return f'{quote}{TR[body]}{quote}'
                return lm.group(0)
            new = translate_exact(body, rep, fn)
            return f'{quote}{new}{quote}' if new is not None else lm.group(0)

        # '...'  "..."  `...`   (single line, no escapes)
        code = re.sub(r"""(['"`])((?:(?!\1)[^\\\n])*)\1""", fix_literal, code)
        return f'<script>{code}</script>'

    return re.sub(r'<script>([\s\S]*?)</script>', fix_script, html)


def post_fixes(html, src_name):
    """Locale, lang attribute, cross-page links and the language switch."""
    html = html.replace('<html lang="de">', '<html lang="en">')
    html = html.replace("toLocaleString('de-DE')", "toLocaleString('en-US')")
    html = html.replace('toLocaleString("de-DE")', 'toLocaleString("en-US")')
    # Cross-links between the pages must stay inside the English set
    for de, en in PAGE_MAP.items():
        html = html.replace(f'href="{de}"', f'href="{en}"')
        html = html.replace(f"'{de}'", f"'{en}'") if de != 'index.html' else html

    # Flip the language switch: EN active, DE links back to the German page
    html = html.replace(
        '<div class="lang-switch" role="group" aria-label="Sprache">\n'
        '    <span class="lang-opt on" aria-current="true">DE</span>\n'
        '    <a class="lang-opt" href="index-en.html" id="langEn">EN</a>\n'
        '  </div>',
        '<div class="lang-switch" role="group" aria-label="Language">\n'
        '    <a class="lang-opt" href="index.html" id="langEn">DE</a>\n'
        '    <span class="lang-opt on" aria-current="true">EN</span>\n'
        '  </div>'
    )
    # …and the preference logic that goes with it
    html = html.replace("const THIS_LANG = 'de';", "const THIS_LANG = 'en';")
    html = html.replace("const OTHER_PAGE = 'index-en.html';", "const OTHER_PAGE = 'index.html';")
    html = html.replace("localStorage.setItem(LANG_KEY, 'en');", "localStorage.setItem(LANG_KEY, 'de');")
    # Marker so it is obvious which file is generated
    html = html.replace('<head>', '<head>\n<!-- GENERATED FILE — do not edit. '
                        f'Built from {src_name} by i18n/make_en.py -->', 1)
    return html


def main():
    rep = Report()
    written = []
    for de_name, en_name in PAGE_MAP.items():
        src = PWA / de_name
        if not src.exists():
            print(f'  ! {de_name} not found, skipped')
            continue
        html = src.read_text(encoding='utf-8')
        html = process_blocks(html, rep, de_name)
        html = process_dynamic_templates(html, rep, de_name)
        html = process_markup(html, rep, de_name)
        html = process_scripts(html, rep, de_name)
        html = post_fixes(html, de_name)
        (PWA / en_name).write_text(html, encoding='utf-8')
        written.append(en_name)

    print(f'Generated: {", ".join(written)}')
    print(f'Table entries used: {len(rep.used)} / {len(TR)}')

    unused = sorted(set(TR) - rep.used)
    if unused:
        print(f'\nUnused table entries ({len(unused)}):')
        for s in unused[:40]:
            print(f'   · {s[:80]}')

    if rep.untranslated:
        total = sum(len(v) for v in rep.untranslated.values())
        print(f'\n!! Untranslated German strings ({total}):')
        for fn, items in rep.untranslated.items():
            print(f'\n  {fn}:')
            for s in sorted(items):
                print(f'   - {s[:110]}')
    else:
        print('\nNo untranslated German strings found.')


if __name__ == '__main__':
    main()
