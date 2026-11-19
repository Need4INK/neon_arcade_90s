// Neon Arcade shared core: one copy of what every game needs. build.py puts it in front of each game's own script.
// A game supplies its sounds (naSfx = its SFX table) and the function that refreshes its Settings rows (naSync = fn).
// The end of the file holds the CPU brain kit (naRng, naThink, naSearch, naWorker, naChoose, naLevel, naKnobs, naAdapt, __ai).
var AC=null,sndOn=false,naSfx={},naSync=null,naKeep=null,naWant=false;
function naEl(i){return document.getElementById(i)}

// ---- sound
// a game that is not on screen (you went back to the cover) makes no sound
function naHid(){try{return !!(window.frameElement&&window.frameElement.hidden)}catch(e){return false}}
function naQuiet(){return !sndOn||naHid()}
function audio(){if(!AC){try{var X=window.AudioContext||window.webkitAudioContext;AC=X?new X():null}catch(e){AC=null}}
 if(AC&&AC.state==='suspended'){try{AC.resume()}catch(e){}}return AC}
function tone(f,d,type,vol,when,to){var a=audio();if(!a)return;var t=a.currentTime+(when||0),o=a.createOscillator(),g=a.createGain();
 o.type=type||'square';o.frequency.setValueAtTime(f,t);if(to)o.frequency.exponentialRampToValueAtTime(to,t+d);
 g.gain.setValueAtTime(vol||.06,t);g.gain.exponentialRampToValueAtTime(.0001,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.02)}
