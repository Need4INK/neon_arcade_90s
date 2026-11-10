"""Rough handling: random fast taps on everything (double taps, Settings, Exit, reloads at random moments), then
checks the game is still consistent, not stuck on a CPU turn, and logged no errors.

    python3 tests/monkey.py kb 8941 11 x 30   # game, free port, random seed, x = small phone, rounds of 40 taps
"""
import sys, random, json
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, game_frame, to_cover
G=sys.argv[1]; port=start_server(int(sys.argv[2])); random.seed(int(sys.argv[3]) if len(sys.argv)>3 else 11)
pw,b,page=open_page(port,'small' if len(sys.argv)>4 else 'iphone12')
POKE="""(all)=>{const bs=[...document.querySelectorAll('button')].filter(b=>!b.disabled&&b.getClientRects().length&&getComputedStyle(b).pointerEvents!=='none'&&(all||(!b.closest('#bar')&&!b.closest('#panel'))));
 if(!bs.length)return '';const b=bs[Math.floor(Math.random()*bs.length)];const t=(b.id||b.className||'')+':'+b.textContent.trim().slice(0,12);b.click();if(Math.random()<.3)b.click();return t}"""
BAD="""(()=>{const t=document.body.innerText;const m=t.match(/undefined|NaN|\\[object|Infinity|null/);return m?m[0]+' in: '+t.slice(Math.max(0,m.index-30),m.index+30).replace(/\\n/g,' '):''})()"""
INV={'kb':"""(()=>{const e=[];[p,c].forEach(g=>{if(g.length!==NC)e.push('grid width');g.forEach(a=>{if(a.length>3)e.push('column over 3');a.forEach(v=>{if(!(v>=1&&v<=6))e.push('bad die value')})})});
  if(+document.getElementById('ps').textContent!==total(p)||+document.getElementById('cs').textContent!==total(c))e.push('score shown differs');
  if(!over&&(full(p)||full(c)))e.push('full grid, game goes on');if(!over&&!(die>=1&&die<=6))e.push('no die');return [e,over||mode!=='cpu'||turn==='p']})()""",
 'oth':"""(()=>{const e=[];if(bd.length!==8||bd.some(r=>r.length!==8||r.some(v=>v!==0&&v!==1&&v!==-1)))e.push('bad board');
  if(!over&&!moves(bd,turn).length)e.push('side to move has no move');if(!over&&busy&&!(mode==='cpu'&&turn===C))e.push('busy outside CPU turn');
  const k=count(bd);const sh=[...document.querySelectorAll('#hdY .sc,#hdO .sc,#yc,#oc')].map(x=>+x.textContent);return [e,over||mode!=='cpu'||turn===P]})()""",
 'ws':"""(()=>{const e=[];const g=JSON.parse(localStorage.getItem('ws_game')||'null');if(!g)return [['no saved game'],true];const n={};g.tubes.forEach(t=>{if(t.length>4)e.push('tube over 4');t.forEach(c=>n[c]=(n[c]||0)+1)});
  for(const c in n)if(n[c]!==4)e.push('colour count '+n[c]);const dom=[...document.querySelectorAll('#board .tube')].map(t=>t.querySelectorAll('.liq').length);
  if(JSON.stringify(dom)!==JSON.stringify(g.tubes.map(t=>t.length)))e.push('screen differs from saved tubes');return [e,true]})()""",
 'sdk':"""(()=>{const e=[];if(!giv)return [e,true];if(val.length!==81)e.push('val length');for(let i=0;i<81;i++){if(giv[i]&&val[i]!==giv[i])e.push('given changed');if(fix[i]===2&&val[i]!==sol[i])e.push('hinted cell wrong');if(val[i]<0||val[i]>9)e.push('bad value')}
  if(over&&!val.every((v,i)=>v===sol[i]))e.push('over but not solved');const shown=cells.map(c=>{const t=c.firstChild&&c.firstChild.nodeType===3?c.firstChild.textContent.trim():c.textContent.trim();return t.length===1?+t:0});
  for(let i=0;i<81;i++)if(val[i]&&shown[i]!==val[i]){e.push('cell shows '+shown[i]+' holds '+val[i]);break}return [e,true]})()""",
 'rem':"""(()=>{const e=[],R=window.__remi,G=R&&R.G;if(!G)return [e,true];const all=[...G.pile,...G.disc,...G.pl.flatMap(P=>P.hand),...G.melds.flatMap(m=>m.t)];
  if(G.phase!=='end'&&G.phase!=='over'&&(all.length!==106||new Set(all).size!==106))e.push('tiles '+all.length+'/'+new Set(all).size+' in phase '+G.phase);
  const badm=G.melds.filter(m=>!R.analyze(m.t)).length;if(badm)e.push(badm+' invalid formations');
  const rack=document.querySelectorAll('#rack .tl').length;if(G.pl&&G.pl[0]&&rack!==G.pl[0].hand.length)e.push('rack shows '+rack+' holds '+G.pl[0].hand.length);
  return [e,G.cur===0||['end','over','dbl','score','done'].indexOf(G.phase)>=0,G.phase,G.cur]})()"""}[G]
