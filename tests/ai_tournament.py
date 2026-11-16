"""CPU tournaments: bot against bot with fixed seeds, to measure the CPU levels (blueprint section 7).

    python3 tests/ai_tournament.py                   # all three games, default game counts
    python3 tests/ai_tournament.py kb 400            # Knucklebones, 400 games per pairing (default 1000)
    python3 tests/ai_tournament.py oth 40            # Othello (default 100)
    python3 tests/ai_tournament.py remi 30           # Remi, 30 rounds per pairing (default 200)
    python3 tests/ai_tournament.py all --seed 7      # another seed (default 1)
    python3 tests/ai_tournament.py all --slow        # also time CPU decisions at 4x CPU slow-down

Knucklebones and Othello: every pairing of Easy / Normal / Hard / Random (a player picking any legal move) plays
N games, the two sides swapping who starts every game. Win rate counts a tie as half. Targets (blueprint 7):
Hard beats Normal and Normal beats Easy at least 75%, every level beats Random at least 95%.
Decisions go through the game's `window.__ai.pick(state, level)` once a game registers one (state: Knucklebones
{me, opp, die} -> column; Othello {bd, side} -> {r, c}, side 1 or -1 to move, bd as in the game); until then the
game's own CPU code is called with its globals swapped (`cpuMove` / `cpuPick`), so today's CPUs are measured as
they play. Randomness: the frame's Math.random is replaced by a seeded generator, and `__ai.seed(seed)` is called.

Remi: a never-shipped copy of the game (built in tests/out/ai_remi/) lets all four seats play as CPUs, each seat
with its own level. Two levels share a table (seats A B A B, then B A B A, both on the same deals); it reports points
per round for each level, the gap with its standard error (ok = more than two errors above zero), how often each
closed and how they took from the discard row. Target: Hard averages more points per round than Normal.
    python3 tests/ai_tournament.py remi 400 --vs     # today's CPU against the one from before the AI build, level by level
    python3 tests/ai_tournament.py remi 400 --base   # the old CPU's levels against each other

--slow: Chrome's CPU slow-down at 4x (the iPhone 12 budget) while timing each Knucklebones / Othello decision; for
Remi it counts main-thread tasks over 50 ms during a few drawn rounds and times every CPU decision of 12 rounds.
Writes the numbers to tests/out/ai_tournament.json.
"""
import json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import ROOT, start_server, open_page, open_game, to_cover, out

argv = sys.argv[1:]
SEED = 1
if '--seed' in argv:
    i = argv.index('--seed'); SEED = int(argv[i + 1]); del argv[i:i + 2]
SLOW = '--slow' in argv
VS = '--vs' in argv        # Remi: the new CPU against the one from before the AI build, same level
BASE = '--base' in argv    # Remi: the old CPU's levels against each other (the "before" numbers)
args = [a for a in argv if not a.startswith('--')]
WHICH = args[0] if args else 'all'
N = int(args[1]) if len(args) > 1 else None
LEVELS = ['easy', 'normal', 'hard', 'random']
PAIRS = [('normal', 'easy'), ('hard', 'normal'), ('hard', 'easy'), ('easy', 'random'), ('normal', 'random'), ('hard', 'random')]
RESULTS = {'seed': SEED, 'date': time.strftime('%Y-%m-%d')}

# Seeded randomness inside a game frame (mulberry32), plus the Knucklebones / Othello bot-vs-bot runners
RNG = r"""window.__mk=s=>{let a=s>>>0;return()=>{a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}};
window.__seed=s=>{Math.random=__mk(s);window.__tr=__mk(s*7919+13);try{if(window.__ai&&__ai.seed)__ai.seed(s)}catch(e){}};"""

