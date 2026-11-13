// Neon Arcade shared core: one copy of what every game needs. build.py puts it in front of each game's own script.
// A game supplies its sounds (naSfx = its SFX table) and the function that refreshes its Settings rows (naSync = fn).
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
// Rules open by themselves the first time a game is opened
function naFirstRules(key){try{if(!localStorage.getItem(key)){showPanel('rules');localStorage.setItem(key,'1')}}catch(e){}}
bR.onclick=function(){showPanel('rules')};bS.onclick=function(){showPanel('settings')};
if(naShade)naShade.onclick=function(e){e.preventDefault();showPanel('')};
naEl('tgSound').onclick=function(){naSound(!sndOn,true);if(sndOn){try{naSfx.on()}catch(e){}}if(naSync)naSync();naShare('snd',sndOn)};
naEl('tgCrt').onclick=function(){var off=document.body.classList.toggle('nocrt');if(naSync)naSync();naShare('crt',!off)};
// a tap outside the open panel closes it and does nothing else; so does Escape
document.addEventListener('click',function(e){if(!panel.hidden&&!panel.contains(e.target)&&!bar.contains(e.target)){e.stopPropagation();e.preventDefault();showPanel('')}},true);
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!panel.hidden)showPanel('')});
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