def frame():
    try:
        f=game_frame(page)
        if G=='rem' and not f.evaluate("!!window.__remi"): raise Exception()
        return f
    except Exception:
        try:
            page.evaluate("kbShowCover()"); page.wait_for_timeout(300); page.click('.card[data-g="%s"]'%G,timeout=3000); page.wait_for_timeout(700)
            f=game_frame(page)
        except Exception as ex:
            global shots
            if not shots:
                shots=1; page.screenshot(path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','stuck_%s.png'%G))
                print('COVER STUCK state:',page.evaluate("[location.href,document.querySelectorAll('.card').length,[...document.querySelectorAll('iframe')].map(f=>f.hidden),document.body.className,document.documentElement.className]"),'last',last[-6:],flush=True)
            page.reload(); page.wait_for_timeout(500); f=open_game(page,G,700)
        from harness import close_panel
        close_panel(f); return f
shots=0
f=open_game(page,G,900); probs={}; acts=0; last=[]
def note(k,ctx=''):
    if k not in probs: probs[k]=ctx
ROUNDS=int(sys.argv[5]) if len(sys.argv)>5 else 40
for rnd in range(ROUNDS):
    for i in range(40):
        try: t=f.evaluate(POKE, random.random()<.18)
        except Exception: f=frame(); continue
        acts+=1; last=(last+[t])[-12:]
        if random.random()<.3: page.wait_for_timeout(random.choice([0,5,20,60,200,700]))
        if not page.query_selector('.card') or True:
            try:
                if not f.evaluate("document.querySelector('main').getClientRects().length>0"): f=frame()
            except Exception: f=frame()
    if random.random()<.35:
        page.reload(); page.wait_for_timeout(400); f=frame()
    page.wait_for_timeout(300)
    try:
        t=f.evaluate(BAD)
        if t: note('text: '+t,str(last))
        r=f.evaluate(INV)
        for e in r[0]: note(e,str(last))
        if not r[1]:
            ok=False
            for _ in range(60):
                page.wait_for_timeout(250)
                r=f.evaluate(INV)
                if r[1]: ok=True; break
            if not ok: note('stuck waiting for the CPU: '+json.dumps(r[2:]),str(last))
            for e in r[0]: note(e,str(last))
    except Exception as ex:
        note('check failed: '+str(ex)[:120],str(last)); f=frame()
    for e in set(page.errors): note('console: '+e[:200],str(last))
    page.errors.clear()
print(G,'actions',acts,'problems',len(probs),flush=True)
for k,v in probs.items(): print('  -',k,'\n      after:',v[:330],flush=True)
b.close(); pw.stop()