KB = RNG + r"""
const kbSc=a=>{const n={};a.forEach(v=>n[v]=(n[v]||0)+1);let s=0;for(const v in n)s+=v*n[v]*n[v];return s};
const kbTot=g=>g.reduce((s,a)=>s+kbSc(a),0),kbFull=g=>g.every(a=>a.length>=3),cpg=g=>g.map(a=>a.slice());
window.__times={};
function kbPick(lv,me,opp,d){const free=me.map((a,i)=>a.length<3?i:-1).filter(i=>i>=0);
 if(lv==='random')return free[__tr()*free.length|0];
 const t0=performance.now();let col;
 if(window.__ai&&typeof __ai.pick==='function')col=__ai.pick({me:cpg(me),opp:cpg(opp),die:d},lv);
 else{const sv=[c,p,die,S.diff,hit,NC];c=cpg(me);p=cpg(opp);die=d;S.diff=lv;NC=me.length;const b=c.map(a=>a.length);cpuMove();
  col=c.findIndex((a,i)=>a.length===b[i]+1);[c,p,die,S.diff,hit,NC]=sv}
 (__times[lv]=__times[lv]||[]).push(performance.now()-t0);
 if(free.indexOf(col)<0)throw new Error('KB '+lv+' picked a full column '+col);return col}
window.__kbGame=function(A,B,nc){const g=[[],[]].map(()=>Array.from({length:nc},()=>[])),lv=[A,B];let t=0,n=0;
 while(!kbFull(g[0])&&!kbFull(g[1])&&n++<200){const d=1+Math.floor(__tr()*6),col=kbPick(lv[t],g[t],g[1-t],d);
  g[t][col].push(d);g[1-t][col]=g[1-t][col].filter(x=>x!==d);t=1-t}
 return [kbTot(g[0]),kbTot(g[1])]};
window.__kbMatch=function(A,B,n,nc){let w=0,l=0,ti=0,pts=0;for(let i=0;i<n;i++){const sw=i%2===1,r=sw?__kbGame(B,A,nc).reverse():__kbGame(A,B,nc);
 if(r[0]>r[1])w++;else if(r[0]<r[1])l++;else ti++;pts+=r[0]-r[1]}return {w,l,t:ti,margin:pts/n}};
"""

OTH = RNG + r"""
window.__times={};
const oIn=(i,j)=>i>=0&&j>=0&&i<8&&j<8;
function oFl(b,r,c,s){if(b[r][c])return[];const out=[];for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){if(!dr&&!dc)continue;let i=r+dr,j=c+dc;const L=[];while(oIn(i,j)&&b[i][j]===-s){L.push([i,j]);i+=dr;j+=dc}if(L.length&&oIn(i,j)&&b[i][j]===s)out.push(...L)}return out}
function oMoves(b,s){const m=[];for(let r=0;r<8;r++)for(let c=0;c<8;c++){const f=oFl(b,r,c,s);if(f.length)m.push({r,c,f})}return m}
function othPick(lv,b,s){const ms=oMoves(b,s);if(lv==='random')return ms[__tr()*ms.length|0];
 const t0=performance.now();let m;
 if(window.__ai&&typeof __ai.pick==='function')m=__ai.pick({bd:b.map(r=>r.slice()),side:s},lv);
 else{const sv=[bd,S.diff,turn];bd=s===C?b.map(r=>r.slice()):b.map(r=>r.map(v=>-v));S.diff=lv;turn=C;m=cpuPick();[bd,S.diff,turn]=sv}
 (__times[lv]=__times[lv]||[]).push(performance.now()-t0);
 const mine=ms.find(x=>x.r===m.r&&x.c===m.c);if(!mine)throw new Error('Othello '+lv+' picked an illegal square');return mine}
window.__othGame=function(A,B){const b=Array.from({length:8},()=>Array(8).fill(0));b[3][3]=b[4][4]=-1;b[3][4]=b[4][3]=1;
 const lv={1:A,'-1':B};let s=1,n=0;
 while(n++<130){let ms=oMoves(b,s);if(!ms.length){s=-s;if(!oMoves(b,s).length)break;continue}
  const m=othPick(lv[s],b,s);b[m.r][m.c]=s;m.f.forEach(([i,j])=>b[i][j]=s);s=-s}
 let a=0,z=0;b.flat().forEach(v=>v===1?a++:v===-1?z++:0);return [a,z]};
window.__othMatch=function(A,B,n){let w=0,l=0,ti=0,pts=0;for(let i=0;i<n;i++){const r=i%2?__othGame(B,A).reverse():__othGame(A,B);
 if(r[0]>r[1])w++;else if(r[0]<r[1])l++;else ti++;pts+=r[0]-r[1]}return {w,l,t:ti,margin:pts/n}};
"""

