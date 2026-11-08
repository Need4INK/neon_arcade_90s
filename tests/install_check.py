"""Android install and offline: manifest/installability errors and offline opening, as on GitHub Pages.

    python3 tests/install_check.py

Chrome only reports installability truthfully in a normal (persistent) profile once the service worker controls
the page, so this uses a fresh persistent profile per run. It serves the repo from a subfolder
(/neon_arcade_90s/, like the live site) and also from the root, then goes offline and opens the cover and a game
at /, /index.html and ?fbclid=x. Expected: no errors anywhere, app ID ending in /neon_arcade_90s/.
"""
import os, tempfile
from harness import ROOT, start_server, chrome_path
from playwright.sync_api import sync_playwright

sub = tempfile.mkdtemp()
os.symlink(ROOT, os.path.join(sub, 'neon_arcade_90s'))
start_server(8835, sub); start_server(8836, ROOT)

with sync_playwright() as pw:
    for base in ['http://localhost:8835/neon_arcade_90s', 'http://localhost:8836']:
        for start in ['/', '/index.html']:
            kw = dict(viewport={'width': 412, 'height': 915}, is_mobile=True, has_touch=True)
            if chrome_path(): kw['executable_path'] = chrome_path()
            ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), **kw)
            pg = ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto(base + start); pg.wait_for_timeout(2500); pg.reload(); pg.wait_for_timeout(2500)
            c = ctx.new_cdp_session(pg)
            print(base + start, '| manifest errors:', c.send('Page.getAppManifest').get('errors'),
                  '| installability errors:', c.send('Page.getInstallabilityErrors').get('installabilityErrors'),
                  '| app ID:', c.send('Page.getAppId').get('appId'))
            ctx.set_offline(True)
            for q in ['/', '/index.html', '/?fbclid=x']:
                pg.goto(base + q); pg.wait_for_timeout(1200)
                cards = pg.evaluate("document.querySelectorAll('.card').length")
                pg.click('.card[data-g="rem"]'); pg.wait_for_timeout(800)
                game = pg.evaluate("[...document.querySelectorAll('iframe')].some(f=>!f.hidden)")
                print('   offline', q, '| cards:', cards, '| game opens:', game)
            print('   console errors:', errs)
            ctx.close()
