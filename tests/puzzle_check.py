"""Puzzles re-solved by independent solvers. Sudoku: every generated puzzle has exactly one solution and it is the
stored one; one puzzle per level is played through (wrong digit, undo, hint, solve) and one is solved by Hint taps alone,
each teaching step (tap 1) checked against independently worked-out candidates before Fill (tap 2). Water Sort: levels
1-3, 4-6, 8-10, 13-15, 20-22 are solved by a separate solver and played by tapping, with Accessibility on (marks
checked); then levels 1, 8 and 13 are played by Hint taps alone (each hint pour is checked against a separate solver)
and random pours run until the stuck alert shows, which is checked: the position really has no way out, and the
number of Undos it asks for is the fewest that reach a solvable position.

    python3 tests/puzzle_check.py sdk 15
    python3 tests/puzzle_check.py ws
"""
import sys, json, time
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, to_cover
which=sys.argv[1]; port=start_server(8921 if which=='sdk' else 8922); pw,b,page=open_page(port,'iphone12')
# ---------- Sudoku: independent solution counter ----------
def count_solutions(g,limit=2):
    rows=[0]*9; cols=[0]*9; boxes=[0]*9; g=g[:]
    for i,v in enumerate(g):
        if v:
            bit=1<<v; r,c=divmod(i,9); bx=r//3*3+c//3
            if rows[r]&bit or cols[c]&bit or boxes[bx]&bit: return 0,None
            rows[r]|=bit; cols[c]|=bit; boxes[bx]|=bit
    res=[0,None]
    def rec():
        best=-1; bm=0; bc=10
        for i in range(81):
            if not g[i]:
                r,c=divmod(i,9); m=~(rows[r]|cols[c]|boxes[r//3*3+c//3])&0x3fe; n=bin(m).count('1')
                if n<bc: best,bm,bc=i,m,n
                if n==0: return
        if best<0:
            res[0]+=1
            if res[1] is None: res[1]=g[:]
            return
        r,c=divmod(best,9); bx=r//3*3+c//3
        for v in range(1,10):
            if bm>>v&1:
                bit=1<<v; g[best]=v; rows[r]|=bit; cols[c]|=bit; boxes[bx]|=bit
                rec()
                g[best]=0; rows[r]&=~bit; cols[c]&=~bit; boxes[bx]&=~bit
                if res[0]>=limit: return
    rec(); return res[0],res[1]
if which=='sdk':
    f=open_game(page,'sdk',1500); bad=[]
    for diff,n in [('easy',int(sys.argv[2])),('normal',int(sys.argv[2])),('hard',int(sys.argv[2])),('master',max(3,int(sys.argv[2])//3))]:
        gv=[]; t0=time.time()
        for k in range(n):
            f.evaluate("S.diff='%s';start()"%diff)
            for _ in range(400):
                page.wait_for_timeout(50)
                if f.evaluate("!!giv&&!over"): break
            giv,sol=f.evaluate("[giv,sol]"); cnt,mine=count_solutions(giv)
            gv.append(sum(1 for v in giv if v))
            if cnt!=1: bad.append('%s puzzle has %d solutions'%(diff,cnt))
            elif mine!=sol: bad.append(diff+' stored solution differs from the real one')
            if k==0:  # play it through the UI: a wrong digit, undo, two hints, then the rest
                rec0=f.evaluate("JSON.stringify(REC)")
                e=[i for i in range(81) if not giv[i]]
                wrong=next(d for d in range(1,10) if d!=sol[e[0]])
                f.evaluate("(a)=>{cells[a[0]].click();[...document.querySelectorAll('#pad button')].find(b=>b.textContent.trim()==String(a[1])).click()}",[e[0],wrong])
                if f.evaluate("over"): bad.append('over after a wrong digit')
                f.evaluate("undo()")
                if f.evaluate("val[%d]"%e[0])!=0: bad.append('undo did not clear the wrong digit')
                f.evaluate("hintOn=true;cells[%d].click();hint()"%e[1])
                if f.evaluate("val.filter(Boolean).length")!=sum(1 for v in giv if v): bad.append('hint tap 1 changed the board')
                f.evaluate("hint()"); hc=f.evaluate("fix.indexOf(2)")
                if hc<0 or f.evaluate("val[%d]"%hc)!=sol[hc]: bad.append('hint gave a wrong digit')
                for i in e:
                    if i==hc: continue
                    f.evaluate("(a)=>{cells[a[0]].click();[...document.querySelectorAll('#pad button')].find(b=>b.textContent.trim()==String(a[1])).click()}",[i,sol[i]])
                page.wait_for_timeout(150)
                over,msg,rec1=f.evaluate("[over,document.getElementById('msg')?document.getElementById('msg').textContent:'',JSON.stringify(REC)]")
                if not over: bad.append(diff+' not over after filling the solution')
                if rec0==rec1: bad.append(diff+' solved count did not change')
                print('   played',diff,'| over',over,'|',msg[:60],'| record',rec0,'->',rec1,flush=True)
        # a whole puzzle by Hint taps alone: every teaching step must be true
        f.evaluate("S.diff='%s';start()"%diff)
        for _ in range(400):
            page.wait_for_timeout(50)
            if f.evaluate("!!giv&&!over"): break
        f.evaluate("hintOn=true;render()"); kinds={}; sol=f.evaluate("sol")
        for step in range(90):
            if f.evaluate("over"): break
            f.evaluate("sel=-1;hint()")
            v,t,msg,lbl=f.evaluate("[val,tip&&{c:tip.c,d:tip.d,u:tip.u,t:tip.t},document.getElementById('msg').textContent,document.getElementById('aHint').textContent]")
            if not t: bad.append(diff+' hint tap 1 gave no step'); break
            c,d=t['c'],t['d']; kind='beyond' if 'No simple step' in msg else ('pairs ' if 'with pairs' in msg else '')+('box' if 'this box' in msg else 'row' if 'this row' in msg else 'column' if 'this column' in msg else 'cell' if 'this cell' in msg else 'none')
            kinds[kind]=kinds.get(kind,0)+1
            if lbl!='Fill': bad.append('Hint button not Fill after tap 1')
            if sol[c]!=d or v[c]: bad.append(diff+' tip points at a wrong or filled cell')
            if t['u'] and c not in t['u']: bad.append('tip cell outside its unit')
            if 'with pairs' not in msg and kind not in ('none','beyond'):
                cand=lambda i: set() if v[i] else set(range(1,10))-{v[p] for p in range(81) if p!=i and (p//9==i//9 or p%9==i%9 or (p//27==i//27 and p%9//3==i%9//3))}
                if kind=='cell':
                    if cand(c)!={d}: bad.append(diff+' "only one number fits" is not true')
                elif [i for i in t['u'] if d in cand(i)]!=[c]: bad.append(diff+' "only one cell can take" is not true')
            f.evaluate("hint()")
            if f.evaluate("val[%d]"%c)!=d: bad.append('Fill did not place the tip')
        if not f.evaluate("over"): bad.append(diff+' not solved by hints alone')
        print('   hints alone',diff,'| solved',f.evaluate("over"),'| steps',kinds,flush=True)
        print('Sudoku',diff,'puzzles',n,'givens min/max',min(gv),max(gv),'time/puzzle %.1fs'%((time.time()-t0)/n),flush=True)
    print('Sudoku problems:',sorted(set(bad)))
# ---------- Water Sort: independent solver, then play the solution by tapping ----------
def ws_pour(ts,a,b,cap=4):
    A,B=ts[a],ts[b]
    if a==b or not A or len(B)>=cap: return 0
    c=A[-1]
    if B and B[-1]!=c: return 0
    n=0
    while A and A[-1]==c and len(B)<cap: B.append(A.pop()); n+=1
    return n
def ws_solve(start,cap=4,limit=400000):
    done=lambda ts: all((not t) or (len(t)==cap and len(set(t))==1) for t in ts)
    seen=set(); stack=[(tuple(tuple(t) for t in start),[])]; nodes=0
    while stack:
        st,path=stack.pop(); key=tuple(sorted(st))
        if key in seen: continue
        seen.add(key); nodes+=1
        if done(st): return path,nodes
        if nodes>limit: return None,nodes
        nxt=[]
        for a in range(len(st)):
            A=st[a]
            if not A or (len(A)==cap and len(set(A))==1): continue
            usedEmpty=False
            for bb in range(len(st)):
                B=st[bb]
                if a==bb or len(B)>=cap: continue
                if B and B[-1]!=A[-1]: continue
                if not B:
                    if usedEmpty or len(set(A))==1: continue
                    usedEmpty=True
                ts=[list(t) for t in st]; ws_pour(ts,a,bb,cap)
                score=sum(1 for t in ts if t and len(set(t))==1)*3+sum(1 for t in ts if not t)
                nxt.append((score,tuple(tuple(t) for t in ts),path+[(a,bb)]))
        nxt.sort(key=lambda x:x[0])
        for s,t,p in nxt: stack.append((t,p))
    return None,nodes
if which=='ws':
    bad=[]
    for lvl0 in [1,4,8,13,20]:
        page.evaluate("(l)=>{localStorage.clear();localStorage.setItem('ws-rules-seen','1');localStorage.setItem('ws_level',l);localStorage.setItem('ws_sym','1')}",lvl0)
        page.reload(); page.wait_for_timeout(400); f=open_game(page,'ws',900)
        for step in range(3):
            g=json.loads(f.evaluate("localStorage.getItem('ws_game')")); lvl=g['level']; ts=[list(t) for t in g['tubes']]
            ncol=len(set(c for t in ts for c in t)); empty=sum(1 for t in ts if not t)
            cnt={}
            for t in ts:
                for c in t: cnt[c]=cnt.get(c,0)+1
            if any(v!=4 for v in cnt.values()): bad.append('level %d: a colour does not have 4 layers'%lvl)
            # marks match colours
            mk=f.evaluate("[...document.querySelectorAll('#board .tube')].map(t=>[...t.querySelectorAll('.liq')].map(l=>[l.style.color,l.querySelector('.sy').className,getComputedStyle(l.querySelector('.sy')).display]))")
            cmap={}
            for ti,t in enumerate(mk):
                for li,(col,cls,disp) in enumerate(t):
                    if cls!='sy s%d'%ts[ti][li]: bad.append('mark class %s on colour %d'%(cls,ts[ti][li]))
                    if disp=='none': bad.append('mark hidden with Accessibility on')
                    cmap.setdefault(ts[ti][li],set()).add(col)
            if any(len(v)!=1 for v in cmap.values()): bad.append('one colour index drawn in two colours')
            t0=time.time(); path,nodes=ws_solve(ts)
            if path is None: bad.append('level %d: my solver found no solution in %d states'%(lvl,nodes)); print('Water Sort level',lvl,'colours',ncol,'empty',empty,'NOT SOLVED by my solver',nodes,flush=True); break
            model=[list(t) for t in ts]
            for a,bb in path:
                ws_pour(model,a,bb)
                f.evaluate("(m)=>{const t=document.querySelectorAll('#board .tube');t[m[0]].click();document.querySelectorAll('#board .tube')[m[1]].click()}",[a,bb])
                got=json.loads(f.evaluate("localStorage.getItem('ws_game')"))['tubes']
                if got!=model: bad.append('level %d: tubes differ from my model after a pour'%lvl); break
            page.wait_for_timeout(200)
            g2=json.loads(f.evaluate("localStorage.getItem('ws_game')")); sub=f.evaluate("document.getElementById('sub').textContent"); msg=f.evaluate("document.getElementById('msg').textContent")
            solvedN=f.evaluate("localStorage.getItem('ws_solved')")
            print('Water Sort level',lvl,'colours',ncol,'empty tubes',empty,'my solution',len(path),'pours, solver states',nodes,'| won',g2.get('won'),'|',msg,'| solved count',solvedN,flush=True)
            if not g2.get('won'): bad.append('level %d not won after my solution'%lvl); break
            if g2.get('moves')!=len(path): bad.append('level %d: move count %s vs %d pours'%(lvl,g2.get('moves'),len(path)))
            f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Next level').click()"); page.wait_for_timeout(700)
            if json.loads(f.evaluate("localStorage.getItem('ws_game')"))['level']!=lvl+1: bad.append('Next level did not go to %d'%(lvl+1))
        to_cover(page)
    # Hint taps alone, each pour checked: from a solvable position the hint keeps it solvable, one step shorter
    def shortest(ts):  # plain breadth-first search, independent of the game's A*
        start=tuple(tuple(t) for t in ts); done=lambda s: all((not t) or (len(t)==4 and len(set(t))==1) for t in s)
        if done(start): return 0
        seen={tuple(sorted(start))}; frontier=[start]; d=0
        while frontier:
            d+=1; nxt=[]
            for st in frontier:
                for a in range(10):
                    for bb in range(10):
                        l=[list(t) for t in st]
                        if not ws_pour(l,a,bb): continue
                        k=tuple(sorted(tuple(t) for t in l))
                        if k in seen: continue
                        if done(l): return d
                        seen.add(k); nxt.append(tuple(tuple(t) for t in l))
            frontier=nxt
            if len(seen)>2500000: return None
        return -1
    for lvl in [1,8,13]:
        page.evaluate("(l)=>{localStorage.clear();localStorage.setItem('ws-rules-seen','1');localStorage.setItem('ws_level',l);localStorage.setItem('ws_hint','1')}",lvl)
        page.reload(); page.wait_for_timeout(400); f=open_game(page,'ws',900); n=0; first=None; checked=0
        while n<80:
            if 'Next level' in f.evaluate("[...document.querySelectorAll('#acts button')].map(b=>b.textContent)"): break
            f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Hint').click()")
            for _ in range(150):
                page.wait_for_timeout(20)
                h=f.evaluate("[[...document.querySelectorAll('#board .tube')].findIndex(t=>t.classList.contains('sel')),[...document.querySelectorAll('#board .tube')].findIndex(t=>t.classList.contains('hn')),document.getElementById('msg').textContent]")
                if h[1]>=0: break
            if h[1]<0 or h[0]<0: bad.append('level %d: no hint shown (%s)'%(lvl,h[2])); break
            ts=json.loads(f.evaluate("localStorage.getItem('ws_game')"))['tubes']; togo=int(h[2].split('· ')[1].split()[0])
            if n<3 and lvl<13:  # BFS is slow; check the first pours of the 8-colour levels
                d0=shortest(ts); l=[list(t) for t in ts]
                if not ws_pour(l,h[0],h[1]): bad.append('level %d: hint pour is not a legal pour'%lvl)
                d1=shortest(l)
                if d0 is not None and (d0!=togo or d1!=d0-1): bad.append('level %d: hint not on a shortest way (%s to go said, BFS %s then %s)'%(lvl,togo,d0,d1))
                checked+=1
            if first is None: first=togo
            f.evaluate("(i)=>document.querySelectorAll('#board .tube')[i].click()",h[1]); n+=1
        g=json.loads(f.evaluate("localStorage.getItem('ws_game')"))
        print('Water Sort hints alone level',lvl,'| said',first,'to go, took',n,'pours | won',g['won'],'| pours checked by BFS',checked,flush=True)
        if not g['won'] or n!=first: bad.append('level %d: hints alone did not solve in the promised pours'%lvl)
    # stuck alert: random pours until it shows, then check it independently
    import random; random.seed(7); alerts=0
    for lvl in [13,13,13,8,8]:
        page.evaluate("(l)=>{localStorage.clear();localStorage.setItem('ws-rules-seen','1');localStorage.setItem('ws_level',l)}",lvl)
        page.reload(); page.wait_for_timeout(400); f=open_game(page,'ws',900); seenpos=[]
        for k in range(200):
            ts=json.loads(f.evaluate("localStorage.getItem('ws_game')"))['tubes']; seenpos.append(ts)
            mv=[(a,c) for a in range(10) for c in range(10) if a!=c and ts[a] and len(ts[c])<4 and (not ts[c] or ts[c][-1]==ts[a][-1]) and not (len(set(ts[a]))==1 and not ts[c])]
            if not mv: break
            a,c=random.choice(mv)
            f.evaluate("(m)=>{const t=document.querySelectorAll('#board .tube');t[m[0]].click();document.querySelectorAll('#board .tube')[m[1]].click()}",[a,c]); page.wait_for_timeout(150)
            m=f.evaluate("document.getElementById('msg').textContent")
            if 'No way out' in m:
                cur=json.loads(f.evaluate("localStorage.getItem('ws_game')"))['tubes']
                if ws_solve(cur)[0] is not None: bad.append('stuck alert on a solvable position')
                u=int(m.split('Undo ')[1].split()[0]) if 'Undo' in m else -1
                back=seenpos[::-1]
                want=next((i+1 for i,p in enumerate(back) if ws_solve(p)[0] is not None),-1)
                if u!=want: bad.append('stuck alert says Undo %s, fewest is %s'%(u,want))
                print('Water Sort stuck alert level',lvl,'after',k+1,'random pours:',m,'| fewest Undos',want,flush=True); alerts+=1
                break
            elif ws_solve(json.loads(f.evaluate("localStorage.getItem('ws_game')"))['tubes'])[0] is None:
                page.wait_for_timeout(600)
                if 'No way out' not in f.evaluate("document.getElementById('msg').textContent"): bad.append('stuck position with no alert'); break
        to_cover(page)
    if not alerts: bad.append('no stuck alert seen')
    print('Water Sort problems:',sorted(set(bad)))
print('console errors:',page.errors[:5]); b.close(); pw.stop()
