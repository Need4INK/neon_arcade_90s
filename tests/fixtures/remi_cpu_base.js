// Remi's CPU as it played before the AI build (main at 09e81ec, Nov 15 2026), kept as the yardstick for
// tests/ai_tournament.py remi --vs: the new CPU must beat this one at the same level. Never shipped: the tournament puts
// it into its test-only copy of the game. Only changes: names start with base_, the rule helpers get the table they
// work on (trySwap, fitsTable), and discards / draws go through toDisc / notePass so the new CPUs' memory sees them.
function base_cpuWants(p,d){const P=G.pl[p],h=P.hand.concat(d);
 return P.opened&&findBest(h,1,false).melds.some(m=>m.includes(d))}
function base_swapIdsFor(m,hand){const a=analyze(m.t);if(!a)return null;
 for(const s of a.seq){if(!s.j||G.jl[s.id])continue;
  if(a.type==='run'){const id=hand.find(x=>!isJ(x)&&TILES[x].n===face(s.n)&&TILES[x].c===s.c);if(id!=null)return [id]}
  else{const real=m.t.filter(x=>!isJ(x));if(m.t.length-real.length!==1)continue;const have=real.map(x=>TILES[x].c),n=TILES[real[0]].n,ids=[];
   for(let c=0;c<4;c++)if(!have.includes(c)){const id=hand.find(x=>!isJ(x)&&TILES[x].n===n&&TILES[x].c===c);if(id!=null)ids.push(id)}
   if(ids.length===4-real.length)return ids}}
 return null}
function base_cpuExtras(p,canLay){const P=G.pl[p];let any=false;
 for(let loop=0;loop<12;loop++){let ch=false;
  if(lvl===2)for(let mi=0;mi<G.melds.length&&P.hand.length>1;mi++){const m=G.melds[mi],ids=base_swapIdsFor(m,P.hand);if(!ids)continue;
   const bk=JSON.stringify({melds:G.melds,hand:P.hand,own:G.own,jl:G.jl});const j=trySwap(m,ids,G);if(j<0)continue;
   rm(P.hand,ids);P.hand.push(j);place(p,ids);let used=false;
   const oi=G.melds.findIndex(x=>x.o===p&&analyze(x.t.concat(j)));
   if(oi>=0&&P.hand.length>1){const x=G.melds[oi];x.t=analyze(x.t.concat(j)).seq.map(s=>s.id);rm(P.hand,[j]);place(p,[j]);used=true}
   else if(canLay){const b=findBest(P.hand,1,false);if(b.melds.some(z=>z.includes(j))){b.melds.forEach(z=>{rm(P.hand,z);G.melds.push({o:p,t:analyze(z).seq.map(s=>s.id)});place(p,z)});used=true}}
   if(used){ch=true}else{const r=JSON.parse(bk);G.melds=r.melds;P.hand=r.hand;G.own=r.own;G.jl=r.jl}}
  const order=P.hand.slice().sort((a,b)=>isJ(a)-isJ(b));
  for(const id of order){if(P.hand.length<=1)break;if(isJ(id)&&P.hand.length>3)continue;const mi=fitsTable(G.melds,id,p);
   if(mi>=0){const m=G.melds[mi];m.t=analyze(m.t.concat(id)).seq.map(s=>s.id);rm(P.hand,[id]);place(p,[id]);ch=true}}
  if(!ch)break;any=true}
 return any}
function base_chooseDiscard(p){const h=G.pl[p].hand;if(h.length===1)return h[0];
 const sc=h.map(id=>{if(isJ(id))return {id,s:1e6};const t=TILES[id];let s=-val(id)/12;
  h.forEach(o=>{if(o===id||isJ(o))return;const u=TILES[o];if(u.c===t.c){const d=Math.abs(u.n-t.n);if(d===1||d===12)s+=3;else if(d===2||d===11)s+=1.5}else if(u.n===t.n)s+=2.5});
  if(t.n===1&&h.length<=3)s+=4;                     // keep a 1 to close with (doubles)
  if(lvl===2&&fitsTable(G.melds,id,(p+1)%4)>=0)s+=1.5;       // don't feed the table
  return {id,s}}).sort((a,b)=>a.s-b.s);
 return lvl===0?sc[Math.floor(Math.random()*Math.min(3,sc.length))].id:sc[0].id}
