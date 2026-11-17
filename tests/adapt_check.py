"""Adjusting to the player (blueprint 6a) in real play: after a whole game against the CPU the game notes your result
in <game>-adapt (kb-adapt, oth-adapt, remi-adapt) for that level; never during a game, never at Hard, never in a
2-player game; the next game's CPU plays with it. Remi notes your place at the table when a match ends.

    python3 tests/adapt_check.py

Prints one line per check; False means it failed (exit code 1 via harness.strict()). How far each level moves
(and that the levels never overlap) is measured by tests/ai_tournament.py all --adapt.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, to_cover, strict

strict()
fails = 0


def check(name, ok, info=''):
    global fails
    fails += 0 if ok else 1
    print(f'  {name}: {ok}', info)


# one whole game: the player taps a random legal move; returns (result for you, the saved value before the last move)
KB = r"""async([lv,two])=>{const sl=ms=>new Promise(r=>setTimeout(r,ms));__ai.fast=true;mode=two?'2p':'cpu';S.diff=lv;start();
 const before=localStorage.getItem('kb-adapt');let same=true,n=0;
 while(!over&&n++<3000){const bs=[...document.querySelectorAll('.col.can')];if(bs.length)bs[Math.floor(Math.random()*bs.length)].click();
  await sl(15);if(!over&&localStorage.getItem('kb-adapt')!==before)same=false}
 await sl(50);const a=total(p),b=total(c);return {won:a>b?1:a<b?-1:0,same,over,saved:localStorage.getItem('kb-adapt')}}"""
OTH = r"""async(lv)=>{const sl=ms=>new Promise(r=>setTimeout(r,ms));__ai.fast=true;mode='cpu';S.diff=lv;start();
 const before=localStorage.getItem('oth-adapt');let same=true,n=0;
 while(!over&&n++<6000){if(!busy&&turn===P){const ms=moves(bd,P);if(ms.length){const m=ms[Math.floor(Math.random()*ms.length)];
   document.querySelectorAll('#board .sq')[m.r*8+m.c].click()}}
  await sl(15);if(!over&&localStorage.getItem('oth-adapt')!==before)same=false}
 await sl(50);let a=0,z=0;bd.forEach(r=>r.forEach(v=>v===P?a++:v===C?z++:0));return {won:a>z?1:a<z?-1:0,same,over,saved:localStorage.getItem('oth-adapt')}}"""


def expect(prev, won):
    return max(-1, min(1, round((prev * .8 + .2 * won) * 1000) / 1000))


port = start_server(8961)
pw, b, page = open_page(port, 'iphone12')
for g, key, js in [('kb', 'kb-adapt', KB), ('oth', 'oth-adapt', OTH)]:
    print(g)
    page.evaluate(f"localStorage.removeItem('{key}')")
    f = open_game(page, g)
    prev = {'easy': 0, 'normal': 0}
    for lv in ['easy', 'easy', 'normal', 'hard']:
        r = f.evaluate(js, lv) if g == 'oth' else f.evaluate(js, [lv, False])
        saved = json.loads(r['saved'] or '{}')
        if lv != 'hard':
            prev[lv] = expect(prev[lv], r['won'])
        check(f'{lv} game (you {["lost", "tied", "won"][r["won"] + 1]}): noted after the game, not during it',
              r['over'] and r['same'] and saved.get('easy', 0) == prev['easy'] and saved.get('normal', 0) == prev['normal'] and 'hard' not in saved, saved)
    k = f.evaluate(f"naKnobs('{g}','easy').adapt")
    check('the next Easy game plays with it', k == prev['easy'], k)
    if g == 'kb':
        r = f.evaluate(js, ['easy', True])
        check('2-player game: nothing noted', r['over'] and json.loads(r['saved'] or '{}').get('easy', 0) == prev['easy'])
        f.evaluate("mode='cpu';start()")
    f.evaluate("__ai.fast=false")
    to_cover(page)
print('console errors:', page.errors[:5]); fails += len(page.errors)
b.close(); pw.stop()

# Remi: the test build (tests/ai_tournament.py) exposes endRound; a match is ended by setting the scores near the target
sys.argv = [sys.argv[0], 'remi']
import ai_tournament as T
d = T.remi_copy(); port = start_server(8962, root=d); pw, b, page = open_page(port, 'iphone12')
page.evaluate("localStorage.setItem('remi-rules-seen','1');localStorage.removeItem('remi_game2');localStorage.removeItem('remi-adapt')")
f = open_game(page, 'rem', 1200)
REMI = r"""(o)=>{const R=__remi;R.lvl=o.lvl;R.newGame();const G=R.G;R.G.pl.forEach((P,i)=>P.score=o.sc[i]);
 const before=localStorage.getItem('remi-adapt');R.endRound(-1,-1,'');const me=G.pl[0].score;let r=0;G.pl.forEach((P,q)=>{if(q)r+=P.score>me?1:P.score===me?.5:0});
 return {over:G.over,place:1-2*r/3,before,saved:localStorage.getItem('remi-adapt'),sc:G.pl.map(P=>P.score)}}"""
print('rem')
prev = {'easy': 0, 'normal': 0}
for lvl, sc in [(0, [2000, 0, 0, 0]), (0, [0, 2000, 1500, 1000]), (1, [1000, 3000, 0, 0]), (2, [3000, 0, 0, 0]), (0, [0, 0, 0, 0])]:
    lv = ['easy', 'normal', 'hard'][lvl]
    r = f.evaluate(REMI, {'lvl': lvl, 'sc': sc})
    if r['over'] and lv != 'hard':
        prev[lv] = expect(prev[lv], r['place'])
    saved = json.loads(r['saved'] or '{}')
    what = 'match over, place %+.2f' % r['place'] if r['over'] else 'round only (match goes on)'
    check(f'{lv}: {what}', saved.get('easy', 0) == prev['easy'] and saved.get('normal', 0) == prev['normal'] and 'hard' not in saved, saved)
print('console errors:', page.errors[:5]); fails += len(page.errors)
b.close(); pw.stop()
print('adapt failures:', fails)