function sfx(n,a){if(naQuiet())return;try{naSfx[n](a)}catch(e){}}
// iPhone: sound plays with the ringer off; the silent loop keeps audio awake on older iPhones. Needs a tap, so a game
// that got Sound from another game unlocks at its first tap.
function naUnlock(){try{if(navigator.audioSession)navigator.audioSession.type='playback'}catch(e){}
 try{if(!naKeep){naKeep=new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQQAAAAAAAAA');naKeep.loop=true}naKeep.play().catch(function(){})}catch(e){}
 audio()}
function naSound(on,tap){sndOn=!!on;if(!sndOn){naWant=false;if(naKeep){try{naKeep.pause()}catch(e){}}return}
 if(tap){naWant=false;naUnlock()}else naWant=true}
document.addEventListener('pointerdown',function(){if(sndOn&&naWant&&!naHid()){naWant=false;naUnlock()}},true);
// the cover calls this when it takes over the screen
function naPause(){if(naKeep){try{naKeep.pause()}catch(e){}}naWant=sndOn}

// ---- Sound and Scanlines: set in one game, all five follow while the app is open (kept on the cover, never saved)
function naShare(k,v){try{parent.naShare(k,v,window)}catch(e){}}
function naSet(k,v){if(k==='snd')naSound(v,false);else document.body.classList.toggle('nocrt',!v);if(naSync)naSync()}
try{var naO=parent.naShared;if(naO){if(naO.snd)naSound(true,false);if(!naO.crt)document.body.classList.add('nocrt')}}catch(e){}

// ---- Rules / Settings panel
var panel=naEl('panel'),bar=naEl('bar'),pR=naEl('pRules'),pS=naEl('pSet'),bR=naEl('bRules'),bS=naEl('bSet'),naShade=naEl('shade');
function showPanel(n){var cur=panel.hidden?'':panel.dataset.p,nx=n&&n!==cur?n:'';panel.hidden=!nx;if(naShade)naShade.hidden=!nx;panel.dataset.p=nx;pR.hidden=nx!=='rules';pS.hidden=nx!=='settings';
 bR.setAttribute('aria-expanded',nx==='rules'?'true':'false');bS.setAttribute('aria-expanded',nx==='settings'?'true':'false');if(nx==='settings'&&naSync)naSync()}
function setSw(id,on){var b=naEl(id);b.setAttribute('aria-checked',on?'true':'false');b.textContent=on?'On':'Off'}
// Settings rows with 3 or more choices (and any row marked data-mtr, like the on-screen difficulty or a 2-choice Mode row) are drawn as a level meter (.mtr): --i = picked choice, --n = choices; kept up to date as games rebuild or re-press them
function naMtr(){document.querySelectorAll('#pSet .seg,[data-mtr]').forEach(function(s){var b=s.children,n=b.length,i=-1,k;for(k=0;k<n;k++)if(b[k].getAttribute('aria-pressed')==='true')i=k;s.classList.toggle('mtr',n>2||s.hasAttribute('data-mtr'));s.style.setProperty('--n',n);s.style.setProperty('--i',i)})}
// Rules open by themselves the first time a game is opened
function naFirstRules(key){try{if(!localStorage.getItem(key)){showPanel('rules');localStorage.setItem(key,'1')}}catch(e){}}
bR.onclick=function(){showPanel('rules')};bS.onclick=function(){showPanel('settings')};
if(naShade)naShade.onclick=function(e){e.preventDefault();showPanel('')};
naEl('tgSound').onclick=function(){naSound(!sndOn,true);if(sndOn){try{naSfx.on()}catch(e){}}if(naSync)naSync();naShare('snd',sndOn)};
naEl('tgCrt').onclick=function(){var off=document.body.classList.toggle('nocrt');if(naSync)naSync();naShare('crt',!off)};
// a tap outside the open panel closes it and does nothing else; so does Escape
document.addEventListener('click',function(e){if(!panel.hidden&&!panel.contains(e.target)&&!bar.contains(e.target)){e.stopPropagation();e.preventDefault();showPanel('')}},true);
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!panel.hidden)showPanel('')});
naMtr();(function(){var mo=new MutationObserver(naMtr),o={subtree:true,childList:true,attributes:true,attributeFilter:['aria-pressed']};mo.observe(pS,o);document.querySelectorAll('[data-mtr]').forEach(function(e){mo.observe(e,o)})})();
// Exit: close any open panel, then show the cover (the game stays loaded)
(function(){var x=document.querySelector('#bar .mnu');if(x)x.onclick=function(){try{document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))}catch(e){}try{parent.kbShowCover()}catch(e){}}})();
// the panel opens right above the bar, wherever the game's layout puts the bar
(function(){var a=naEl('app');function place(){var y=0,e=bar;while(e&&e!==a){y+=e.offsetTop;e=e.offsetParent}panel.style.bottom=Math.max(0,a.clientHeight-y)+'px'}
 place();addEventListener('resize',function(){setTimeout(place,0)});
 try{new MutationObserver(place).observe(panel,{attributes:true,attributeFilter:['hidden']});new ResizeObserver(place).observe(document.querySelector('main'))}catch(e){}})();

// ---- "Tap again": the first tap arms the button for 3 s, the second one does it
function naDisarm(b){clearTimeout(b._t);if(b.classList.contains('arm')){b.classList.remove('arm');b.textContent=b._l}}
function naArm(b,fn){if(b.disabled)return;
 if(!b.classList.contains('arm')){b._l=b.textContent;b.classList.add('arm');b.textContent='Tap again';clearTimeout(b._t);b._t=setTimeout(function(){naDisarm(b)},3000);return}
 naDisarm(b);fn()}

