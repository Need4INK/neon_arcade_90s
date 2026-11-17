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
    python3 tests/ai_tournament.py remi 2000 --styles  # the three personalities: each against the plain level, then
                                                     # the game's table (who wins the matches, how each one plays)
    python3 tests/ai_tournament.py remi 2000 --person  # playing like a person (blueprint 3a): what the habits cost,
                                                     # how often each shows, score play in matches, the pauses
In the game seat 0 is you, and CPU 1 / 2 / 3 play Cautious / Bold / Sly; here seat 0 is a CPU of the plain level
(no style). Target (blueprint 6b): each style wins a third of the three styles' matches, give or take 5 points.
The styles' tables are played as matches (scores run on to the target, as in the game), because the CPUs play the
score; the level pairings start every round at 0 : 0.

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
STYLES = '--styles' in argv  # Remi: the three personalities (same strength, different play)
PERSON = '--person' in argv  # Remi: playing like a person (misses, memory, pauses, score play, fishing, holding back)
IMAGINE = '--imagine' in argv  # Remi: Hard's timing and imagined hands (step 5), each part on and off
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
    ("window.__remi={", "window.__remi={dealRound,newGame,endRound,get lvl(){return lvl},set limit(v){LIMIT=v},"),
    # the tournament doesn't draw the table (same game, about 10x faster), and counts what is taken from the discards
    ("function render(){", "function render(){if(window.__norender)return;"),
    ("function takeRow(p,i){", "function takeRow(p,i){if(window.__tk)__tk.push([p,G.disc.length-i]);"),
    # every seat can play in any style (0 = none, 1 Cautious, 2 Bold, 3 Sly); in the game seat p plays style p
    ("S0=RSTY[p]||{}", "S0=RSTY[window.__sty?__sty[p]:p]||{}"),
    # what the styles look like: when each seat opens, and who goes for the board game
    ("const was=P.opened;P.opened=true;", "const was=P.opened;P.opened=true;if(window.__op&&!was)__op.push([p,myTurnNo(p),pts]);"),
    ("if(d.board&&canBoard(p)){P.board=true;", "if(d.board&&canBoard(p)){P.board=true;if(window.__bd)__bd.push(p);"),
    # how long each pause is, as a share of the speed setting's step
    ("(s>>>8&1023)/1024)));return o}", "(s>>>8&1023)/1024)));if(window.__pw)__pw.push([k,PW,q.w]);return o}"),
    # a seat can play with some knobs set by the test (to compare one habit on and off on the same deals)
    ("Math.max(0,K[k]+S[k]);return K}", "Math.max(0,K[k]+S[k]);if(window.__kn&&__kn[p])Object.assign(K,__kn[p]);return K}"),
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
window.setTimeout=(fn,t,...a)=>{if(window.__realT)return st(fn,t,...a);if(window.__slowT)return st(fn,Math.min(t||0,1),...a);tq.push(()=>fn(...a));mc.port2.postMessage(0);return 0};
window.__sleep=ms=>new Promise(r=>st(r,ms));
window.__bot0=true;__remi.spd=2;if(window.__ai){__ai.adapt=false;__ai.main=true}   // main: Hard's imagined hands are worked out in the page, not in its Worker (timers are faked here)
window.__long=[];try{new PerformanceObserver(l=>l.getEntries().forEach(e=>__long.push(e.duration))).observe({type:'longtask',buffered:false})}catch(e){}
window.__remiRounds=async function(seats,old,n,seed,sty,opt){const R=__remi,rounds=[],closes=[0,0,0,0],x2=[0,0,0,0],shut=[0,0,0,0],wins=[0,0,0,0],M=opt&&opt.match;let draws=0,stuck=0,turns=0;window.__lv=seats;window.__old=old;window.__tk=[];window.__sty=sty;window.__op=[];window.__bd=[];window.__kn=opt&&opt.kn||null;
 if(R.G.phase!=='over')R.endRound(-1,-1,'');   // the game opened with the page: stop its CPU turn before dealing again
 for(let i=0;i<n;i++){__seed(seed*100000+i);if(!M||!i||R.G.over)R.G.pl.forEach(P=>P.score=0);R.G.over=false;R.G.starter=i%4;R.G.round=i;R.dealRound();let w=0;
  while(R.G.phase!=='over'&&w++<60000){await __sleep(1);
   // nobody can ever close (every tile left fits nowhere and the pile keeps being reshuffled): counted, then ended like a pile that ran out
   if(R.G.tn>1200&&R.G.phase!=='over'){stuck++;R.endRound(-1,-1,'stuck')}}
  if(R.G.phase!=='over')throw new Error('Remi round did not finish');
  const r=R.G.res;turns+=R.G.tn;rounds.push(r.pen.slice());if(r.closer>=0){closes[r.closer]++;if(r.x)x2[r.closer]++;R.G.pl.forEach((P,q)=>{if(!P.opened&&q!==r.closer)shut[q]++})}else draws++;
  if(M&&R.G.over)wins[R.G.pl.reduce((b,P,q)=>P.score>R.G.pl[b].score?q:b,0)]++}
 return {rounds,closes,x2,shut,draws,stuck,turns,takes:__tk,opens:__op,boards:__bd,wins}};
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


