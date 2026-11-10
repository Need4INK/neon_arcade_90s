"""Independent referee for Othello and Knucklebones: auto-plays full games by tapping, and checks every move
against its own copy of the rules (legal moves, flips / removed dice, passes, end of game, result text, saved stats).

    python3 tests/referee.py oth 30         # games per CPU level (Hard gets a quarter)
    python3 tests/referee.py kb 60
"""
import sys, json
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, open_page, open_game, to_cover
port=start_server(8911 if sys.argv[1]=="oth" else 8912); pw,b,page=open_page(port,'iphone12')
FAST="const st=window.setTimeout;window.setTimeout=(f,t,...a)=>st(f,Math.min(t||0,2),...a);window.__sleep=ms=>new Promise(r=>st(r,ms));"
OTH=FAST+r"""
const V=window.__v=[];window.__plays=0;let lastMover=0;
const inB=(i,j)=>i>=0&&j>=0&&i<8&&j<8;
function fl(b,r,c,p){if(b[r][c]!==0)return null;let out=[];for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){if(!dr&&!dc)continue;let i=r+dr,j=c+dc,line=[];while(inB(i,j)&&b[i][j]===-p){line.push([i,j]);i+=dr;j+=dc}if(line.length&&inB(i,j)&&b[i][j]===p)out.push(...line)}return out}
function legal(b,p){const m=[];for(let r=0;r<8;r++)for(let c=0;c<8;c++){const f=fl(b,r,c,p);if(f&&f.length)m.push([r,c,f])}return m}
const orig=play;
play=function(m){const before=bd.map(r=>r.slice()),t=turn,lg=legal(before,t),mine=lg.find(x=>x[0]===m.r&&x[1]===m.c);
 if(over)V.push('play after game over');if(!mine)V.push('illegal move '+JSON.stringify([m.r,m.c,t]));
 if(lastMover===t&&legal(before,-t).length)V.push('same side moved twice though the other side had moves');
 const r=orig.apply(this,arguments);
 if(mine){const e=before.map(r=>r.slice());e[m.r][m.c]=t;mine[2].forEach(([i,j])=>e[i][j]=t);if(JSON.stringify(e)!==JSON.stringify(bd))V.push('wrong board after a move')}
 lastMover=t;window.__plays++;return r};
window.__game=async function(md,df){mode=md;S.diff=df;const s0=JSON.stringify(S);lastMover=0;start();if(JSON.stringify(bd)!==JSON.stringify([0,1,2,3,4,5,6,7].map(r=>[0,1,2,3,4,5,6,7].map(c=>(r==3&&c==3)||(r==4&&c==4)?bd[3][3]:(r==3&&c==4)||(r==4&&c==3)?-bd[3][3]:0))))V.push('odd start position');
 if(turn!==1)V.push('P1 does not start');let n=0,idle=0;
 while(!over&&n++<6000){
  if(busy||(mode==='cpu'&&turn!==1)){await __sleep(4);if(++idle>3000){V.push('stalled waiting for CPU');break}continue}idle=0;
  const lg=legal(bd,turn);if(!lg.length){V.push('side to move has no move but game goes on');break}
  const sq=document.querySelectorAll('#board .sq');if(sq.length!==64){V.push('board has '+sq.length+' squares');break}
  if(Math.random()<.2){const ill=[];for(let i=0;i<64;i++){const r=i/8|0,c=i%8;if(!lg.some(x=>x[0]===r&&x[1]===c))ill.push(i)}const s=JSON.stringify(bd);sq[ill[Math.random()*ill.length|0]].click();if(JSON.stringify(bd)!==s)V.push('illegal square accepted')}
  const hint=[...sq].map((q,i)=>q.classList.contains('can')?i:-1).filter(i=>i>=0).join(),mineH=lg.map(x=>x[0]*8+x[1]).sort((a,b)=>a-b).join();
  if(hints&&hint!==mineH)V.push('hint squares differ from legal moves: '+hint+' vs '+mineH);
  const m=lg[Math.random()*lg.length|0],k=__plays;sq[m[0]*8+m[1]].click();if(__plays===k)V.push('legal square refused');await __sleep(2)}
 await __sleep(30);
 const a=bd.flat().filter(x=>x===1).length,z=bd.flat().filter(x=>x===-1).length,msg=document.querySelector('#msg>div').textContent;
 if(!over)V.push('game did not finish');else{if(legal(bd,1).length||legal(bd,-1).length)V.push('ended while a move existed');
  const nums=(msg.match(/\d+/g)||[]).map(Number);const exp=a===z?[a]:md==='2p'?[a>z?1:2,Math.max(a,z),Math.min(a,z)]:[a,z];
  if(JSON.stringify(nums)!==JSON.stringify(exp))V.push('result text "'+msg+'" vs counts '+a+'-'+z);
  if(md==='cpu'&&((a>z)!==/You win/.test(msg)||(a<z)!==/You lose/.test(msg)))V.push('wrong winner text: '+msg+' '+a+'-'+z);
  const s1=JSON.parse(JSON.stringify(S)),o=JSON.parse(s0);const d=k=>s1[k]-o[k];
  const want=md==='cpu'?{w:+(a>z),l:+(a<z),t:+(a===z),p1:0,p2:0,pt:0}:{w:0,l:0,t:0,p1:+(a>z),p2:+(a<z),pt:+(a===z)};
  for(const k in want)if(d(k)!==want[k])V.push('stat '+k+' changed by '+d(k)+' expected '+want[k])}
 return [a,z]}"""
