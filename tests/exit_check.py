"""Exit must always bring back the cover:
- normal browser; several instant taps on Exit or on a card (never leave the arcade, one Exit is enough);
- a window that ignores the step back (as reported in a Chrome app installed on Windows);
- the phone's / browser's Back button from a game.

    python3 tests/exit_check.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, launch, SIZES
from playwright.sync_api import sync_playwright
port = start_server(8973)
fails = []
def game(pg):
    return [x for x in pg.frames if x != pg.main_frame and x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")][0]
def on_cover(pg):
    return pg.evaluate("!document.getElementById('cover').hidden&&[...document.querySelectorAll('iframe')].every(f=>f.hidden)")
def check(name, ok):
    print(('ok   ' if ok else 'FAIL ') + name); ok or fails.append(name)
with sync_playwright() as pw:
    b = launch(pw)
    for label, script in [('normal window', ''), ('window that ignores the step back', "history.back=function(){};history.go=function(){};")]:
        ctx = b.new_context(**SIZES['iphone12']); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        if script: ctx.add_init_script(script)
        pg.goto('http://127.0.0.1:%d/tests/README.md' % port); pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(600)
        for g in ['kb', 'oth', 'ws', 'sdk', 'rem']:
            pg.click('.card[data-g="%s"]' % g); pg.wait_for_timeout(500)
            game(pg).evaluate("document.querySelector('.mnu').click()"); pg.wait_for_timeout(400)
            check('%s: Exit from %s shows the cover' % (label, g), on_cover(pg) and pg.url.endswith('index.html'))
        for n in (2, 5):
            pg.click('.card[data-g="kb"]'); pg.wait_for_timeout(500)
            game(pg).evaluate("(n)=>{const b=document.querySelector('.mnu');for(let i=0;i<n;i++)b.click()}", n); pg.wait_for_timeout(600)
            check('%s: %d instant taps on Exit stay in the arcade' % (label, n), on_cover(pg) and pg.url.endswith('index.html'))
        pg.evaluate("(()=>{const c=document.querySelector('.card[data-g=\"oth\"]');c.click();c.click();c.click()})()"); pg.wait_for_timeout(500)
        game(pg).evaluate("document.querySelector('.mnu').click()"); pg.wait_for_timeout(500)
        check('%s: 3 taps on a card, then one Exit' % label, on_cover(pg))
        pg.click('.card[data-g="ws"]'); pg.wait_for_timeout(400)
        check('%s: a game opens again after all that' % label, not on_cover(pg))
        if not script:
            pg.go_back(); pg.wait_for_timeout(400)
            check('normal window: Back button from a game shows the cover', on_cover(pg) and pg.url.endswith('index.html'))
        check('%s: no errors' % label, not errs)
        ctx.close()
    b.close()
print('failures:', len(fails))
import sys; sys.exit(1 if fails else 0)