// ---- CPU brain kit (claude/ai-blueprint.md section 4). Each game builds its CPU on these; tests drive them via window.__ai.
// Random numbers that can be seeded: naRng(seed) gives a function returning 0 <= x < 1. naR is the shared one, seeded
// from the clock; __ai.seed(n) reseeds it so a test repeats exactly. Dice and shuffles never depend on the level.
function naRng(seed){var a=seed>>>0;return function(){a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
var naR=naRng(Date.now()^Math.floor(naNow()*1000));
function naNow(){return self.performance&&performance.now?performance.now():Date.now()}
// naThink(fn,{min,max,ok}): one CPU decision with a visible pause. fn(deadline) finds the move (it may return a Promise,
// e.g. from naWorker) and should stop by deadline (now + max ms). The answer comes no sooner than min ms after the start.
// ok() says the game is still the same one (gid / token check): if not, the Promise never settles, so no late move or sound.
function naThink(fn,o){o=o||{};var t0=naNow(),min=naAI.fast?0:o.min||0,ok=o.ok||o.token;
 return new Promise(function(res,rej){Promise.resolve().then(function(){return fn(t0+(o.max||1500))}).then(function(v){
  setTimeout(function(){if(!ok||ok())res(v)},Math.max(0,min-(naNow()-t0)))},function(e){if(!ok||ok())rej(e)})})}
// Looking ahead deeper each round: naSearch(fn,{from,to,deadline}) calls fn(depth,deadline) for depth from..to and keeps the
// deepest answer that finished ({v,depth}). Inside its loops fn calls naTick(deadline), which throws NA_TIME once time is up;
// that depth is dropped. The first depth always finishes (no deadline). fn may return {done:true} to stop early.
var NA_TIME={t:1};
function naTick(dl){if(dl&&naNow()>dl)throw NA_TIME}
function naSearch(fn,o){var best=null,f=o.from||1;for(var d=f;d<=(o.to||64);d++){try{var v=fn(d,d===f?0:o.deadline);best={v:v,depth:d};if(v&&v.done)break}
 catch(e){if(e!==NA_TIME)throw e;break}if(o.deadline&&naNow()>o.deadline)break}return best}
// Heavy thinking off the main screen: naWorker(work,helpers) starts a Worker from a blob: URL (the CSP allows it) holding
// work(data) and the helpers: plain functions that use nothing from outside (the kit's naNow, naTick, naSearch, naRng and
// naChoose come along). .run(data) gives a Promise of work(data). If no Worker starts or it fails, work runs on the main thread.
function naWorker(work,helpers){var fns=[naNow,naTick,naSearch,naRng,naChoose].concat(helpers||[]),W=null,n=0,cb={};
 function here(d){return new Promise(function(res){res(work(d))})}
 try{if(!naAI.main){W=new Worker(URL.createObjectURL(new Blob(['var NA_TIME={t:1},naR=naRng(Date.now());\n'+fns.map(String).join('\n')+'\nvar work='+work+
  ';\nonmessage=function(e){var r,x=null;try{r=work(e.data.d)}catch(er){x=String(er)}postMessage({i:e.data.i,r:r,x:x})}'],{type:'text/javascript'})));
  W.onmessage=function(e){var c=cb[e.data.i];delete cb[e.data.i];if(c)c(e.data)};
  W.onerror=function(e){if(e.preventDefault)e.preventDefault();var k=cb;cb={};W=null;for(var i in k)k[i](null)}}}catch(e){W=null}
 return {run:function(d){if(!W)return here(d);var i=++n;return new Promise(function(res,rej){
   cb[i]=function(m){if(!m)here(d).then(res,rej);else if(m.x!=null)rej(new Error(m.x));else res(m.r)};
   try{W.postMessage({i:i,d:d})}catch(e){delete cb[i];here(d).then(res,rej)}})},
  stop:function(){if(W)W.terminate();W=null;cb={}}}}
// The one mistake model. moves: [{s:score,...}], higher is better. k.temp: how loosely it picks among good moves (0 = always
// the best; otherwise softmax over s/temp). k.blind: chance to overlook the best move this time. A move may carry miss (0..1),
// how easy it is to overlook (a tile deep in the discard row); then every move is overlooked with chance blind x miss.
// At least one move is always seen. No pure random picks: the weights always follow the scores.
function naChoose(moves,k,r){r=r||naR;k=k||{};if(moves.length<2)return moves[0];var bl=k.blind||0,t=k.temp||0,i,w=0,
 ms=moves.slice().sort(function(a,b){return b.s-a.s}),see=ms.filter(function(m,i){var p=bl*(m.miss!=null?m.miss:i?0:1);return !(p>0&&r()<p)});
 if(!see.length)see=[ms[0]];if(!t||see.length<2)return see[0];
 var ws=see.map(function(m){var x=Math.exp((m.s-see[0].s)/t);w+=x;return x}),q=r()*w;
 for(i=0;i<see.length;i++){q-=ws[i];if(q<=0)return see[i]}return see[see.length-1]}
// Level knobs for every game in one place (blueprint section 6), tuned with tests/ai_tournament.py. "all" says what a level
// means everywhere; a game's own knobs go under its key and win over the shared ones.
var NA_LV=['easy','normal','hard'],naLevel={all:{easy:{temp:1.2,blind:.3},normal:{temp:.3,blind:.05},hard:{temp:0,blind:0}},kb:{},oth:{},remi:{}};
// naKnobs(game,level): that level's knobs, nudged by naAdapt. Sharper (x>0) moves a knob towards the next level's value
// (Easy up to 90% of the way, Normal a third, or the game's naLevel[game].span[level]); gentler (x<0) moves it away by the same share, unless the game sets the
// gentlest values itself (naLevel[game].soft[level]): then only those knobs move, towards them (a beginner stays a
// beginner, never worse than random). Hard never moves. Knobs that must be whole numbers are rounded by the game.
function naKnobs(game,level){var lv=typeof level==='number'?NA_LV[level]:level,i=NA_LV.indexOf(lv),g=naLevel[game]||{},o={},nx={},k;
 [naLevel.all[lv],g[lv]].forEach(function(s){for(k in s)o[k]=s[k]});[naLevel.all[NA_LV[i+1]],g[NA_LV[i+1]]].forEach(function(s){for(k in s)nx[k]=s[k]});
 var x=naAI.adapt?naAdapt(game,lv):0,span=lv==='hard'?0:g.span&&g.span[lv]!=null?g.span[lv]:lv==='easy'?.9:1/3,sf=x<0&&g.soft&&g.soft[lv];o.level=lv;o.adapt=x;
 if(sf){for(k in sf)if(typeof o[k]==='number'&&typeof sf[k]==='number')o[k]+=(sf[k]-o[k])*-x}
 else if(x&&span)for(k in o)if(typeof o[k]==='number'&&typeof nx[k]==='number'&&k!=='adapt')o[k]+=(nx[k]-o[k])*x*span;return o}
// Adjusting to the player (blueprint 6a): one number per game and level, -1 (you keep losing: gentler) to 1 (you keep
// winning: sharper), about your last 5 results. Saved as <game>-adapt (kb-adapt, oth-adapt, remi-adapt); damaged = 0.
function naAdaptAll(game){var o={};try{o=JSON.parse(localStorage.getItem(game+'-adapt'))||{}}catch(e){}var r={};
 if(o&&typeof o==='object')['easy','normal'].forEach(function(l){var v=o[l];if(typeof v==='number'&&isFinite(v)&&v>=-1&&v<=1)r[l]=v});return r}
function naAdapt(game,level){return level==='hard'?0:naAdaptAll(game)[level]||0}
// after each game vs the CPU: won = 1 you won, -1 you lost, 0 a tie, or in between (Remi: your place at the table);
// never during a game
function naAdaptNote(game,level,won){if(level==='hard'||!naAI.adapt)return;var a=naAdaptAll(game),v=(a[level]||0)*.8+.2*Math.max(-1,Math.min(1,+won||0));
 a[level]=Math.max(-1,Math.min(1,Math.round(v*1000)/1000));try{localStorage.setItem(game+'-adapt',JSON.stringify(a))}catch(e){}}
// Test hooks: __ai.seed(n), adapt (false = no adjusting), fast (no thinking pauses), main (no Worker), knobs, choose;
// a game sets __ai.pick(state,level) and __ai.level once its CPU uses the kit (tests/ai_tournament.py calls pick).
var naAI=window.__ai={seed:function(s){naR=naRng(s)},adapt:true,fast:false,main:false,pick:null,level:null,knobs:naKnobs,adaptOf:naAdapt,choose:naChoose};