KB=FAST+r"""
const V=window.__v=[];window.__dice=[];
const sc=g=>g.reduce((s,a)=>{const n={};a.forEach(v=>n[v]=(n[v]||0)+1);return s+Object.keys(n).reduce((t,v)=>t+v*n[v]*n[v],0)},0);
const cp=g=>g.map(a=>a.slice()),J=JSON.stringify;
function diff(meB,oppB,me,opp,who){let k=-1;for(let i=0;i<me.length;i++){if(me[i].length===meB[i].length+1&&J(me[i].slice(0,-1))===J(meB[i])){if(k>=0)return who+': two columns changed';k=i}else if(J(me[i])!==J(meB[i]))return who+': own column changed oddly '+J(meB[i])+'->'+J(me[i])}
 if(k<0)return who+': no die placed';if(meB[k].length>=3)return who+': placed in a full column';const v=me[k][me[k].length-1];
 for(let i=0;i<opp.length;i++){const e=i===k?oppB[i].filter(x=>x!==v):oppB[i];if(J(opp[i])!==J(e))return who+': other grid wrong in column '+i+' '+J(oppB[i])+'->'+J(opp[i])+' after '+v}return v}
const fullG=g=>g.every(a=>a.length>=3);
window.__game=async function(md,df,nc){mode=md;S.diff=df;NC=nc;const s0=J(S);start();await __sleep(3);
 if(p.length!==nc||c.length!==nc||p.concat(c).some(a=>a.length))V.push('start not empty');let n=0,idle=0;
 while(!over&&n++<400){
  if(md==='cpu'&&turn!=='p'){await __sleep(3);if(++idle>4000){V.push('stalled on CPU turn');break}continue}idle=0;
  const side=turn,me=side==='p'?p:c,opp=side==='p'?c:p,meB=cp(me),oppB=cp(opp),d=die,el=document.getElementById(side==='p'?'pg':'cg');
  if(!(d>=1&&d<=6&&d===Math.floor(d)))V.push('bad die '+d);__dice.push(d);
  const btns=[...el.querySelectorAll('button.col')],can=btns.filter(b=>!b.disabled),free=me.map((a,i)=>a.length<3?i:-1).filter(i=>i>=0);
  if(can.length!==free.length)V.push(side+': '+can.length+' columns tappable, '+free.length+' have room');
  if(!can.length){V.push('no column to tap but game goes on');break}
  if(+document.getElementById('ps').textContent!==sc(p)||+document.getElementById('cs').textContent!==sc(c))V.push('score shown differs from my count');
  const full=btns.filter(b=>b.disabled);if(full.length){const s=J([p,c]);full[0].click();if(J([p,c])!==s)V.push('full column accepted a die')}
  const cB=cp(c),pB0=cp(p);can[Math.random()*can.length|0].click();
  const r=diff(meB,oppB,side==='p'?p:c,side==='p'?c:p,'player '+side);if(typeof r==='string')V.push(r);else if(r!==d)V.push('placed '+r+' but the die was '+d);
  if(md==='cpu'&&!over){const pA=cp(p),cA=cp(c);let w=0;while(turn!=='p'&&!over&&w++<4000)await __sleep(3);
   if(J(c)===J(cA)&&!over)V.push('CPU did not move');else if(J(c)!==J(cA)){const r2=diff(cA,pA,c,p,'CPU');if(typeof r2==='string')V.push(r2)}}
  if(!over&&(fullG(p)||fullG(c)))V.push('a grid is full but the game goes on');await __sleep(2)}
 await __sleep(20);const a=sc(p),z=sc(c),msg=document.querySelector('#msg .t').textContent;
 if(!over)V.push('game did not finish');else{if(!fullG(p)&&!fullG(c))V.push('ended with no full grid');
  if(+document.getElementById('ps').textContent!==a||+document.getElementById('cs').textContent!==z)V.push('final score shown differs');
  const nums=(msg.match(/\d+/g)||[]).map(Number);
  if(a!==z&&(nums.indexOf(Math.max(a,z))<0||nums.indexOf(Math.min(a,z))<0))V.push('result text "'+msg+'" vs '+a+'-'+z);
  if(md==='cpu'&&((a>z)!==/You win/i.test(msg)||(a<z)!==/You lose|CPU wins/i.test(msg)))V.push('winner text "'+msg+'" vs '+a+'-'+z);
  const s1=JSON.parse(J(S)),o=JSON.parse(s0),want=md==='cpu'?{w:+(a>z),l:+(a<z),t:+(a===z)}:{p1:+(a>z),p2:+(a<z),pt:+(a===z)};
  for(const k in want)if(s1[k]-o[k]!==want[k])V.push('stat '+k+' changed by '+(s1[k]-o[k])+' expected '+want[k]+' ('+msg+')')}
 return [a,z,msg]}"""
