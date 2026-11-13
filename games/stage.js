// Neon Arcade stage: every screen is a 390 x 797 block (iPhone 12: banner 64 + game area 667 + bar 36 + gap 30), placed
// below the top safe inset and scaled as one to fit; other screen shapes get plain background around it. The game's
// iframe fills the whole screen; the cover gives each game the safe-area insets, which iOS doesn't pass into iframes.
// build.py puts this in each game's <head> (it runs before the page is drawn). __NACALC__ is the sizing shared with the cover.
(function(){var de=document.documentElement;
__NACALC__
// Remi's Medias Landscape layout (html.lnd) is a 750-wide block, turned a quarter only when the screen is upright;
// everything else stays upright when a phone lies sideways (touch screen, short side under 600)
function st(){var L=de.classList.contains("lnd"),W=innerWidth,H=innerHeight,rot=L?W<H:W>H&&H<600&&matchMedia("(pointer:coarse)").matches,a=0;
 var s={t:0,r:0,b:0,l:0};try{s=parent.__safe()}catch(e){}
 NA_W=L?750:390;NA_H=797;if(L){var cw=rot?H-s.t-s.b:W-s.l-s.r,ch=rot?W-s.l-s.r:H-s.t;NA_H=Math.max(390,Math.min(560,Math.round(750*ch/cw)))}de.style.setProperty("--stw",NA_W+"px");
 if(rot&&!L){a=screen.orientation&&typeof screen.orientation.angle==="number"?screen.orientation.angle:(window.orientation===-90?270:90)}
 de.classList.toggle("rot",rot&&!L);de.classList.toggle("r270",rot&&!L&&a===270);   // scanlines follow the picture
 var r=naCalc(s,W,L&&rot?H-s.b:H,rot,a===270);
 de.style.setProperty("--sh",r.sh+"px");de.style.setProperty("--st",r.st)}
window.naSt=st;st();addEventListener("resize",st);addEventListener("orientationchange",function(){setTimeout(st,90)});
})();
