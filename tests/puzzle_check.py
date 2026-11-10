"""Puzzles re-solved by independent solvers. Sudoku: every generated puzzle has exactly one solution and it is the
stored one; one puzzle per level is played through (wrong digit, undo, hint, solve). Water Sort: levels 1-3, 4-6,
8-10, 13-15, 20-22 are solved by a separate solver and played by tapping, with Accessibility on (marks checked).

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
                if f.evaluate("val[%d]"%e[1])!=sol[e[1]]: bad.append('hint gave a wrong digit')
                for i in e:
                    if i==e[1]: continue
                    f.evaluate("(a)=>{cells[a[0]].click();[...document.querySelectorAll('#pad button')].find(b=>b.textContent.trim()==String(a[1])).click()}",[i,sol[i]])
                page.wait_for_timeout(150)
                over,msg,rec1=f.evaluate("[over,document.getElementById('msg')?document.getElementById('msg').textContent:'',JSON.stringify(REC)]")
                if not over: bad.append(diff+' not over after filling the solution')
                if rec0==rec1: bad.append(diff+' solved count did not change')
                print('   played',diff,'| over',over,'|',msg[:60],'| record',rec0,'->',rec1,flush=True)
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
    print('Water Sort problems:',sorted(set(bad)))
print('console errors:',page.errors[:5]); b.close(); pw.stop()
