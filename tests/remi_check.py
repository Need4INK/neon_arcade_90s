"""Remi: auto-play with a rule check, and the reload-after-draw fix.

    python3 tests/remi_check.py            # 4 rounds per CPU level (Easy, Norm, Hard)
    python3 tests/remi_check.py 2          # 2 rounds per level

You draw and discard; the CPUs play normally at Fast speed. About every 5 steps it checks that all 106 tiles are
accounted for (pile + discards + hands + table, each once) and that every formation on the table is valid
(the game's own `analyze`); that nobody takes a discard before opening (house rule; board players excepted); and that
every CPU opening has 45+ points with at least one run and one set, or is a set of 1s alone (house rule). Then that
reopening after a draw keeps the drawn tile, and that an empty pile is refilled from the discards (house rule).
Uses the game's test hook `window.__remi` (G, T, hDraw, hDiscard, sel, analyze, lvl, spd, ...).
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


# CPUs take the last discard with G.disc.pop(): wrap it (re-wrapped every step, as each round makes a new row)
# and record whether the taker had opened (or plays on the board) at that moment
HOOK = """(()=>{window.__takes=window.__takes||[];const G=__remi.G,d=G.disc;if(d.__w)return;d.__w=1;
 d.pop=function(){const P=G.pl[G.cur];__takes.push([G.cur,P.opened||P.board]);return Array.prototype.pop.call(this)}})()"""


# Every CPU opening: once a CPU has opened and its turn is over, its formations (all laid that turn: adding comes later)
# must hold 45+ opening points with a run and a set, or be a single set of 1s
OPENS = """(()=>{if(window.__op)return;window.__op={prev:[],pend:{},bad:[],n:0};setInterval(()=>{const R=__remi,G=R.G;if(!G)return;
 G.pl.forEach((P,i)=>{if(i&&P.opened&&!__op.prev[i]&&!P.board)__op.pend[i]=1;__op.prev[i]=P.opened});
 for(const p in __op.pend){if(G.cur===+p&&G.phase!=='over')continue;delete __op.pend[p];__op.n++;
  let pts=0,runs=0,sets=0,ones=0;G.melds.filter(m=>m.o===+p).forEach(m=>{const a=R.analyze(m.t);if(!a){__op.bad.push('invalid');return}pts+=a.pts;
   if(a.type==='run')runs++;else{sets++;if(a.seq.every(x=>x.n===1||x.n===14))ones++}});
  if(!((pts>=45&&runs&&sets)||(!runs&&sets===1&&ones)))__op.bad.push('CPU '+p+': '+pts+' pts, '+runs+' runs, '+sets+' sets')}},20)})()"""


def fresh(lvl):
    page.evaluate("localStorage.removeItem('remi_game2')"); page.reload(); page.wait_for_timeout(700)
    open_game(page, 'rem', 700); f = fr(); f.evaluate(f"__remi.lvl={lvl};__remi.spd=2"); f.evaluate(HOOK); f.evaluate(OPENS); return f


viol = checks = takes = opens = 0
rounds = {}
for lvl, name in [(0, 'Easy'), (1, 'Norm'), (2, 'Hard')]:
    f = fresh(lvl); rounds[name] = 0
    for step in range(8000):
        f.evaluate(HOOK); ph = f.evaluate(STEP)
        if ph == 'over':
            rounds[name] += 1
            if rounds[name] >= ROUNDS or f.evaluate("__remi.G.over"): break
            f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>/Next round/.test(b.textContent)).click()")
            page.wait_for_timeout(300); continue
        if step % 5 == 0:
            n, u, bad = f.evaluate(CHK); checks += 1
            if n != 106 or u != 106 or bad: viol += 1; print('VIOLATION', name, n, u, bad)
        page.wait_for_timeout(40)
    tk = f.evaluate("__takes"); takes += len(tk)
    op = f.evaluate("__op"); opens += op['n']
    for x in op['bad']: viol += 1; print('VIOLATION opening:', name, x)
    for m, ok in tk:
        if not ok: viol += 1; print('VIOLATION take before opening:', name, 'CPU', m)
print('rounds:', rounds, '| checks:', checks, '| CPU takes:', takes, '| CPU openings:', opens, '| violations:', viol)

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

# Pile runs out (house rule): on your draw, with the whole pile moved into the discard row, the discards (all but the
# first and the last) become a new pile, you draw from it, and all 106 tiles are still there
f = fresh(1)
for i in range(400):
    s = f.evaluate("({ph:__remi.G.phase,cur:__remi.G.cur,tn:__remi.G.tn})")
    if s['ph'] == 'draw' and s['cur'] == 0 and s['tn'] >= 4: break
    f.evaluate(STEP); page.wait_for_timeout(150)
k = f.evaluate("(()=>{const G=__remi.G;G.disc.splice(1,0,...G.pile.splice(0));return G.disc.length})()")
f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Draw').click()"); page.wait_for_timeout(300)
r = f.evaluate("({pile:__remi.G.pile.length,row:__remi.G.disc.length,ph:__remi.G.phase,msg:document.getElementById('msg').textContent})")
n, u, bad = f.evaluate(CHK)
ok = r['pile'] == k - 3 and r['row'] == 2 and r['ph'] == 'play' and r['msg'].startswith('Discards reshuffled') and n == u == 106 and not bad
print('pile runs out, discards reshuffled:', 'OK' if ok else 'FAIL', r)
print('console errors:', page.errors)
b.close(); pw.stop()
