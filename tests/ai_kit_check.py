"""The CPU brain kit in games/core.js (naRng, naThink, naSearch, naWorker, naChoose, naKnobs, naAdapt, window.__ai),
checked inside every game's frame.

    python3 tests/ai_kit_check.py

Prints one line per check; False means it failed (exit code 1 via harness.strict()).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, to_cover, GAMES, strict

strict()
JS = r"""async()=>{const R={},A=window.__ai;
 R.hook=!!A&&typeof A.seed==='function'&&(A.pick===null||typeof A.pick==='function')&&A.adapt===true;
 // naRng: same seed, same numbers; in 0..1
 const a=naRng(5),b=naRng(5),xs=[];for(let i=0;i<1000;i++)xs.push(a());R.rngRepeat=xs.every(x=>x===b());R.rngRange=xs.every(x=>x>=0&&x<1);
 A.seed(9);const s1=[naR(),naR()];A.seed(9);R.seed=JSON.stringify(s1)===JSON.stringify([naR(),naR()]);
 // the kit never uses Math.random (seeded tests of the games keep their sequence)
 const mr=Math.random;let used=0;Math.random=()=>{used++;return mr()};
 // naChoose
 const ms=[{s:1,id:'a'},{s:5,id:'b'},{s:3,id:'c'}],r=naRng(3),cnt=k=>{const n={a:0,b:0,c:0};for(let i=0;i<3000;i++)n[naChoose(ms,k,r).id]++;return n};
 let n=cnt({temp:0,blind:0});R.chooseBest=n.b===3000;
 n=cnt({temp:0,blind:1});R.chooseBlind=n.b===0&&n.c===3000;
 n=cnt({temp:2,blind:0});R.chooseSoft=n.b>n.c&&n.c>n.a&&n.a>0;
 n=cnt({temp:0,blind:.3});R.chooseBlindRate=Math.abs(n.b/3000-.7)<.04;
 const mm=[{s:9,id:'a',miss:1},{s:1,id:'b',miss:0}];R.chooseMiss=Array.from({length:500},()=>naChoose(mm,{blind:1},r).id).every(x=>x==='b');
 R.chooseOne=naChoose([{s:1,id:'z'}],{blind:1})?.id==='z'&&naChoose([],{})===undefined;
 // naSearch: keeps the deepest depth that finished; the first depth always finishes
 let deep=naSearch((d,dl)=>{const t=naNow();while(naNow()-t<(d<4?2:400))naTick(dl);return d*10},{from:1,to:8,deadline:naNow()+60});
 R.searchDeep=deep&&deep.depth===3&&deep.v===30;
 deep=naSearch((d,dl)=>{const t=naNow();while(naNow()-t<30)naTick(dl);return d},{from:2,to:5,deadline:naNow()+1});R.searchFirst=deep&&deep.depth===2;
 deep=naSearch(d=>d===3?{done:true,d}:{d},{from:1,to:9});R.searchDone=deep.depth===3;
 // naThink: waits at least min; a changed game gets no answer
 let t0=naNow(),v=await naThink(dl=>dl>naNow()?42:0,{min:120,max:500});R.thinkMin=v===42&&naNow()-t0>=115;
 let got=false,live=true;naThink(()=>1,{min:50,ok:()=>live}).then(()=>got=true);live=false;await new Promise(r=>setTimeout(r,150));R.thinkCancel=!got;
 A.fast=true;t0=naNow();await naThink(()=>1,{min:400});R.thinkFast=naNow()-t0<100;A.fast=false;
 // naWorker: in a Worker (with the kit's helpers) and on the main thread
 function sq(d){return {x:d*d,seeded:typeof naRng==='function'&&typeof naSearch==='function',worker:typeof document==='undefined'}}
 const w=naWorker(sq);let r1=await w.run(7);R.worker=r1.x===49&&r1.seeded&&r1.worker;w.stop();
 A.main=true;const w2=naWorker(sq);r1=await w2.run(6);R.workerMain=r1.x===36&&!r1.worker;A.main=false;
 function boom(){throw new Error('x')}const w3=naWorker(boom);R.workerErr=await w3.run(1).then(()=>false,()=>true);w3.stop();
 // naKnobs and naAdapt: Hard never moves; Easy at its sharpest stays weaker than plain Normal; damaged saves = no change
 const G='kitcheck';localStorage.removeItem(G+'-adapt');
 const k0=naKnobs(G,'easy'),kn=naKnobs(G,'normal'),kh=naKnobs(G,'hard');R.knobsPlain=k0.temp===1.2&&k0.blind===.3&&kh.temp===0&&k0.adapt===0;
 for(let i=0;i<40;i++){naAdaptNote(G,'easy',1);naAdaptNote(G,'normal',1);naAdaptNote(G,'hard',1)}
 const ke=naKnobs(G,'easy'),kn2=naKnobs(G,'normal'),kh2=naKnobs(G,'hard');
 R.adaptSharp=ke.adapt>.99&&ke.temp<k0.temp&&ke.temp>kn.temp&&ke.blind>kn.blind&&kn2.temp<kn.temp&&kn2.temp>kh.temp&&kh2.adapt===0&&kh2.temp===0;
 R.adaptHardNotSaved=!('hard' in JSON.parse(localStorage.getItem(G+'-adapt')));
 for(let i=0;i<40;i++)naAdaptNote(G,'easy',-1);const kg=naKnobs(G,'easy');R.adaptGentle=kg.adapt<-.99&&kg.temp>k0.temp&&kg.blind>k0.blind;
 A.adapt=false;R.adaptOff=naKnobs(G,'easy').adapt===0;A.adapt=true;
 const bad=['{','null','[1,2]','{"easy":"x","normal":5}','{"easy":NaN}','{"easy":-7,"normal":null}','"easy"'];
 R.adaptDamaged=bad.every(s=>{localStorage.setItem(G+'-adapt',s);const k=naKnobs(G,'easy'),kk=naKnobs(G,'normal');return k.adapt===0&&kk.adapt===0&&k.temp===1.2});
 localStorage.setItem(G+'-adapt','{"easy":0.5}');R.adaptRead=naAdapt(G,'easy')===.5&&naKnobs(G,0).level==='easy';
 // a result in between (Remi: your place at the table) moves it part of the way; out of range counts as +-1
 localStorage.removeItem(G+'-adapt');naAdaptNote(G,'easy',1/3);naAdaptNote(G,'normal',-1/3);naAdaptNote(G,'easy',7);naAdaptNote(G,'normal','x');
 R.adaptPart=naAdapt(G,'easy')===.254&&naAdapt(G,'normal')===-.054;
 // a game's own range: span (how far towards the next level) and soft (its gentlest values; only those knobs move)
 naLevel[G]={easy:{temp:2,kill:1},span:{easy:.5},soft:{easy:{kill:.5}}};
 localStorage.setItem(G+'-adapt','{"easy":1}');let kq=naKnobs(G,'easy');R.adaptSpan=Math.abs(kq.temp-(2+(.3-2)*.5))<1e-9&&Math.abs(kq.blind-(.3+(.05-.3)*.5))<1e-9&&kq.kill===1;
 localStorage.setItem(G+'-adapt','{"easy":-0.5}');kq=naKnobs(G,'easy');R.adaptSoft=kq.temp===2&&kq.blind===.3&&kq.kill===.75;
 localStorage.setItem(G+'-adapt','{"normal":-1}');kq=naKnobs(G,'normal');R.adaptMirror=kq.temp>.3&&kq.blind>.05;
 delete naLevel[G];
 localStorage.removeItem(G+'-adapt');
 Math.random=mr;R.noMathRandom=used===0;
 return R}"""

port = start_server(8958)
pw, b, page = open_page(port, 'iphone12')
fails = 0
for g in GAMES:
    f = open_game(page, g)
    r = f.evaluate(JS)
    bad = [k for k, v in r.items() if v is not True]
    fails += len(bad)
    print(g, 'kit checks', len(r), 'failed', bad, len(bad) == 0)
    to_cover(page)
print('kit failures:', fails)
print('console errors:', page.errors[:5])
b.close(); pw.stop()