# Othello played through the page (the player taps a random legal square), CPU at its real pace in its Worker
OTH_LIVE = r"""
window.__othLive=async function(lv,games){const sl=ms=>new Promise(r=>setTimeout(r,ms)),R={search:[],turn:[],long:[]};
 let po=null;try{po=new PerformanceObserver(l=>l.getEntries().forEach(e=>R.long.push(e.duration)));po.observe({type:'longtask'})}catch(e){}
 const ob=brain,oc=cpuTurn;let t0=0;
 brain=function(){const w=ob();return {run:d=>{const t=naNow();return w.run(d).then(o=>{R.search.push(naNow()-t);return o})}}};
 cpuTurn=function(){t0=naNow();return oc()};
 mode='cpu';S.diff=lv;
 for(let g=0;g<games;g++){start();let n=0;
  while(!over&&n++<4000){if(busy||turn!==P){if(!busy&&t0){}await sl(20);continue}
   if(t0){R.turn.push(naNow()-t0);t0=0}
   const ms=moves(bd,P);if(!ms.length){await sl(20);continue}const m=ms[__tr()*ms.length|0];
   document.querySelectorAll('#board .sq')[m.r*8+m.c].click();await sl(30)}}
 brain=ob;cpuTurn=oc;if(po)po.disconnect();return R};
"""


def rate(r):
    n = r['w'] + r['l'] + r['t']
    return (r['w'] + r['t'] / 2) / n if n else 0


def target(a, b):
    if b == 'random':
        return .95
    return .75


def stats(ts):
    if not ts:
        return None
    ts = sorted(ts)
    return {'n': len(ts), 'mean_ms': round(sum(ts) / len(ts), 1), 'p95_ms': round(ts[int(.95 * (len(ts) - 1))], 1),
            'max_ms': round(ts[-1], 1)}


def table(game, f, fn, n, extra=''):
    res = {}
    for a, b in PAIRS:
        nn = n
        r = f.evaluate(f"__{fn}('{a}','{b}',{nn}{extra})")
        wr = rate(r); res[f'{a}-{b}'] = dict(r, rate=round(wr, 3))
        mark = 'ok' if wr >= target(a, b) else 'MISS'
        print(f"  {a:>6} vs {b:<6} {nn:4d} games  W/L/T {r['w']}/{r['l']}/{r['t']}  win {wr*100:5.1f}%"
              f"  (target {target(a, b)*100:.0f}%: {mark})  avg margin {r['margin']:+.1f}", flush=True)
    return res


def timing(f, label):
    t = f.evaluate("__times")
    out_ = {k: stats(v) for k, v in t.items()}
    for k in ['easy', 'normal', 'hard']:
        if out_.get(k):
            s = out_[k]
            print(f"  {label} {k:>6}: {s['n']} decisions, mean {s['mean_ms']} ms, 95% within {s['p95_ms']} ms, max {s['max_ms']} ms")
    return out_


def throttle(page, f, rate_):
    cdp = page.context.new_cdp_session(page)
    cdp.send('Emulation.setCPUThrottlingRate', {'rate': rate_})
    return cdp


def run_kb(page):
    n = N or 1000
    print(f'Knucklebones (3 columns, seed {SEED})', flush=True)
    f = open_game(page, 'kb'); f.evaluate(KB); f.evaluate(f"__seed({SEED})")
    RESULTS['kb'] = {'games': n, 'pairs': table('kb', f, 'kbMatch', n, ',3'), 'time': timing(f, 'desktop')}
    if SLOW:
        f.evaluate(f"__times={{}};__seed({SEED+1})"); cdp = throttle(page, f, 4)
        for lv in ['easy', 'normal', 'hard']:
            f.evaluate(f"__kbMatch('{lv}','random',6,3)")
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
        RESULTS['kb']['time_4x'] = timing(f, '4x slow')


def run_oth(page):
    n = N or 100
    print(f'Othello (seed {SEED})', flush=True)
    to_cover(page); f = open_game(page, 'oth'); f.evaluate(OTH); f.evaluate(f"__seed({SEED})")
    RESULTS['oth'] = {'games': n, 'pairs': table('oth', f, 'othMatch', n), 'time': timing(f, 'desktop')}
    if SLOW:
        f.evaluate(f"__times={{}};__seed({SEED+1})"); cdp = throttle(page, f, 4)
        for lv in ['easy', 'normal', 'hard']:
            f.evaluate(f"__othMatch('{lv}','random',2)")
        RESULTS['oth']['time_4x'] = timing(f, '4x slow')
        # real games through the page at 4x: the CPU thinks in its Worker; time each CPU turn (search, and
        # search + visible pause) and count main-thread tasks over 50 ms
        f.evaluate(OTH_LIVE); live = {}
        for lv in ['easy', 'normal', 'hard']:
            r = f.evaluate(f"__othLive('{lv}',1)")
            live[lv] = {'search': stats(r['search']), 'turn': stats(r['turn']), 'long_over_50ms': len(r['long']),
                        'long_max_ms': round(max(r['long']), 1) if r['long'] else 0}
            s1, s2 = live[lv]['search'], live[lv]['turn']
            print(f"  4x slow, real game {lv:>6}: {s1['n']} CPU turns, search 95% within {s1['p95_ms']} ms (max {s1['max_ms']}),"
                  f" whole turn {s2['mean_ms']} ms mean / {s2['max_ms']} max; main-thread tasks over 50 ms: {len(r['long'])}"
                  f"{' (longest ' + str(round(max(r['long']))) + ' ms)' if r['long'] else ''}", flush=True)
        RESULTS['oth']['live_4x'] = live
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})