async function base_cpuTurn(tk){
 const p=G.cur,P=G.pl[p],start=P.hand.length,startOpened=P.opened,nm=NAMES[p];const wait=async()=>{await sleep(DEL[spd]);return tk===token};
 if(!await wait())return;
 if(lvl>0&&canBoard(p)&&doubles(P.hand)>=5){P.board=true;ev.push([nm,'plays on the board']);say(nm+' plays on the board!');render();if(!await wait())return}
 if(P.board)return base_cpuBoard(p,wait);
 if(G.tn>0){const n=G.disc.length,d=n>1?G.disc[n-1]:-1;
  if(d>=0&&startOpened&&start>=3&&base_cpuWants(p,d)){G.disc.pop();P.hand.push(d);ev.push([nm,'took '+tname(d)]);say(nm+' takes '+tname(d))}
  else{notePass(p,start,startOpened);if(!refill()){endRound(-1,-1,'The pile ran out');return}P.hand.push(G.pile.pop());say(nm+' draws')}
  sfx('draw');render();if(!await wait())return}
 if(start>2){const b=P.opened?findBest(P.hand,1,false):canOpen()?openFor(P.hand):null;
  if(b&&b.melds.length){b.melds.forEach(ids=>{const a=analyze(ids);rm(P.hand,ids);G.melds.push({o:p,t:a.seq.map(s=>s.id)});place(p,ids)});
   const was=P.opened;P.opened=true;hitMeld=G.melds.length-1;sfx('lay');ev.push([nm,was?'laid down':'opened']);say(nm+(was?' lays down':' opens with '+b.pts));render();if(!await wait())return}}
 if(startOpened&&base_cpuExtras(p,start>2)){sfx('lay');ev.push([nm,'added']);say(nm+' adds to the table');render();if(!await wait())return}
 const id=base_chooseDiscard(p);toDisc(p,id);sfx('disc');
 if(!P.hand.length){endRound(p,id,nm+' closes with '+tname(id));return}
 say(nm+' discards '+tname(id)+(P.hand.length<=3?' · '+P.hand.length+' left!':''));nextTurn()}

// CPU on the board: collect doubles, close as soon as 14 tiles make a board hand
async function base_cpuBoard(p,wait){const P=G.pl[p],nm=NAMES[p],key=x=>isJ(x)?'j':TILES[x].c*13+TILES[x].n,cnt=x=>P.hand.filter(y=>key(y)===key(x)).length;
 if(G.tn>0){const n=G.disc.length,d=n>1?G.disc[n-1]:-1;
  if(d>=0&&canOpen()&&!isJ(d)&&cnt(d)===1){G.disc.pop();P.hand.push(d);ev.push([nm,'took '+tname(d)]);say(nm+' takes '+tname(d))}
  else{if(!refill()){endRound(-1,-1,'The pile ran out');return}P.hand.push(G.pile.pop());say(nm+' draws')}
  sfx('draw');render();if(!await wait())return}
 const out=boardOuts(P.hand);
 if(out.length){const {id,b}=out[0];toDisc(p,id);G.bw=b;sfx('disc');endRound(p,id,nm+' closes: '+b.nm+' +'+b.pts+'!');return}
 const singles=P.hand.filter(x=>!isJ(x)&&cnt(x)%2===1),id=singles.length?pickR(singles):pickR(P.hand.filter(x=>!isJ(x)));
 toDisc(p,id);sfx('disc');say(nm+' discards '+tname(id));nextTurn()}
