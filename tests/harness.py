"""Shared test harness: a local server and headless Chrome pages at phone sizes.

    from harness import start_server, open_page, game_frame, open_game
    port = start_server(8801)                         # serves the repo root (or root=...)
    pw, browser, page = open_page(port, 'iphone12')   # see SIZES
    f = open_game(page, 'kb')                         # kb, oth, ws, sdk, rem -> the game's frame
    ...
    print(page.errors)                                # console errors from the cover and games
    browser.close(); pw.stop()

'iphone12' simulates the user's iPhone 12 home-screen app with the see-through status bar:
viewport 390x797, screen 390x844, window.__SAFE={t:47,b:34} on the cover and .bar{padding-bottom:34px}
in each game. The page then lays out 844 tall, so use full_page=True for screenshots that show the bar.
Needs: pip install playwright (Chrome is taken from $CHROME, /usr/bin/google-chrome, or Playwright's own).
"""
import functools, http.server, os, shutil, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tests', 'out')

SIZES = {
    'iphone12': dict(viewport={'width': 390, 'height': 797}, screen={'width': 390, 'height': 844},
                     has_touch=True, is_mobile=True, device_scale_factor=3),
    'small': dict(viewport={'width': 320, 'height': 568}, has_touch=True, is_mobile=True, device_scale_factor=2),
    'big': dict(viewport={'width': 430, 'height': 932}, has_touch=True, is_mobile=True, device_scale_factor=3),
    'sideways': dict(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True, device_scale_factor=3),
    'desk': dict(viewport={'width': 1280, 'height': 800}),
}
GAMES = ['kb', 'oth', 'ws', 'sdk', 'rem']


def chrome_path():
    for p in [os.environ.get('CHROME'), '/usr/bin/google-chrome', shutil.which('google-chrome') or '']:
        if p and os.path.exists(p):
            return p
    return None  # Playwright's bundled Chromium


def strict():
    """For the automatic checks on GitHub: after this, a printed False or a non-empty "console errors" list makes the
    script end with exit code 1 (the scripts otherwise only print what they find)."""
    import builtins, atexit
    bad = []; real = builtins.print
    def p(*a, **k):
        if any(x is False for x in a) or (len(a) > 1 and isinstance(a[0], str) and 'console errors' in a[0] and a[1]):
            bad.append(a)
        real(*a, **k)
    builtins.print = p
    def done():
        if bad:
            real('FAILED checks:', len(bad)); sys.stdout.flush(); os._exit(1)
    atexit.register(done)


def start_server(port, root=ROOT):
    """Serve `root` on http://127.0.0.1:port in a background thread (localhost, so the service worker runs)."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=root)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return port


def launch(pw, **kw):
    cp = chrome_path()
    return pw.chromium.launch(executable_path=cp, **kw) if cp else pw.chromium.launch(**kw)


def open_page(port, size='iphone12', path='/index.html'):
    pw = sync_playwright().start()
    browser = launch(pw)
    ctx = browser.new_context(**SIZES[size])
    if size == 'iphone12':
        ctx.add_init_script(
            "if(window===window.top){window.__SAFE={t:47,b:34,l:0,r:0}}else{document.addEventListener('DOMContentLoaded',"
            "function(){var s=document.createElement('style');s.textContent='.bar{padding-bottom:34px}';document.head.appendChild(s)})}")
    page = ctx.new_page()
    page.errors = []
    page.on('pageerror', lambda e: page.errors.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and page.errors.append(m.text))
    page.goto(f'http://127.0.0.1:{port}{path}')
    page.wait_for_timeout(800)
    return pw, browser, page


def game_frame(page):
    """The frame of the game that is on screen."""
    return [x for x in page.frames if x != page.main_frame and
            x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")][0]


def close_panel(f):
    """Close the Rules/Settings panel (Rules opens by itself the first time a game is opened)."""
    f.evaluate("(()=>{const p=document.getElementById('panel');if(p&&!p.hidden){"
               "const b=document.querySelector('#bar button[aria-expanded=true]');b&&b.click()}})()")


def open_game(page, g, wait=900):
    page.click(f'.card[data-g="{g}"]')
    page.wait_for_timeout(wait)
    f = game_frame(page)
    close_panel(f)
    return f


def to_cover(page):
    page.evaluate("kbShowCover()")
    page.wait_for_timeout(300)


def out(name):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, name)
