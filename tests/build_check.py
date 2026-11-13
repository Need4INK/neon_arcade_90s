"""index.html must be exactly what games/build.py makes from the sources (so nobody ships a page that was edited by hand
or forgot to rebuild).

    python3 tests/build_check.py

The packed fonts are left out of the comparison: another version of the font tool may pack the same font into other bytes.
Exit code 1 if the page differs.
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES = ['Knucklebones', 'Othello', 'Water_Sort', 'Sudoku', 'Remi']
out = os.path.join(tempfile.mkdtemp(), 'index.html')
subprocess.run([sys.executable, os.path.join(ROOT, 'games', 'build.py')] + [os.path.join(ROOT, 'games', g + '.html') for g in GAMES] + [out],
               check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
mask = lambda s: re.sub(r'url\(data:font/[a-z0-9]+;base64,[A-Za-z0-9+/=]+\)', 'url(FONT)', s)
a = mask(open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()); b = mask(open(out, encoding='utf-8').read())
if a == b:
    print('index.html matches the sources'); sys.exit(0)
i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
print('index.html differs from a fresh build (run games/build.py and commit the result).')
print('first difference at character', i, '\n  index.html:', repr(a[max(0, i - 60):i + 60]), '\n  fresh build:', repr(b[max(0, i - 60):i + 60]))
sys.exit(1)
