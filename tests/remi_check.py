"""Remi: auto-play with a rule check, and the reload-after-draw fix.

    python3 tests/remi_check.py            # 4 rounds per CPU level (Easy, Norm, Hard)
    python3 tests/remi_check.py 2          # 2 rounds per level

You draw and discard; the CPUs play normally at Fast speed. About every 5 steps it checks that all 106 tiles are
accounted for (pile + discards + hands + table, each once) and that every formation on the table is valid
(the game's own `analyze`). Then it checks that reopening after a draw keeps the drawn tile (no peeking at the
pile). Uses the game's test hook `window.__remi` (G, T, hDraw, hDiscard, sel, analyze, lvl, spd, ...).
"""
import sys
from harness import start_server, open_page, open_game

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
port = start_server(8834)
pw, b, page = open_page(port, 'small')
fr = lambda: [x for x in page.frames if x != page.main_frame and x.evaluate("!!window.__remi")][0]

CHK = """(()=>{const G=__remi.G;const all=[...G.pile,...G.disc,...G.pl.flatMap(P=>P.hand),...G.melds.flatMap(m=>m.t)];
 return [all.length,new Set(all).size,G.melds.filter(m=>!__remi.analyze(m.t)).length]})()"""
STEP = """(()=>{const R=__remi,G=R.G,btn=t=>[...document.querySelectorAll('#acts button')].find(b=>b.textContent===t);
 if(G.phase==='dbl'){btn('Play').click()}
 else if(G.cur===0&&G.phase==='draw'){btn('Draw').click()}
 else if(G.cur===0&&G.phase==='play'){R.sel.clear();const h=G.pl[0].hand;R.sel.add(h[h.length-1]);R.hDiscard()}
 return G.phase})()"""


def fresh(lvl):
    page.evaluate("localStorage.removeItem('remi_game2')"); page.reload(); page.wait_for_timeout(700)
    open_game(page, 'rem', 700); f = fr(); f.evaluate(f"__remi.lvl={lvl};__remi.spd=2"); return f


viol = checks = 0
rounds = {}
for lvl, name in [(0, 'Easy'), (1, 'Norm'), (2, 'Hard')]:
    f = fresh(lvl); rounds[name] = 0
    for step in range(8000):
        ph = f.evaluate(STEP)
        if ph == 'over':
            rounds[name] += 1
            if rounds[name] >= ROUNDS or f.evaluate("__remi.G.over"): break
            f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>/Next round/.test(b.textContent)).click()")
            page.wait_for_timeout(300); continue
        if step % 5 == 0:
            n, u, bad = f.evaluate(CHK); checks += 1
            if n != 106 or u != 106 or bad: viol += 1; print('VIOLATION', name, n, u, bad)
        page.wait_for_timeout(40)
print('rounds:', rounds, '| checks:', checks, '| violations:', viol)

# Reload after a draw: the drawn tile stays in hand and Draw is off
f = fresh(1)
for i in range(400):
    s = f.evaluate("({ph:__remi.G.phase,cur:__remi.G.cur})")
    if s['ph'] == 'draw' and s['cur'] == 0: break
    f.evaluate(STEP); page.wait_for_timeout(150)
top = f.evaluate("__remi.G.pile[__remi.G.pile.length-1]")
f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Draw').click()"); page.wait_for_timeout(300)
page.reload(); page.wait_for_timeout(800); open_game(page, 'rem', 800); f = fr()
r = f.evaluate(f"({{ph:__remi.G.phase,has:__remi.G.pl[0].hand.includes({top}),n:__remi.G.pl[0].hand.length,"
               "draw:!![...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Draw'&&!b.disabled)})")
print('reload after a draw:', 'OK' if r['ph'] == 'play' and r['has'] and not r['draw'] else 'FAIL', r)
print('console errors:', page.errors)
b.close(); pw.stop()
