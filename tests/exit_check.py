"""Exit pressed several times at once must land on the cover, never step back out of the arcade;
several instant taps on a card must still need only one Exit.

    python3 tests/exit_check.py
"""
import sys
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, launch, SIZES
from playwright.sync_api import sync_playwright
port=start_server(8973)
with sync_playwright() as pw:
    b=launch(pw); ctx=b.new_context(**SIZES['iphone12']); pg=ctx.new_page()
    pg.goto('http://127.0.0.1:%d/tests/README.md'%port); pg.goto('http://127.0.0.1:%d/index.html'%port); pg.wait_for_timeout(600)
    for n in (2,5):
        pg.click('.card[data-g="kb"]'); pg.wait_for_timeout(700)
        fr=[x for x in pg.frames if x!=pg.main_frame and x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")][0]
        fr.evaluate("(n)=>{const b=document.querySelector('.mnu');for(let i=0;i<n;i++)b.click()}",n); pg.wait_for_timeout(600)
        print(n,'instant taps on Exit -> page:',pg.url.split('/')[-1],'| cover cards:',pg.evaluate("document.querySelectorAll('.card').length"))
    pg.evaluate("(()=>{const c=document.querySelector('.card[data-g=\"oth\"]');c.click();c.click();c.click()})()"); pg.wait_for_timeout(700)
    fr=[x for x in pg.frames if x!=pg.main_frame and x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")][0]
    fr.evaluate("document.querySelector('.mnu').click()"); pg.wait_for_timeout(600)
    print('3 instant taps on a card, then one Exit -> game frames showing:',pg.evaluate("[...document.querySelectorAll('iframe')].filter(f=>!f.hidden).length"),'| page:',pg.url.split('/')[-1])
    b.close()
