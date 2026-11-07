"""Packs the Neon Arcade games and the cover page into one HTML file.

Usage:  python3 build.py Knucklebones.html Othello.html Water_Sort.html Neon-Arcade.html

Each game stays a normal standalone page. This script only adds the yellow Menu button
to each game's bottom bar and wraps all three in the cover page (cards, flicker title,
portrait lock, offline service-worker registration). Publish the output next to
sw.js, manifest.json and icon.png.
"""
import json, sys
kb = open(sys.argv[1], encoding='utf-8').read()
oth = open(sys.argv[2], encoding='utf-8').read()
ws = open(sys.argv[3], encoding='utf-8').read()
out = sys.argv[4]

MENU_CSS = '.bar .mnu{color:var(--yel);text-shadow:0 0 6px var(--yel)}'
# Menu button in each game's bottom bar: closes any open panel (games close it on Escape), then shows the cover.
MENU_BTN = '<button type="button" class="mnu" onclick="try{document.dispatchEvent(new KeyboardEvent(\'keydown\',{key:\'Escape\'}))}catch(e){}try{parent.kbShowCover()}catch(e){}">Menu</button>'
CENTRE = '.bar{display:grid;grid-template-columns:1fr auto 1fr;align-items:center}#bRules{justify-self:start}#bar .mnu{justify-self:center}#bSet{justify-self:end}'

# Knucklebones: bar is already a 3-column grid, middle column is free
kb = kb.replace('</style>', '#bar .mnu{grid-column:2;justify-self:center}' + MENU_CSS + '</style>', 1)
kb = kb.replace('aria-controls="panel">Rules</button>', 'aria-controls="panel">Rules</button>' + MENU_BTN, 1)
# Othello and Water Sort: turn the two-button bar into three columns so Menu sits exactly in the middle
for name in ('oth', 'ws'):
    g = globals()[name]
    g = g.replace('</style>', CENTRE + MENU_CSS + '</style>', 1)
    g = g.replace('id="bRules" aria-expanded="false">Rules</button>', 'id="bRules" aria-expanded="false">Rules</button>' + MENU_BTN, 1)
    globals()[name] = g
assert kb.count('class="mnu"') == 1 and oth.count('class="mnu"') == 1 and ws.count('class="mnu"') == 1

games = json.dumps({'kb': kb, 'oth': oth, 'ws': ws}).replace('</', '<\\/')

page = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Neon Arcade</title>
<meta name="description" content="Neon Arcade: Knucklebones, Othello and Water Sort. Play solo, against the CPU or a friend on one phone.">
<meta name="theme-color" content="#07030f">
<meta name="apple-mobile-web-app-title" content="Neon Arcade">
<meta name="application-name" content="Neon Arcade">
<meta property="og:title" content="Neon Arcade">
<meta property="og:description" content="Three neon arcade games: Knucklebones, Othello and Water Sort. Play solo, against the CPU or a friend on one phone.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%95%B9%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="icon.png">
<link rel="manifest" href="manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
<style>
:root{--bg:#07030f;--panel:#10072a;--line:#2e1d66;--ink:#eaf6ff;--mut:#9a8bd6;--mag:#ff2bd6;--cy:#19f3ff;--yel:#ffe94d;--die:#0b0720;
--px:"Press Start 2P","Courier New",monospace;--vt:"VT323","Courier New",monospace;color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--vt);font-size:18px}
#cover{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;
 padding:calc(20px + env(safe-area-inset-top,0px)) 18px calc(20px + env(safe-area-inset-bottom,0px));overflow:auto;
 background:radial-gradient(120% 55% at 50% 0%,rgba(255,43,214,.2),transparent 60%),radial-gradient(120% 45% at 50% 100%,rgba(25,243,255,.15),transparent 60%),var(--bg)}
