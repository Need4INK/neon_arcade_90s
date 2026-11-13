"""Remi with a mouse (laptop window 1366 x 657, no touch): the discard row and a wide Landscape rack slide sideways with the
wheel, the table, discard row and rack can be dragged when they hold more than fits, a drag never taps a tile, and a plain
click still does. Neon and Medias upright, Medias Landscape.

    python3 tests/mouse_scroll_check.py        # exit code 1 if anything fails
"""
import sys
import harness
from harness import start_server, open_page, open_game
from device_sweep import STRESS

port = start_server(8849)
harness.SIZES['desk'] = dict(viewport={'width': 1366, 'height': 657})
pw, b, page = open_page(port, 'desk')
page.evaluate("localStorage.setItem('remi-rules-seen','1')"); page.reload(); page.wait_for_timeout(700)
f = open_game(page, 'rem')
for _ in range(40):
    ph = f.evaluate("__remi.G.phase")
    if ph == 'dbl':
        f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Play').click()")
    elif ph in ('draw', 'play'):
        break
    page.wait_for_timeout(300)
# 32 small formations (more than the Landscape table shows), a few tiles in hand
FULL = """(()=>{const R=__remi,G=R.G;const melds=[];for(let k=0;k<2;k++)for(let c=0;c<4;c++)[[1,3],[4,6],[7,9],[10,12]].forEach(([a,b],i)=>{const t=[];for(let n=a;n<=b;n++)t.push(k*52+c*13+n-1);melds.push({o:(c+i)%4,t})});
 G.melds=melds;G.own=Array(106).fill(-1);melds.forEach(m=>m.t.forEach(id=>G.own[id]=m.o));G.pl[0].hand=[12,25,38,51,64];G.pl[0].opened=true;G.disc=[77,90];G.pile=[103,104,105];[1,2,3].forEach(p=>{G.pl[p].hand=[];G.pl[p].opened=true});
 G.cur=0;G.phase='draw';G.tn=20;R.T.start=5;G.atuBy=-1;G.dbl=false;R.sel&&R.sel.clear&&R.sel.clear()})()"""
fails = []
seen = []


def ok(name, cond, extra=''):
    print(('  ok   ' if cond else '  FAIL ') + name, '' if cond else extra)
    if not cond:
        fails.append(name)


def sort():
    f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Sort').click()"); page.wait_for_timeout(250)


def area(sel):
    return f.evaluate("(s)=>{const e=document.querySelector(s),r=e.getBoundingClientRect();e.scrollTop=0;e.scrollLeft=0;return {x:r.left+r.width/2,y:r.top+r.height/2,side:e.scrollWidth>e.clientWidth+1,down:e.scrollHeight>e.clientHeight+1}}", sel)


def pos(sel):
    return f.evaluate("(s)=>{const e=document.querySelector(s);return [Math.round(e.scrollLeft),Math.round(e.scrollTop)]}", sel)


def check(tag, sel, side):
    a = area(sel)
    if not (a['side'] if side else a['down']):
        return
    seen.append(f'{tag} {sel}')
    page.mouse.move(a['x'], a['y']); page.mouse.wheel(0, 100); page.wait_for_timeout(250)
    ok(f'{tag} {sel}: the wheel moves it', pos(sel)[0 if side else 1] > 0, pos(sel))
    area(sel); before = f.evaluate("JSON.stringify([[...__remi.G.pl[0].hand],__remi.G.disc.length,document.querySelectorAll('.tl.sel').length])")
    page.mouse.move(a['x'], a['y']); page.mouse.down(); page.mouse.move(a['x'] - 50, a['y'] - 50, steps=6); page.mouse.up(); page.wait_for_timeout(150)
    ok(f'{tag} {sel}: a drag moves it', pos(sel)[0 if side else 1] > 0, pos(sel))
    ok(f'{tag} {sel}: a drag taps nothing', f.evaluate("JSON.stringify([[...__remi.G.pl[0].hand],__remi.G.disc.length,document.querySelectorAll('.tl.sel').length])") == before)


def run(tag):
    f.evaluate(STRESS['rem'].replace('HN', '26')); sort()          # long discard row, 26 tiles in hand
    check(tag, '#sir', True); check(tag, '#rack', True)
    f.evaluate(FULL); sort()
    check(tag, '#table', False)
    f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Draw').click()"); page.wait_for_timeout(200)
    n = f.evaluate("document.querySelectorAll('#rack .tl.sel').length")
    r = f.evaluate("(()=>{const r=document.querySelector('#rack .tl').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
    page.mouse.click(r[0], r[1]); page.wait_for_timeout(150)
    ok(f'{tag}: a plain click still picks a tile', f.evaluate("document.querySelectorAll('#rack .tl.sel').length") != n)
    page.mouse.click(r[0], r[1]); page.wait_for_timeout(100)


run('Neon upright')
f.click('#bSet'); f.evaluate("document.querySelectorAll('#sSkin button')[1].click()"); page.wait_for_timeout(250); f.click('#bSet')
run('Medias upright')
f.click('#bSet'); f.evaluate("document.querySelectorAll('#sLay button')[1].click()"); page.wait_for_timeout(400)
run('Medias Landscape')
want = ['Neon upright #sir', 'Medias upright #sir', 'Medias Landscape #sir', 'Medias Landscape #rack', 'Medias Landscape #table']
ok('every area that should overflow was tested', all(w in seen for w in want), seen)
ok('no console errors', not page.errors, page.errors[:3])
b.close(); pw.stop()
print('failures:', len(fails), fails)
sys.exit(1 if fails else 0)