# ---- Remi: a test-only build where seat 0 is a CPU too, every seat has its own level, and a seat can be played by the
# CPU from before the AI build (tests/fixtures/remi_cpu_base.js) as a yardstick
REMI_PATCH = [
    # every seat plays with its own level (set at the start of its turn; turns never overlap); "base" seats use the old CPU
    ("async function cpuTurn(tk){\n const p=G.cur", "async function cpuTurn(tk){if(window.__lv)lvl=__lv[G.cur];if(window.__old&&__old[G.cur])return base_cpuTurn(tk);\n const p=G.cur"),
    # seat 0 is played by the CPU code (no doubles swap screen for it either)
    ("if(G.cur===0){if(G.tn>3)fresh=[]", "if(G.cur===0&&!window.__bot0){if(G.tn>3)fresh=[]"),
    ("if(G.d3||(swp&&dblTiles(G.pl[0].hand).length))", "if(!window.__bot0&&(G.d3||(swp&&dblTiles(G.pl[0].hand).length)))"),
    ("window.__remi={", "window.__remi={dealRound,newGame,endRound,get lvl(){return lvl},"),
    # the tournament doesn't draw the table (same game, about 10x faster), and counts what is taken from the discards
    ("function render(){", "function render(){if(window.__norender)return;"),
    ("function takeRow(p,i){", "function takeRow(p,i){if(window.__tk)__tk.push([p,G.disc.length-i]);"),
]


def remi_copy():
    d = out('ai_remi'); os.makedirs(d, exist_ok=True)
    src = open(os.path.join(ROOT, 'games', 'Remi.html'), encoding='utf-8').read()
    for a, b in REMI_PATCH:
        if a not in src:
            sys.exit('ai_tournament: Remi changed, update REMI_PATCH: ' + a[:50])
        src = src.replace(a, b, 1)
    base = open(os.path.join(ROOT, 'tests', 'fixtures', 'remi_cpu_base.js'), encoding='utf-8').read()
    base = base.replace("G.disc.pop();P.hand.push(d);", "if(window.__tk)__tk.push([p,1]);G.disc.pop();P.hand.push(d);")
    mark = "// ---- game flow"
    if mark not in src:
        sys.exit('ai_tournament: Remi changed, no "' + mark + '" line to put the old CPU before')
    src = src.replace(mark, base + mark, 1)
    open(os.path.join(d, 'Remi.html'), 'w', encoding='utf-8').write(src)
    g = os.path.join(ROOT, 'games')
    subprocess.run([sys.executable, os.path.join(g, 'build.py')] + [os.path.join(g, x) for x in
                    ['Knucklebones.html', 'Othello.html', 'Water_Sort.html', 'Sudoku.html']] +
                   [os.path.join(d, 'Remi.html'), os.path.join(d, 'index.html')], check=True, capture_output=True)
    for x in ['sw.js', 'manifest.json', 'favicon.png', 'icon.png']:
        shutil.copy(os.path.join(ROOT, x), d)
    return d


