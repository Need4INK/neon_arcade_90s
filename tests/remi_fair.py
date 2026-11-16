"""Remi fairness check: the CPUs decide from public information plus their own hand, and from nothing else.

    python3 tests/remi_fair.py        # 6 rounds per CPU level
    python3 tests/remi_fair.py 20     # 20 rounds per level

Every CPU decision in the game is `think(p, kind)`: it builds a "view" for player p (viewOf) and hands it to a plain
function (rbStart / rbLay / rbExtras / rbDisc). This plays whole rounds with four CPUs (the tournament's test-only copy
of the game) and checks every single decision four ways:

1. Nothing hidden in the view. Every tile in it is in that CPU's own hand, on the table, or was seen by the whole
   table: it lay in the discard row at some point this round, or it is the atu's twin (announced at the deal). The
   pile and the other hands appear only as counts.
2. Hidden tiles don't matter. The pile and the other players' unseen tiles are shuffled among themselves; the view
   built afterwards must be identical and the decision, asked again while the tiles are shuffled, must be the same.
3. Empty room. The decision functions (and the rule helpers they use, `__remi.brain`) are copied into an empty page
   with no game in it: no G, no table, no saved data, and Math.random switched off. Fed only the recorded views and
   seeds, they must give the same answers as in the game.
4. The source of those functions never names the game state (G, T), the page or Math.random.
It also shows that check 1 would notice a leak, by planting a pile tile in a view. Ends with exit code 1 on any failure.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
_argv, sys.argv = sys.argv, sys.argv[:1]
import ai_tournament as T
sys.argv = _argv
from harness import start_server, open_page, open_game

# Runs inside the game at every decision, right after the brain answered (the game state hasn't moved yet)
AUDIT = r"""
window.__fair={n:0,leak:[],diff:[],log:[],seen:new Set(),round:-1,keep:1};
window.tw=id=>id>=104?209-id:id<52?id+52:id-52;const rnd=__mk(99);
function idsOf(v){const a=[...v.hand,...v.disc,...v.melds.flatMap(m=>m.t),...Object.keys(v.h).map(Number),...v.no.flat()];if(v.must>=0)a.push(v.must);return a}
window.__leaks=function(v,G){const p=v.p,ok=new Set([...G.pl[p].hand,...G.melds.flatMap(m=>m.t),...__fair.seen,tw(G.atu)]),bad=idsOf(v).filter(id=>!ok.has(id));
 if(typeof v.pile!=='number'||v.pl.some(q=>Object.keys(q).join()!=='n,opened,board'))bad.push('shape');return bad};
__ai.log={push(e){const [k,s,vj,oj]=e,v=JSON.parse(vj),G=__remi.G,F=__fair,p=v.p;
 if(F.round!==G.round){F.round=G.round;F.seen=new Set()}G.disc.forEach(id=>F.seen.add(id));F.n++;
 const bad=__leaks(v,G);if(bad.length)F.leak.push([k,p,bad]);
 // shuffle everything p can't know: the pile and the other hands, except tiles the table saw them take
 const known=id=>G.mem.h[id]!=null&&G.own[id]<0,spots=[G.pile,...G.pl.filter((P,q)=>q!==p).map(P=>P.hand)],bk=spots.map(a=>a.slice()),pool=[];
 spots.forEach(a=>a.forEach(id=>{if(!known(id))pool.push(id)}));for(let i=pool.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]]}
 let c=0;spots.forEach(a=>a.forEach((id,i)=>{if(!known(id))a[i]=pool[c++]}));
 const taking=v.must>=0&&k==='lay',v2=__remi.viewOf(p,taking?{hand:v.hand,disc:v.disc,must:v.must}:{start:v.start});
 if(JSON.stringify(v2)!==vj)F.diff.push([k,p,'view changed']);
 else if(JSON.stringify(__ai.pick({k,v:v2,s}))!==oj)F.diff.push([k,p,'answer changed']);
 spots.forEach((a,i)=>{a.length=0;a.push(...bk[i])});
 if(F.keep)F.log.push([k,s,vj,oj])}};