STYLE = ['plain', 'Cautious', 'Bold', 'Sly']


def remi_table(f, lv, n, perms, label, limit=1000):
    """One level, a style per seat, played as matches to `limit`. perms: seatings (style of seats 0-3) that all play the same deals."""
    m = max(1, n // len(perms)); rounds = []; w = {}; st = {k: dict(pts=0, n=0, cl=0, x2=0, shut=0, tk=0, tiles=0, op=0, opn=0, opp=0, bd=0) for k in range(4)}
    f.evaluate(f"__remi.limit={limit}")
    for sty in perms:
        r = f.evaluate(f"__remiRounds({[lv] * 4},[false,false,false,false],{m},{SEED},{json.dumps(sty)},{{match:1}})")
        rounds += r['rounds']
        for q in range(4):
            w[sty[q]] = w.get(sty[q], 0) + r['wins'][q]
        for pen in r['rounds']:
            for q in range(4):
                st[sty[q]]['pts'] += pen[q]; st[sty[q]]['n'] += 1
        for q in range(4):
            a = st[sty[q]]; a['cl'] += r['closes'][q]; a['x2'] += r['x2'][q]; a['shut'] += r['shut'][q]
        for q, depth in r['takes']:
            st[sty[q]]['tk'] += 1; st[sty[q]]['tiles'] += depth
        for q, turn, pts in r['opens']:
            a = st[sty[q]]; a['op'] += turn; a['opn'] += 1; a['opp'] += pts
        for q in r['boards']:
            st[sty[q]]['bd'] += 1
    f.evaluate("__remi.limit=1000")
    res = {'rounds': len(rounds), 'limit': limit, 'styles': {}}
    print(f"  {label}, {len(rounds)} rounds, matches to {limit}:", flush=True)
    for k in range(4):
        a = st[k]
        if not a['n']:
            continue
        d = dict(pts_per_round=round(a['pts'] / a['n'], 1), closes=round(a['cl'] / a['n'], 3), closes_x2=round(a['x2'] / max(1, a['cl']), 3),
                 not_opened=round(a['shut'] / a['n'], 3), takes=round(a['tk'] / a['n'], 2), tiles_per_take=round(a['tiles'] / max(1, a['tk']), 1),
                 opens_turn=round(a['op'] / max(1, a['opn']), 2), opens_with=round(a['opp'] / max(1, a['opn'])), boards=a['bd'])
        res['styles'][STYLE[k]] = d
        print(f"    {STYLE[k]:>8}: {d['pts_per_round']:+6.1f} points a round · closes {d['closes']:.1%} (with a 1 or joly {d['closes_x2']:.0%})"
              f" · not opened {d['not_opened']:.1%} · takes {d['takes']} a round ({d['tiles_per_take']} tiles) · opens in turn {d['opens_turn']}"
              f" with {d['opens_with']} · board games {d['boards']}", flush=True)
    nm = sum(w.values()); three = sum(w.get(k, 0) for k in (1, 2, 3)) or 1
    sh = {STYLE[k]: round(w.get(k, 0) / three, 3) for k in (1, 2, 3)}
    ok = all(abs(v - 1 / 3) <= .05 for v in sh.values())
    res['wins'] = {'matches': nm, 'plain': round(w.get(0, 0) / max(1, nm), 3), 'share': sh, 'ok': ok}
    print(f"    {nm:5d} matches · share of the three styles' wins: " + ' · '.join(f"{k} {v:.1%}" for k, v in sh.items())
          + f" ({'ok' if ok else 'MISS'}: each within 5 points of a third) · the plain seat wins {w.get(0, 0) / max(1, nm):.1%}", flush=True)
    return res


def run_styles(f, n):
    """The three personalities (blueprint 6b): same strength, different play. Per level: each style against the plain
    level (two seats each, same deals), then the game's own table (plain in your seat, CPU 1-3 in their styles) and the
    styles moved round the three CPU seats."""
    out_ = {}
    for name in ['easy', 'normal', 'hard']:
        lv = L[name]; print(f' {name}', flush=True); o = out_[name] = {'vs_plain': {}}
        for k in (1, 2, 3):
            half = max(1, n // 2); pts = [0, 0]; diff = [0.0] * half
            for sty in ([k, 0, k, 0], [0, k, 0, k]):
                r = f.evaluate(f"__remiRounds({[lv] * 4},[false,false,false,false],{half},{SEED},{sty})")
                for i, pen in enumerate(r['rounds']):
                    for q in range(4):
                        pts[sty[q] == 0] += pen[q]; diff[i] += (pen[q] if sty[q] else -pen[q]) / 4
            m = sum(diff) / half; se = (sum((d - m) ** 2 for d in diff) / max(1, half - 1) / half) ** .5
            o['vs_plain'][STYLE[k]] = {'pts': round(pts[0] / half / 4, 1), 'plain': round(pts[1] / half / 4, 1), 'gap': round(m, 1), 'gap_se': round(se, 1)}
            print(f"  {STYLE[k]:>8} vs plain {2 * half} rounds: {pts[0] / half / 4:+.1f} / {pts[1] / half / 4:+.1f} points a round, gap {m:+.1f} ± {se:.1f}", flush=True)
        o['game'] = remi_table(f, lv, 3 * n, [[0, 1, 2, 3]], "the game's table (you = plain, CPU 1 Cautious, CPU 2 Bold, CPU 3 Sly)")
        o['moved'] = remi_table(f, lv, 3 * n, [[0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 1, 3, 2], [0, 3, 2, 1], [0, 2, 1, 3]], 'styles moved round the CPU seats')
        o['game_500'] = remi_table(f, lv, 3 * n // 2, [[0, 1, 2, 3]], "the game's table", 500)
    return out_


# ---- playing like a person (blueprint 3a). Every habit has a knob that is off at 0, so a seat can play without it.
HABITS = {'memory': ['span', 'fade', 'fog'], 'misses': ['slip'], 'reading': ['read', 'shut'], 'fishing': ['fish'], 'small opening': ['sand'], 'score': ['score']}


def habits_off(name, keys=None):
    """knobs that switch habits off for a seat of that level (all of them: the CPU as it was before step 4b)"""
    keys = keys or [k for g in HABITS.values() for k in g] + ['tempo']
    return {k: (1 if name == 'hard' else 0) if k == 'read' else 0 for k in keys}


def remi_ab(f, name, on, off, n, label, match=False):
    """One level at the game's table (seat p plays style p). Seats 0 and 2 play with knobs `on`, 1 and 3 with `off`
    (None = as built), then the other way round on the same deals: points a round on minus off, and matches won."""
    half = max(1, n // 2); diff = [0.0] * half; wins = [0, 0]
    for flip in (0, 1):
        kn = [off, on, off, on] if flip else [on, off, on, off]
        r = f.evaluate(f"__remiRounds({[L[name]] * 4},[false,false,false,false],{half},{SEED},null,{json.dumps({'kn': kn, 'match': match})})")
        for i, pen in enumerate(r['rounds']):
            for q in range(4):
                diff[i] += (pen[q] if (q % 2 == 0) != bool(flip) else -pen[q]) / 4
        for q in range(4):
            wins[(q % 2 == 0) == bool(flip)] += r['wins'][q]
    m = sum(diff) / half; se = (sum((d - m) ** 2 for d in diff) / max(1, half - 1) / half) ** .5
    res = {'rounds': 2 * half, 'gap': round(m, 1), 'gap_se': round(se, 1)}
    txt = f"  {name:>6} · {label:<28} {2 * half} rounds: {m:+.1f} ± {se:.1f} points a round"
    if match:
        res['matches'] = sum(wins); res['won'] = round(wins[0] / max(1, sum(wins)), 3)
        txt += f" · wins {wins[0]} of {sum(wins)} matches ({wins[0] / max(1, sum(wins)):.1%}; even = 50%)"
    print(txt, flush=True)
    return res


# Every decision of some rounds, asked again with one habit off: where the answer differs, the habit was at work
PERSON_JS = r"""(()=>{const B=__remi.brain,o={disc:0,fitThrown:0,fish:0,opens:0,small:0,adds:0,addMiss:0,swapMiss:0,takes:0,takeMiss:0,row:0,rowGone:0,score:0,rush:0,pace:{}};
 const pick=(k,v,s,kn)=>JSON.stringify(__ai.pick({k,v:Object.assign({},v,{K:Object.assign({},v.K,kn)}),s}));
 for(const [k,s,vj,oj] of __ai.log){const v=JSON.parse(vj),me=v.pl[v.p];
  if(k==='disc'){o.disc++;if(me.opened&&v.hand.length>1&&!me.board&&B.fitsTable(v.melds,JSON.parse(oj),v.p)>=0)o.fitThrown++;
   if(v.K.fish>0&&v.K.pool<2&&pick(k,v,s,{fish:0})!==oj)o.fish++;
   const nd=v.disc.length;v.disc.forEach((x,i)=>{const a=nd-1-i;o.row++;if(B.rbH(v.z,v.p,x)<Math.min(.6,Math.max(0,a-v.K.span)*v.K.fade)||(a>=v.K.span&&!v.K.mem))o.rowGone++});
   const m=B.rbMood(v);if(m!==v){o.score++;if(Math.max(...v.sc)>=v.lim-200&&v.K.score>.5)o.rush++}}
  if(k==='lay'&&!me.opened&&JSON.parse(oj).length){o.opens++;if(v.K.sand>0&&pick(k,v,s,{sand:0})!==oj)o.small++}
  if(k==='extras'){const a=JSON.parse(oj),b=JSON.parse(pick(k,v,s,{slip:0}));if(b.length){o.adds++;if(b.length>a.length)o.addMiss++;if(b.some(x=>x.a==='swap')&&!a.some(x=>x.a==='swap'))o.swapMiss++}}
  if(k==='start'&&me.opened&&v.hand.length>=3&&!me.board&&pick(k,v,s,{blind:0,temp:0}).includes('take')){o.takes++;if(!oj.includes('take'))o.takeMiss++}}
 for(const [k,w] of __pw)(o.pace[k]||(o.pace[k]=[])).push(w);
 for(const k in o.pace){const a=o.pace[k].sort((x,y)=>x-y),q=p=>+a[Math.floor(p*(a.length-1))].toFixed(2);o.pace[k]={n:a.length,min:q(0),p10:q(.1),mid:q(.5),p90:q(.9),max:q(1)}}
 return o})()"""


def run_person(f, n):
    """Playing like a person (blueprint 3a). Per level: the CPU as built against itself without the new habits (what
    they cost), each habit on its own, score play in matches, then how often each habit shows and how long the pauses are."""
    out_ = {}
    for name in ['easy', 'normal', 'hard']:
        o = out_[name] = {}
        o['all'] = remi_ab(f, name, None, habits_off(name), n, 'all habits, against none')
        for g, keys in HABITS.items():
            if g != 'score':
                o[g] = remi_ab(f, name, None, habits_off(name, keys), n, g + ', against without')
        o['score'] = remi_ab(f, name, None, {'score': 0}, 3 * n, 'playing the score, matches', True)
        f.evaluate("__ai.log=[];window.__pw=[]")
        f.evaluate(f"__remiRounds({[L[name]] * 4},[false,false,false,false],{min(300, n)},{SEED + 3},null,{{match:1}})")
        h = o['shows'] = f.evaluate(PERSON_JS); f.evaluate("__ai.log=null;window.__pw=null")
        p = lambda a, c: f"{a} of {c} ({a / max(1, c):.1%})"
        print(f"  {name:>6} · in {min(300, n)} rounds of match play: threw a tile that fits the table {p(h['fitThrown'], h['disc'])} discards · an add overlooked in"
              f" {p(h['addMiss'], h['adds'])} turns with one (a joly swap: {h['swapMiss']}) · takes overlooked {p(h['takeMiss'], h['takes'])}"
              f" · discards in the row it no longer knows {h['rowGone'] / max(1, h['row']):.1%} · fishing discards {p(h['fish'], h['disc'])}"
              f" · small openings {p(h['small'], h['opens'])} · discards with the score in mind {p(h['score'], h['disc'])} (closing fast: {h['rush']})", flush=True)
        print(f"  {name:>6} · pauses, as a share of the speed step (lowest, 10%, middle, 90%, highest): "
              + ' · '.join(f"{k} {v['min']} {v['p10']} {v['mid']} {v['p90']} {v['max']}" for k, v in h['pace'].items()), flush=True)
    return out_


# ---- Hard's timing and imagined hands (blueprint 5, Remi step 3 and "How Hard thinks"). Every part has a knob that is
# off at 0; step4b(seat) switches all of them off for a seat (and puts back what a style had at Hard then), which gives
# the Hard CPU of step 4b: checked on 900 rounds against the build of step 4b, same scores to the point.
def step4b(seat):
    return {'img': 0, 'bev': 0, 'atu': 0, 'cheap': 0, 'fin': 1 if seat == 3 else 0, **STEP4B_STYLE.get(seat, {})}


STEP4B_STYLE = {1: {'draw': 23}}   # Cautious asked more of a take at Hard then (the level's 3 + 20)
SPEEDS = ['Slow', 'Normal', 'Fast']


def remi_seats(f, on, off, n, label, match=False):
    """Hard at the game's table. on(seat) / off(seat): the knobs a seat plays with (None = as built). Seats 0 and 2 play
    `on`, 1 and 3 `off`, then the other way round on the same deals."""
    half = max(1, n // 2); diff = [0.0] * half; wins = [0, 0]
    for flip in (0, 1):
        kn = [(on if (q % 2 == 0) != bool(flip) else off)(q) for q in range(4)]
        r = f.evaluate(f"__remiRounds([2,2,2,2],[false,false,false,false],{half},{SEED},null,{json.dumps({'kn': kn, 'match': match})})")
        for i, pen in enumerate(r['rounds']):
            for q in range(4):
                diff[i] += (pen[q] if (q % 2 == 0) != bool(flip) else -pen[q]) / 4
        for q in range(4):
            wins[(q % 2 == 0) == bool(flip)] += r['wins'][q]
    m = sum(diff) / half; se = (sum((d - m) ** 2 for d in diff) / max(1, half - 1) / half) ** .5
    res = {'rounds': 2 * half, 'gap': round(m, 1), 'gap_se': round(se, 1)}
    txt = f"  hard · {label:<44} {2 * half} rounds: {m:+.1f} ± {se:.1f} points a round"
    if match:
        res['matches'] = sum(wins); res['won'] = round(wins[0] / max(1, sum(wins)), 3)
        txt += f" · wins {wins[0]} of {sum(wins)} matches ({wins[0] / max(1, sum(wins)):.1%}; even = 50%)"
    print(txt, flush=True)
    return res


# Every Hard decision of some rounds, asked again without imagining: where the answer differs, the imagined hands decided
IMAGINE_JS = r"""(()=>{const o={disc:0,dImg:0,dCh:0,start:0,sImg:0,sCh:0,tables:0,plays:0,board:0};
 for(const [k,s,vj,oj] of __ai.log){const v=JSON.parse(vj);if(k!=='disc'&&k!=='start')continue;
  const q=v.q={w:1},a=JSON.stringify(__ai.pick({k,v,s})),im=q.im;if(k==='start'&&oj.includes('board'))o.board++;
  if(k==='disc'){if(v.hand.length>1)o.disc++}else if(v.pl[v.p].opened&&v.hand.length>=3)o.start++;
  if(!im)continue;o.tables+=im.n;o.plays+=im.ro;k==='disc'?o.dImg++:o.sImg++;if(im.b)k==='disc'?o.dCh++:o.sCh++}
 return o})()"""


def run_imagine(f, n):
    o = {}; none = lambda q: None; off = lambda **kw: (lambda q: kw)
    o['all'] = remi_seats(f, none, step4b, n, 'all of step 5, against Hard of step 4b')
    for k, sp in enumerate(SPEEDS):
        f.evaluate(f"__remi.spd={k}")
        o['imagine_' + sp] = remi_seats(f, none, off(img=0), n if k == 2 else n // 2, f'imagined hands at {sp} speed, against without')
    o['discards'] = remi_seats(f, off(ims=0), off(img=0), n, 'imagining the discard only, against without')
    o['takes'] = remi_seats(f, none, off(ims=0), n, 'imagining take or draw too, against without')
    o['fin'] = remi_seats(f, none, lambda q: {'fin': 1 if q == 3 else 0}, n, 'closing with a 1 or joly (all), against Sly only')
    o['cheap'] = remi_seats(f, none, off(cheap=0), n, 'holding on to costly tiles, against not')
    o['board'] = remi_seats(f, none, off(bev=0), n, 'board game by expected points, against 5 doubles')
    o['atu'] = remi_seats(f, none, off(atu=0), 2 * n, 'weighing the atu, matches', True)
    f.evaluate("__ai.log=[]"); f.evaluate(f"__remiRounds([2,2,2,2],[false,false,false,false],{min(200, n)},{SEED + 3},null,{{match:1}})")
    h = o['shows'] = f.evaluate(IMAGINE_JS); f.evaluate("__ai.log=null")
    p = lambda a, c: f"{a} of {c} ({a / max(1, c):.1%})"
    print(f"  hard · in {min(200, n)} rounds at Fast speed: discards weighed on imagined tables {p(h['dImg'], h['disc'])}, changed by them {p(h['dCh'], h['disc'])}"
          f" · take-or-draw weighed {p(h['sImg'], h['start'])}, changed {p(h['sCh'], h['start'])}"
          f" · {h['tables'] / max(1, h['dImg'] + h['sImg']):.0f} tables and {h['plays'] / max(1, h['dImg'] + h['sImg']):.0f} play-outs a choice · board games {h['board']}", flush=True)
    return o


# Hard at the real pace through the page: the CPUs' own pauses, the Worker, the table drawn
REMI_PACE = r"""window.__pace=async function(lv,spd,rounds,seed){const R=__remi,w=__sleep;window.__realT=true;window.__norender=false;__ai.main=false;__ai.tm=[];
 window.__lv=[lv,lv,lv,lv];window.__old=[false,false,false,false];window.__kn=null;window.__sty=null;R.spd=spd;let turns=0;const t0=performance.now();__long.length=0;
 for(let i=0;i<rounds;i++){if(R.G.phase!=='over')R.endRound(-1,-1,'');__seed(seed*100000+i);R.G.pl.forEach(P=>P.score=0);R.G.over=false;R.G.starter=i%4;R.G.round=i;R.dealRound();
  while(R.G.phase!=='over'&&performance.now()-t0<600000)await w(100);turns+=R.G.tn}
 const o={tm:__ai.tm,long:__long.slice(),turns,ms:performance.now()-t0};__ai.tm=null;__ai.main=true;window.__realT=false;window.__norender=true;R.spd=2;return o}"""


def remi_slow(page, f):
    """Speed at 4x CPU slow-down (blueprint 7). Easy / Normal: main-thread tasks over 50 ms in drawn rounds. Hard: whole
    rounds at the real pace at each speed, its imagined choices worked out in the Worker: how long an answer takes
    against the pause that move has anyway. Then every decision timed on its own on the main thread (CDP's slow-down
    doesn't reach a Worker, so this is the honest 4x number for the thinking itself, and what a page without a
    Worker would do)."""
    res = RESULTS['remi']; names = ['easy', 'normal', 'hard']
    f.evaluate("window.__norender=false;window.__slowT=true;__long=[]"); cdp = throttle(page, f, 4)
    for lv in [0, 1]:
        f.evaluate(f"__long=[];__remiRounds([{lv},{lv},{lv},{lv}],[false,false,false,false],3,{SEED + 7})")
        lg = f.evaluate("__long")
        res.setdefault('long_tasks_4x', {})[names[lv]] = {'over_50ms': len(lg), 'max_ms': round(max(lg), 1) if lg else 0}
        print(f"  4x slow, {names[lv]}: {len(lg)} main-thread tasks over 50 ms in 3 rounds, longest {round(max(lg)) if lg else 0} ms", flush=True)
    f.evaluate("window.__slowT=false"); f.evaluate(REMI_PACE)
    q = lambda a, p: sorted(a)[min(len(a) - 1, int(p * len(a)))] if a else 0
    for spd, rounds in ((0, 2), (1, 2), (2, 4)):
        r = f.evaluate(f"__pace(2,{spd},{rounds},{SEED + 7})")
        im = [x for x in r['tm'] if x[3]]; pt = [x[1] for x in im] or [0]; pa = [x[2] for x in im] or [0]
        d = res.setdefault('pace_4x', {})[SPEEDS[spd]] = {
            'rounds': rounds, 'turns': r['turns'], 's_per_turn': round(r['ms'] / 1000 / max(1, r['turns']), 2), 'imagined': len(im),
            'answer_ms': {'mean': round(sum(pt) / len(pt)), 'p95': round(q(pt, .95)), 'max': round(max(pt))},
            'pause_ms': {'mean': round(sum(pa) / len(pa)), 'min': round(min(pa))}, 'later_than_pause': sum(1 for x in im if x[1] > x[2]),
            'no_answer_in_time': sum(x[4] for x in r['tm']), 'tables': round(sum(x[3][0] for x in im) / max(1, len(im))),
            'long_tasks': len(r['long']), 'long_max_ms': round(max(r['long'] or [0]))}
        print(f"  4x slow, hard at {SPEEDS[spd]} speed, real pace, Worker: {r['turns']} turns, {d['s_per_turn']} s a turn · {len(im)} imagined choices"
              f" ({d['tables']} tables each): answer after {d['answer_ms']['mean']} ms, 95% within {d['answer_ms']['p95']}, longest {d['answer_ms']['max']}"
              f" · their pauses {d['pause_ms']['mean']} ms, shortest {d['pause_ms']['min']} · answers later than the pause: {d['later_than_pause']}"
              f" · no answer in time: {d['no_answer_in_time']} · main-thread tasks over 50 ms: {d['long_tasks']}"
              + (f" (longest {d['long_max_ms']} ms)" if d['long_tasks'] else ''), flush=True)
    cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
    # every decision of a few rounds, asked again at 4x slow-down and timed on its own (Hard: at each speed's number of tables)
    f.evaluate("window.__norender=true")
    for lv in [0, 1, 2]:
        f.evaluate("__ai.log=[]"); f.evaluate(f"__remiRounds([{lv},{lv},{lv},{lv}],[false,false,false,false],12,{SEED + 9})")
        for spd in ([0, 1, 2] if lv == 2 else [2]):
            cdp = throttle(page, f, 4)
            ts = f.evaluate("sp=>__ai.log.map(([k,s,v])=>{v=JSON.parse(v);v.sp=sp;const q=v.q={w:1},t=performance.now();__ai.pick({k,v,s});return [k,performance.now()-t,q.im?1:0]})", spd)
            cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
            st = stats([t for k, t, i in ts]); st['over_50ms'] = sum(1 for k, t, i in ts if t > 50)
            st['slowest'] = max(ts, key=lambda x: x[1])[0]
            key = names[lv] + ('' if lv < 2 else '_' + SPEEDS[spd])
            txt = f"  4x slow, {names[lv]}: {st['n']} decisions, mean {st['mean_ms']} ms, 95% within {st['p95_ms']} ms, max {st['max_ms']} ms ({st['slowest']}), over 50 ms: {st['over_50ms']}"
            if lv == 2:
                im = [t for k, t, i in ts if i]; rest = [t for k, t, i in ts if not i]; floor = [1000, 600, 250][spd] * .748
                st.update(imagined=stats(im), imagined_over_pause=sum(1 for t in im if t > floor), pause_floor_ms=round(floor),
                          other_max_ms=round(max(rest), 1), other_over_50ms=sum(1 for t in rest if t > 50))
                txt = (f"  4x slow, hard at {SPEEDS[spd]} speed, on the main thread: {len(im)} imagined choices mean {st['imagined']['mean_ms']} ms, 95% within"
                       f" {st['imagined']['p95_ms']} ms, max {st['imagined']['max_ms']} ms; shortest pause they can have {round(floor)} ms, longer than that: {st['imagined_over_pause']}"
                       f" · the other {len(rest)} decisions: max {st['other_max_ms']} ms, over 50 ms: {st['other_over_50ms']}")
            res.setdefault('time_4x', {})[key] = st
            print(txt, flush=True)
    f.evaluate("__ai.log=null")


def run_remi(page_unused):
    n = N or 200
    mode = 'styles' if STYLES else 'person' if PERSON else 'imagine' if IMAGINE else 'vs' if VS else 'base' if BASE else 'levels'
    pairs = {'levels': [('normal', 'easy'), ('hard', 'normal'), ('hard', 'easy')],
             'vs': [('easy', 'base:easy'), ('normal', 'base:normal'), ('hard', 'base:hard')],
             'base': [('base:normal', 'base:easy'), ('base:hard', 'base:normal'), ('base:hard', 'base:easy')], 'styles': [], 'person': [], 'imagine': []}[mode]
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
        if STYLES:
            RESULTS['remi']['styles'] = run_styles(f, n)
        if PERSON:
            RESULTS['remi']['person'] = run_person(f, n)
        if IMAGINE:
            RESULTS['remi']['imagine'] = run_imagine(f, n)
        if SLOW:
            remi_slow(page, f)
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
