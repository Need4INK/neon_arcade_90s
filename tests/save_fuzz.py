"""Damaged saved data: plays a little to make real saves, then reopens the game with each saved value damaged
(garbage, cut in half, every field deleted / wrong type / out of range) and with storage blocked. The game must open,
be playable, show no "undefined"/"NaN" and log no errors.

    python3 tests/save_fuzz.py kb 8901      # game: kb, oth, ws, sdk, rem; any free port
"""
import sys, json, random, copy
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, game_frame, close_panel
G=sys.argv[1]; port=start_server(int(sys.argv[2])); random.seed(5)
KEYS={'kb':['kb-stats','kb-rec','kb-game'],'oth':['oth-stats','oth-rec','oth-game'],'ws':['ws_level','ws_best','ws_solved','ws_game','ws_sym'],
      'sdk':['sdk-best','sdk-game','sdk-solved'],'rem':['remi_set','remi_game2','remi_rec']}[G]
POKE="""(()=>{const bs=[...document.querySelectorAll('main button, #app button, body button')].filter(b=>!b.closest('#bar')&&!b.closest('#panel')&&!b.disabled&&b.getClientRects().length&&getComputedStyle(b).pointerEvents!=='none');
 if(!bs.length)return 0;const b=bs[Math.floor(Math.random()*bs.length)];b.click();return bs.length})()"""
BAD="""(()=>{const t=document.body.innerText;const m=t.match(/undefined|NaN|\\[object|Infinity/);return m?m[0]+' in: '+t.slice(Math.max(0,m.index-30),m.index+30).replace(/\\n/g,' '):''})()"""
pw,b,page=open_page(port,'iphone12')
def fresh(store):
    # close any open game first: one left open saves itself when the page closes (Sudoku does) and would overwrite the damaged values
    page.evaluate("document.querySelectorAll('iframe').forEach(f=>f.remove())")
    page.evaluate("(s)=>{localStorage.clear();for(const k in s)localStorage.setItem(k,s[k]);localStorage.setItem('%s-rules-seen','1');localStorage.setItem('remi-rules-seen','1');localStorage.setItem('ws-rules-seen','1')}"%G, store)
    page.errors.clear(); page.reload(); page.wait_for_timeout(350)
    try: f=open_game(page,G,500)
    except Exception as e: return None,'game did not open: '+str(e)[:80]
    return f,''
def poke(f,n,wait=120):
    c=0
    for _ in range(n):
        try: c=f.evaluate(POKE)
        except Exception as e: return 'poke failed '+str(e)[:60]
        page.wait_for_timeout(wait)
    return c
# 1) make a real save by playing a little
f,_=fresh({}); poke(f,30,200); page.wait_for_timeout(1500)
base=page.evaluate("(ks)=>{const o={};ks.forEach(k=>{const v=localStorage.getItem(k);if(v!=null)o[k]=v});return o}",KEYS)
print(G,'saved keys:',{k:len(v) for k,v in base.items()},flush=True)
cases=[]
for k in KEYS:
    for v in ['x','null','{}','[]','0','"s"','{"a":','true','-1','1e9','9999999']: cases.append((k+' = '+v,{**base,k:v}))
    if k in base:
        cases.append((k+' truncated',{**base,k:base[k][:len(base[k])//2]}))
        try: o=json.loads(base[k])
        except Exception: o=None
        if isinstance(o,dict):
            for fld in list(o.keys()):
                for name,mut in [('deleted',None),('null','N'),('"x"','x'),('-5',-5),('[]',[]),('{}',{}),('1e9',10**9)]:
                    c=copy.deepcopy(o)
                    if mut is None: del c[fld]
                    elif mut=='N': c[fld]=None
                    else: c[fld]=mut
                    cases.append(('%s.%s %s'%(k,fld,name),{**base,k:json.dumps(c)}))
                # nested: shorten arrays / corrupt first element
                if isinstance(o[fld],list) and o[fld]:
                    c=copy.deepcopy(o); c[fld]=c[fld][:-1]; cases.append(('%s.%s shorter'%(k,fld),{**base,k:json.dumps(c)}))
                    c=copy.deepcopy(o); c[fld][0]='x'; cases.append(('%s.%s[0]="x"'%(k,fld),{**base,k:json.dumps(c)}))
                    c=copy.deepcopy(o); c[fld][0]=99; cases.append(('%s.%s[0]=99'%(k,fld),{**base,k:json.dumps(c)}))
print(G,'cases:',len(cases),flush=True)
bad=0
for name,store in cases:
    f,err=fresh(store)
    res=[]
    if f is None: res.append(err)
    else:
        page.wait_for_timeout(250); p=poke(f,6,90); page.wait_for_timeout(300)
        if p==0 or isinstance(p,str): res.append('nothing to tap: '+str(p))
        try:
            t=f.evaluate(BAD)
            if t: res.append('text: '+t)
            f.evaluate("document.getElementById('bSet').click()"); page.wait_for_timeout(80)   # records are shown in Settings
            t=f.evaluate(BAD)
            if t: res.append('settings text: '+t)
        except Exception as e: res.append('frame gone')
        if page.errors: res.append('errors: '+' | '.join(sorted(set(page.errors)))[:260])
    if res: bad+=1; print('FAIL',name,'->',' ; '.join(res),flush=True)
print(G,'done, failures:',bad,'of',len(cases),flush=True)
# 2) storage blocked entirely
ctx=b.new_context(viewport={'width':390,'height':797},has_touch=True,is_mobile=True)
ctx.add_init_script("try{const t=()=>{throw new DOMException('blocked','SecurityError')};Storage.prototype.getItem=t;Storage.prototype.setItem=t;Storage.prototype.removeItem=t}catch(e){}")
pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
pg.goto('http://127.0.0.1:%s/index.html'%sys.argv[2]); pg.wait_for_timeout(700); pg.click('.card[data-g="%s"]'%G); pg.wait_for_timeout(900)
fr=[x for x in pg.frames if x!=pg.main_frame and x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")]
if fr:
    close_panel(fr[0]); 
    for _ in range(12): fr[0].evaluate(POKE); pg.wait_for_timeout(120)
print(G,'storage blocked: opens',bool(fr),'errors',sorted(set(errs))[:4],flush=True)
b.close(); pw.stop()