which=sys.argv[1]; N=int(sys.argv[2])
if which=='oth':
    f=open_game(page,'oth'); f.evaluate(OTH)
    for md,df,n in [('cpu','easy',N),('cpu','normal',N),('cpu','hard',max(2,N//4)),('2p','normal',N)]:
        w=[0,0,0]
        for i in range(n):
            a,z=f.evaluate("__game('%s','%s')"%(md,df)); w[0 if a>z else 1 if a<z else 2]+=1
        print('Othello',md,df,'games',n,'P1 wins/losses/ties',w,'violations',sorted(set(f.evaluate("__v")))[:8],flush=True)
else:
    f=open_game(page,'kb'); f.evaluate(KB)
    for md,df,nc,n in [('cpu','easy',3,N),('cpu','normal',3,N),('cpu','hard',3,N),('cpu','normal',4,N),('cpu','hard',4,N),('2p','normal',3,N),('2p','normal',4,N)]:
        w=[0,0,0]; last=''
        for i in range(n):
            a,z,last=f.evaluate("__game('%s','%s',%d)"%(md,df,nc)); w[0 if a>z else 1 if a<z else 2]+=1
        print('Knucklebones',md,df,'%dx3'%nc,'games',n,'P1 wins/losses/ties',w,'last:',last,'| violations',sorted(set(f.evaluate("__v")))[:8],flush=True)
    d=f.evaluate("__dice"); print('dice seen',len(d),[d.count(i) for i in range(1,7)])
print('console errors:',page.errors[:5]); b.close(); pw.stop()