#cover::after{content:"";position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(to bottom,transparent 0 2px,rgba(0,0,0,.16) 2px 3px)}
.logo{text-align:center}
.logo h1{font:400 26px/1.25 var(--px);letter-spacing:3px;margin:0;color:#fff;text-transform:uppercase;
 text-shadow:0 0 4px #fff,0 0 10px var(--mag),0 0 22px var(--mag),0 0 42px var(--mag);animation:powerOn 1.1s steps(1) 1}
.logo h1 .w1{display:block}
.logo h1 .w2{display:block;color:#fff;text-shadow:0 0 4px #fff,0 0 10px var(--cy),0 0 22px var(--cy),0 0 42px var(--cy)}
.logo p{margin:12px 0 0;color:var(--mut);font-size:21px}
.md{white-space:nowrap;word-spacing:-.18em}
/* Pixel icons in the tagline: person = player, robot = CPU */
.pi{height:.62em;height:1cap;width:auto;vertical-align:baseline;fill:currentColor;shape-rendering:crispEdges;filter:drop-shadow(0 0 3px currentColor)}
.pi.cy{color:var(--cy)}.pi.mg{color:var(--mag)}
@keyframes powerOn{0%{opacity:0}8%{opacity:1}12%{opacity:.2}18%{opacity:1}24%{opacity:.4}30%,100%{opacity:1}}
.cards{display:flex;flex-direction:column;gap:16px;width:100%;max-width:360px}
.card{display:flex;align-items:center;gap:16px;width:100%;padding:16px;border-radius:8px;background:var(--panel);cursor:pointer;text-align:left;font:inherit;color:inherit;border:2px solid}
.card.kb{border-color:#39ff7a;box-shadow:0 0 10px rgba(57,255,122,.5),inset 0 0 14px rgba(57,255,122,.14)}
.card.oth{border-color:var(--mag);box-shadow:0 0 10px rgba(255,43,214,.5),inset 0 0 14px rgba(255,43,214,.14)}
.card.ws{border-color:var(--cy);box-shadow:0 0 10px rgba(25,243,255,.5),inset 0 0 14px rgba(25,243,255,.14)}
.card:active{transform:scale(.98);filter:brightness(1.3)}
.card:focus-visible{outline:3px solid var(--mag);outline-offset:3px}
/* Icon is exactly as tall as the text block: title 16px + 6px gap + two 20px lines = 62px */
.ic{flex:none;width:62px;height:62px;display:block}
.card b{display:block;font:400 12px/16px var(--px);margin-bottom:6px;white-space:nowrap}
/* Player-count flag: a fixed-size tab in the card's top-right corner */
.card{position:relative}
.flag{position:absolute;top:0;right:0;width:44px;height:16px;font:400 8px/16px var(--px);font-style:normal;text-align:center;color:#07030f;border-radius:0 5px 0 6px}
.card.kb .flag{background:#39ff7a}.card.oth .flag{background:var(--mag)}.card.ws .flag{background:var(--cy)}
.card.kb b{color:#39ff7a;text-shadow:0 0 8px #39ff7a}
.card.oth b{color:var(--mag);text-shadow:0 0 8px var(--mag)}
.card.ws b{color:var(--cy);text-shadow:0 0 8px var(--cy)}
.card small{color:var(--mut);font-size:19px;line-height:20px;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden}
.card>span{min-width:0}
.blink{font:400 10px/1 var(--px);color:var(--yel);text-shadow:0 0 8px var(--yel);animation:blink 1.2s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
@media (max-height:520px){html:not(.rot) #cover{gap:12px}html:not(.rot) .logo h1{font-size:18px}html:not(.rot) .logo p{display:none}html:not(.rot) .cards{flex-direction:row;max-width:900px}html:not(.rot) .card{padding:10px}}
/* Phone held sideways: turn the cover back to portrait, like the games */
.rot #cover{inset:auto;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg);padding:calc(20px + env(safe-area-inset-right,0px)) 18px calc(20px + env(safe-area-inset-left,0px))}
.rot.r270 #cover{transform:translate(-50%,-50%) rotate(90deg);padding:calc(20px + env(safe-area-inset-left,0px)) 18px calc(20px + env(safe-area-inset-right,0px))}
.rot #cover::after{background:repeating-linear-gradient(to right,transparent 0 2px,rgba(0,0,0,.16) 2px 3px)}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
/* iOS does not pass notch / home-bar insets into iframes, so keep the frame inside the safe area here. */
html{background:var(--bg)}
iframe{position:fixed;top:env(safe-area-inset-top,0px);bottom:env(safe-area-inset-bottom,0px);left:env(safe-area-inset-left,0px);right:env(safe-area-inset-right,0px);width:calc(100% - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px));height:calc(100% - env(safe-area-inset-top,0px) - env(safe-area-inset-bottom,0px));border:0;background:var(--bg)}
[hidden]{display:none!important}
</style>
</head>
<body>
<div id="cover">
 <div class="logo"><h1><span class="w1">Neon</span><span class="w2">Arcade</span></h1><p><span class="md">Two modes</span> · <span class="md"><svg class="pi cy" viewBox="0 0 12 12" role="img" aria-label="P1"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg> vs <svg class="pi mg" viewBox="0 0 12 10" role="img" aria-label="CPU"><path d="M3 0h1v1h-1zM8 0h1v1h-1zM4 1h1v1h-1zM7 1h1v1h-1zM1 2h10v1h-10zM1 3h10v1h-10zM0 4h12v1h-12zM0 5h12v1h-12zM0 6h12v1h-12zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10z"/><path fill="#000" d="M3 4h2v1h-2zM7 4h2v1h-2zM3 5h2v1h-2zM7 5h2v1h-2zM3 7h1v1h-1zM8 7h1v1h-1zM4 8h4v1h-4z"/></svg></span> / <span class="md"><svg class="pi cy" viewBox="0 0 12 12" role="img" aria-label="P1"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg> vs <svg class="pi mg" viewBox="0 0 12 12" role="img" aria-label="P2"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg></span></p></div>
 <div class="cards">
  <button type="button" class="card kb" data-g="kb">
   <i class="flag" role="img" aria-label="1 or 2 players">1–2P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#39ff7a" stroke-width="3"/>
    <g fill="#c9ffd9"><circle cx="17" cy="17" r="5.5"/><circle cx="47" cy="17" r="5.5"/><circle cx="32" cy="32" r="5.5"/><circle cx="17" cy="47" r="5.5"/><circle cx="47" cy="47" r="5.5"/></g></svg>
   <span><b>Knucklebones</b><small>Stack dice, multiply matches, smash rival columns.</small></span>
  </button>
  <button type="button" class="card oth" data-g="oth">
   <i class="flag" role="img" aria-label="1 or 2 players">1–2P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#ff2bd6" stroke-width="3"/>
    <circle cx="20.5" cy="20.5" r="10" fill="#0b5f70" stroke="#19f3ff" stroke-width="2.5"/><circle cx="43.5" cy="43.5" r="10" fill="#0b5f70" stroke="#19f3ff" stroke-width="2.5"/>
    <circle cx="43.5" cy="20.5" r="10" fill="#7a0d65" stroke="#ff2bd6" stroke-width="2.5"/><circle cx="20.5" cy="43.5" r="10" fill="#7a0d65" stroke="#ff2bd6" stroke-width="2.5"/></svg>
   <span><b>Othello</b><small>Flip discs, own the board, grab the corners.</small></span>
  </button>
  <button type="button" class="card ws" data-g="ws">
   <i class="flag" role="img" aria-label="1 player">1P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><defs><clipPath id="tA"><path d="M14 10h14v34a7 7 0 0 1-14 0z"/></clipPath><clipPath id="tB"><path d="M36 10h14v34a7 7 0 0 1-14 0z"/></clipPath></defs>
    <rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#19f3ff" stroke-width="3"/>
    <g clip-path="url(#tA)"><rect x="14" y="21" width="14" height="10" fill="#ff2bd6"/><rect x="14" y="31" width="14" height="10" fill="#19f3ff"/><rect x="14" y="41" width="14" height="11" fill="#ff2bd6"/></g>
    <g clip-path="url(#tB)"><rect x="36" y="31" width="14" height="10" fill="#ffe94d"/><rect x="36" y="41" width="14" height="11" fill="#ffe94d"/></g>
    <path d="M14 10v34a7 7 0 0 0 14 0V10M36 10v34a7 7 0 0 0 14 0V10" fill="none" stroke="#c7fcff" stroke-width="2"/></svg>
   <span><b>Water Sort</b><small>Pour colours until each tube holds just one.</small></span>
  </button>
 </div>
 <div class="blink">Select a game</div>
</div>
<script>
var GAMES=__GAMES__;
// Keep each card description to two lines: shrink the text a little if it would wrap to a third.
function fitCards(){document.querySelectorAll('.card small').forEach(function(el){el.style.fontSize='';el.style.webkitLineClamp='unset';
 var f=19;while(el.scrollHeight>41&&f>14){f-=.5;el.style.fontSize=f+'px'}el.style.webkitLineClamp=''})}
// Same rule as the games: a phone (touch, short side under 600px) held sideways shows the cover upright.
function orientCover(){var de=document.documentElement,W=innerWidth,H=innerHeight,c=document.getElementById('cover'),
 rot=W>H&&H<600&&matchMedia('(pointer:coarse)').matches,a=0;
 if(rot){a=screen.orientation&&typeof screen.orientation.angle==='number'?screen.orientation.angle:(window.orientation===-90?270:90)}
 de.classList.toggle('rot',rot);de.classList.toggle('r270',rot&&a===270);
 c.style.width=rot?H+'px':'';c.style.height=rot?W+'px':'';fitCards()}
orientCover();addEventListener('resize',orientCover);addEventListener('orientationchange',function(){setTimeout(orientCover,100)});
try{screen.orientation.addEventListener('change',orientCover)}catch(e){}try{document.fonts.ready.then(fitCards)}catch(e){}
(function(){if(matchMedia('(prefers-reduced-motion:reduce)').matches)return;
 var w1=document.querySelector('.logo .w1'),w2=document.querySelector('.logo .w2'),R=function(a,b){return a+Math.random()*(b-a)};
 // Build a one-off flicker: a few blinks of random depth and length, sometimes a longer dim "buzz".
 function pattern(){var k=[{offset:0,opacity:1}],t=0,steps=[],n=1+Math.floor(Math.random()*4);
  if(Math.random()<.2){steps.push([R(.6,.8),R(250,550)])}
  for(var i=0;i<n;i++){steps.push([R(.45,.8),R(25,110)]);steps.push([1,R(30,160)])}
  if(Math.random()<.3)steps.push([R(.8,.92),R(80,200)]);
  steps.forEach(function(s){t+=s[1]});var acc=0;
  steps.forEach(function(s){k.push({offset:acc/t,opacity:s[0],easing:'steps(1,end)'});acc+=s[1]});
  k.push({offset:1,opacity:1});k[0].easing='steps(1,end)';return{k:k,d:t}}
 function fire(el){var p=pattern();try{el.animate(p.k,{duration:p.d})}catch(e){}}
 function tick(){if(!cover.hidden){var r=Math.random();
   if(r<.42)fire(w1);else if(r<.78)fire(w2);else{fire(w1);setTimeout(function(){fire(w2)},R(0,180))}}
  setTimeout(tick,R(1600,3600))}
 setTimeout(tick,R(1400,2400))})();
var frames={},cover=document.getElementById('cover'),current=null;
function openGame(g,push){
 cover.hidden=true;
 Object.keys(frames).forEach(function(k){frames[k].hidden=k!==g});
 if(!frames[g]){var f=document.createElement('iframe');f.title={kb:'Knucklebones',oth:'Othello',ws:'Water Sort'}[g];f.setAttribute('allow','autoplay');
  f.srcdoc=GAMES[g];document.body.appendChild(f);frames[g]=f}
 current=g;
 if(push){try{history.pushState({g:g},'',location.pathname+location.search)}catch(e){}}
 setTimeout(function(){try{frames[g].contentWindow.focus()}catch(e){}},50)}
function showCover(){
 Object.keys(frames).forEach(function(k){frames[k].hidden=true});
 cover.hidden=false;current=null}
// Called by the Menu button inside each game. Games stay loaded, so a match in progress is kept.
window.kbShowCover=function(){if(history.state&&history.state.g){try{history.back();return}catch(e){}}showCover()};
window.addEventListener('popstate',function(e){var g=e.state&&e.state.g;g&&GAMES[g]?openGame(g,false):showCover()});
document.querySelectorAll('.card').forEach(function(b){b.onclick=function(){openGame(b.dataset.g,true)}});
// Always start on the cover: drop any old #game from the URL and any game left in the history entry.
try{history.replaceState(null,'',location.pathname+location.search)}catch(e){}
// Offline: sw.js keeps a copy of this page and its fonts on the phone (needs https, e.g. GitHub Pages).
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost')){
 try{navigator.serviceWorker.register('sw.js').then(function(){return navigator.serviceWorker.ready}).then(function(r){
  var fonts=[].slice.call(document.querySelectorAll('link[rel=stylesheet]')).map(function(l){return l.href});
  if(r.active)r.active.postMessage({cache:[location.href.split('#')[0]].concat(fonts)})}).catch(function(){})}catch(e){}}
</script>
</body>
</html>
'''
page = page.replace('__GAMES__', games)
open(out, 'w', encoding='utf-8').write(page)
print(len(page))