# Round i of a pairing is always dealt from seed*100000+i, whoever sits where: both seatings (and every pairing) play
# the same deals, so the levels are compared on equal cards. Timers fire at once (the game's own waits, not its moves).
REMI_GO = RNG + r"""
const st=window.setTimeout,tq=[],mc=new MessageChannel();mc.port1.onmessage=()=>{const f=tq.shift();if(f)f()};
window.setTimeout=(fn,t,...a)=>{if(window.__slowT)return st(fn,Math.min(t||0,1),...a);tq.push(()=>fn(...a));mc.port2.postMessage(0);return 0};
window.__sleep=ms=>new Promise(r=>st(r,ms));
window.__bot0=true;__remi.spd=2;if(window.__ai)__ai.adapt=false;
window.__long=[];try{new PerformanceObserver(l=>l.getEntries().forEach(e=>__long.push(e.duration))).observe({type:'longtask',buffered:false})}catch(e){}
window.__remiRounds=async function(seats,old,n,seed){const R=__remi,rounds=[],closes=[0,0,0,0];let draws=0,stuck=0,turns=0;window.__lv=seats;window.__old=old;window.__tk=[];
 if(R.G.phase!=='over')R.endRound(-1,-1,'');   // the game opened with the page: stop its CPU turn before dealing again
 for(let i=0;i<n;i++){__seed(seed*100000+i);R.G.pl.forEach(P=>P.score=0);R.G.over=false;R.G.starter=i%4;R.dealRound();let w=0;
  while(R.G.phase!=='over'&&w++<60000){await __sleep(1);
   // nobody can ever close (every tile left fits nowhere and the pile keeps being reshuffled): counted, then ended like a pile that ran out
   if(R.G.tn>1200&&R.G.phase!=='over'){stuck++;R.endRound(-1,-1,'stuck')}}
  if(R.G.phase!=='over')throw new Error('Remi round did not finish');
  const r=R.G.res;turns+=R.G.tn;rounds.push(r.pen.slice());if(r.closer>=0)closes[r.closer]++;else draws++}
 return {rounds,closes,draws,stuck,turns,takes:__tk}};
"""
L = {'easy': 0, 'normal': 1, 'hard': 2}