"""

port = start_server(8958, root=T.remi_copy())
pw, b, page = open_page(port, 'iphone12')
page.evaluate("localStorage.setItem('remi-rules-seen','1');localStorage.removeItem('remi_game2')")
f = open_game(page, 'rem', 1200); f.evaluate(T.REMI_GO); f.evaluate("__seed(5)"); f.evaluate("__remi.newGame()")
f.evaluate("window.__norender=true"); f.evaluate(AUDIT)
fails = 0; logs = []; kinds = {}
for lv, name in enumerate(['Easy', 'Normal', 'Hard']):
    f.evaluate(f"__remiRounds([{lv},{lv},{lv},{lv}],[false,false,false,false],{ROUNDS},{50 + lv})")
    r = f.evaluate("(()=>{const F=__fair,o={n:F.n,leak:F.leak.slice(0,3),nl:F.leak.length,diff:F.diff.slice(0,3),nd:F.diff.length,log:F.log};F.n=0;F.leak=[];F.diff=[];F.log=[];return o})()")
    logs += r['log']; fails += r['nl'] + r['nd']
    takes = sum(1 for e in r['log'] if e[0] == 'start' and 'take' in e[3])
    print(f"{name}: {ROUNDS} rounds, {r['n']} decisions ({takes} takes) | hidden tiles in a view: {r['nl']} {r['leak'] or ''}"
          f" | changed when hidden tiles were shuffled: {r['nd']} {r['diff'] or ''}", flush=True)
    for e in r['log']:
        kinds[e[0]] = kinds.get(e[0], 0) + 1

# the leak check must be able to fail: plant a tile from the pile in a view
planted = f.evaluate("(()=>{const G=__remi.G;G.disc.forEach(id=>__fair.seen.add(id));const v=__remi.viewOf(1),x=[...G.pile,...G.pl[0].hand].find(id=>!__fair.seen.has(id)&&id!==tw(G.atu));v.h[x]=2;return __leaks(v,G).length})()")
print('planted leak noticed:', planted == 1); fails += planted != 1

# 4. the source never names the game state or the page
src = f.evaluate("Object.entries(__remi.brain).map(([k,v])=>[k,typeof v==='function'?String(v):null])")
words = re.compile(r'\b(G|T|window|document|localStorage|lvl|token)\b|Math\.random')
named = [(k, m.group(0)) for k, s in src if s for m in [words.search(s)] if m]
print('brain functions:', sum(1 for k, s in src if s), '| naming the game state, the page or Math.random:', named or 'none'); fails += len(named)

# 3. empty room: only the brain's own source, the views and the seeds
code = f.evaluate("Object.entries(__remi.brain).map(([k,v])=>'var '+k+'='+(typeof v==='function'?'('+v+')':JSON.stringify(v))+';').join('\\n')")
room = b.new_page(); room.goto('about:blank')
room.add_script_tag(content="Math.random=function(){throw new Error('Math.random used')};\n" + code +
                    "\nvar RB={start:rbStart,lay:rbLay,extras:rbExtras,disc:rbDisc};"
                    "window.replay=L=>{let bad=[];L.forEach(([k,s,v,o],i)=>{let r;try{r=JSON.stringify(RB[k](JSON.parse(v),naRng(s)))}catch(e){r='error: '+e.message}"
                    "if(r!==o)bad.push([i,k,r.slice(0,80),o.slice(0,80)])});return bad}")
globals_ = room.evaluate("['G','__remi','naR','naKnobs'].filter(k=>k in window)")
bad = []
for i in range(0, len(logs), 400):
    bad += room.evaluate("L=>replay(L)", logs[i:i + 400])
print(f"empty room: {len(logs)} decisions replayed {kinds} | game objects in the room: {globals_ or 'none'} | different answers: {len(bad)} {bad[:3] or ''}")
fails += len(bad) + len(globals_)
print('console errors:', page.errors[:5]); fails += len(page.errors)
print('FAIR' if not fails else 'NOT FAIR: %d problems' % fails)
b.close(); pw.stop()
sys.exit(1 if fails else 0)