def remi_pair(f, a, b, n):
    """a, b: 'normal' or 'base:normal'. Two of each at the table, both seatings on the same deals."""
    lv = lambda x: L[x.split(':')[-1]]
    old = lambda x: x.startswith('base:')
    half = max(1, n // 2); pts = {a: 0, b: 0}; cl = {a: 0, b: 0}; tk = {a: [], b: []}; draws = stuck = turns = 0; diff = [0.0] * half
    for seats in ([a, b, a, b], [b, a, b, a]):
        r = f.evaluate(f"__remiRounds({json.dumps([lv(x) for x in seats])},{json.dumps([old(x) for x in seats])},{half},{SEED})")
        for i, pen in enumerate(r['rounds']):
            for k, x in enumerate(seats):
                pts[x] += pen[k]; diff[i] += (pen[k] if x == a else -pen[k]) / 4
        for k, x in enumerate(seats):
            cl[x] += r['closes'][k]
        for p, depth in r['takes']:
            tk[seats[p]].append(depth)
        draws += r['draws']; stuck += r['stuck']; turns += r['turns']
    seat_rounds = 4 * half                                  # two seats per level, two seatings
    pa, pb = pts[a] / seat_rounds, pts[b] / seat_rounds
    m = sum(diff) / half; se = (sum((d - m) ** 2 for d in diff) / max(1, half - 1) / half) ** .5
    tks = lambda x: {'per_round': round(len(tk[x]) / seat_rounds, 2), 'deep': round(sum(1 for d in tk[x] if d > 1) / max(1, len(tk[x])), 2),
                     'avg_tiles': round(sum(tk[x]) / max(1, len(tk[x])), 1), 'most': max(tk[x] or [0])}
    res = {'rounds': 2 * half, a: {'pts_per_round': round(pa, 1), 'closes': cl[a], 'takes': tks(a)},
           b: {'pts_per_round': round(pb, 1), 'closes': cl[b], 'takes': tks(b)}, 'gap': round(m, 1), 'gap_se': round(se, 1), 'pile_ran_out': draws,
           'stuck': stuck, 'turns_per_round': round(turns / (2 * half), 1)}
    ta, tb = tks(a), tks(b)
    print(f"  {a:>11} vs {b:<11} {2 * half} rounds: points per round per CPU {pa:+.1f} / {pb:+.1f}, gap {m:+.1f} ± {se:.1f}"
          f" ({'ok' if m > 2 * se else 'ok?' if m > 0 else 'MISS'});  closes {cl[a]} / {cl[b]};"
          f"  takes per CPU per round {ta['per_round']} / {tb['per_round']} (2+ tiles {ta['deep']:.0%} / {tb['deep']:.0%}, avg {ta['avg_tiles']} / {tb['avg_tiles']}, most {ta['most']} / {tb['most']})"
          f"; {turns / (2 * half):.0f} turns a round, no close {draws}, stuck {stuck}", flush=True)
    return res


def run_remi(page_unused):
    n = N or 200
    mode = 'vs' if VS else 'base' if BASE else 'levels'
    pairs = {'levels': [('normal', 'easy'), ('hard', 'normal'), ('hard', 'easy')],
             'vs': [('easy', 'base:easy'), ('normal', 'base:normal'), ('hard', 'base:hard')],
             'base': [('base:normal', 'base:easy'), ('base:hard', 'base:normal'), ('base:hard', 'base:easy')]}[mode]
    print(f'Remi (4 CPUs, two kinds per table, seed {SEED}; "base" = the CPU from before the AI build; gap ± standard error)', flush=True)
    d = remi_copy(); port = start_server(8957, root=d)
    pw, b, page = open_page(port, 'iphone12')
    try:
        page.evaluate("localStorage.setItem('remi-rules-seen','1');localStorage.removeItem('remi_game2')")
        f = open_game(page, 'rem', 1200); f.evaluate(REMI_GO); f.evaluate(f"__seed({SEED})")
        f.evaluate("__remi.newGame()"); f.evaluate("window.__norender=true")
        res = {}
        for a, bb in pairs:
            res[f'{a}-{bb}'] = remi_pair(f, a, bb, n)
        RESULTS['remi'] = {'mode': mode, 'pairs': res}
        if SLOW:
            f.evaluate("window.__norender=false;window.__slowT=true;__long=[]"); cdp = throttle(page, f, 4)
            for lv in [0, 1, 2]:
                f.evaluate(f"__long=[];__remiRounds([{lv},{lv},{lv},{lv}],[false,false,false,false],3,{SEED + 7})")
                lg = f.evaluate("__long")
                RESULTS['remi'].setdefault('long_tasks_4x', {})[['easy', 'normal', 'hard'][lv]] = {
                    'over_50ms': len(lg), 'max_ms': round(max(lg), 1) if lg else 0}
                print(f"  4x slow, {['easy', 'normal', 'hard'][lv]}: {len(lg)} main-thread tasks over 50 ms in 3 rounds"
                      f", longest {round(max(lg)) if lg else 0} ms", flush=True)
            cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
            # every decision of a few rounds, asked again at 4x slow-down and timed on its own
            f.evaluate("window.__norender=true;window.__slowT=false")
            for lv in [0, 1, 2]:
                f.evaluate("__ai.log=[]"); f.evaluate(f"__remiRounds([{lv},{lv},{lv},{lv}],[false,false,false,false],12,{SEED + 9})")
                cdp = throttle(page, f, 4)
                ts = f.evaluate("(()=>{const L=__ai.log;__ai.log=null;return L.map(([k,s,v])=>{v=JSON.parse(v);const t=performance.now();__ai.pick({k,v,s});return [k,performance.now()-t]})})()")
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
                st = stats([t for k, t in ts]); st['over_50ms'] = sum(1 for k, t in ts if t > 50)
                st['slowest'] = max(ts, key=lambda x: x[1])[0]
                RESULTS['remi'].setdefault('time_4x', {})[['easy', 'normal', 'hard'][lv]] = st
                print(f"  4x slow, {['easy', 'normal', 'hard'][lv]}: {st['n']} decisions, mean {st['mean_ms']} ms, 95% within {st['p95_ms']} ms,"
                      f" max {st['max_ms']} ms ({st['slowest']}), over 50 ms: {st['over_50ms']}", flush=True)
        RESULTS['remi_errors'] = page.errors[:5]
        print('  console errors:', page.errors[:5])
    finally:
        b.close(); pw.stop()


if __name__ == '__main__':
    t0 = time.time()
    if WHICH in ('kb', 'oth', 'all'):
        port = start_server(8956); pw, b, page = open_page(port, 'iphone12')
        if WHICH in ('kb', 'all'):
            run_kb(page)
        if WHICH in ('oth', 'all'):
            run_oth(page)
        RESULTS['errors'] = page.errors[:5]
        print('console errors:', page.errors[:5]); b.close(); pw.stop()
    if WHICH in ('remi', 'all'):
        run_remi(None)
    RESULTS['seconds'] = round(time.time() - t0)
    json.dump(RESULTS, open(out('ai_tournament.json'), 'w'), indent=1)
    print(f'done in {RESULTS["seconds"]} s; numbers in tests/out/ai_tournament.json')
