"""Packs the Neon Arcade games and the cover page into one HTML file.

Usage:  python3 build.py Knucklebones.html Othello.html Water_Sort.html Sudoku.html Remi.html Neon-Arcade.html

Each game stays a normal standalone page. This script only adds the yellow Menu button
to each game's bottom bar and wraps all five in the cover page (cards, flicker title,
portrait lock, offline service-worker registration). Publish the output next to
sw.js, manifest.json and icon.png.
"""
import json, sys
kb = open(sys.argv[1], encoding='utf-8').read()
oth = open(sys.argv[2], encoding='utf-8').read()
ws = open(sys.argv[3], encoding='utf-8').read()
sdk = open(sys.argv[4], encoding='utf-8').read()
rem = open(sys.argv[5], encoding='utf-8').read()
out = sys.argv[6]

MENU_CSS = '.bar .mnu{color:var(--yel);text-shadow:0 0 6px var(--yel)}'
# Menu button in each game's bottom bar: closes any open panel (games close it on Escape), then shows the cover.
MENU_BTN = '<button type="button" class="mnu" onclick="try{document.dispatchEvent(new KeyboardEvent(\'keydown\',{key:\'Escape\'}))}catch(e){}try{parent.kbShowCover()}catch(e){}">Menu</button>'
CENTRE = '.bar{display:grid;grid-template-columns:1fr auto 1fr;align-items:center}#bRules{justify-self:start}#bar .mnu{justify-self:center}#bSet{justify-self:end}'

# Knucklebones: bar is already a 3-column grid, middle column is free
kb = kb.replace('</style>', '#bar .mnu{grid-column:2;justify-self:center}' + MENU_CSS + '</style>', 1)
kb = kb.replace('aria-controls="panel">Rules</button>', 'aria-controls="panel">Rules</button>' + MENU_BTN, 1)
# Othello, Water Sort, Sudoku and Remi: turn the two-button bar into three columns so Menu sits exactly in the middle
for name in ('oth', 'ws', 'sdk', 'rem'):
    g = globals()[name]
    g = g.replace('</style>', CENTRE + MENU_CSS + '</style>', 1)
    g = g.replace('id="bRules" aria-expanded="false">Rules</button>', 'id="bRules" aria-expanded="false">Rules</button>' + MENU_BTN, 1)
    globals()[name] = g
assert all(g.count('class="mnu"') == 1 for g in (kb, oth, ws, sdk, rem))

# Stage: every screen is laid out 390 points wide (iPhone 12) and scaled evenly to fit; the stage always fills
# the full height below the notch, reaching over the home-bar area (only 10 points kept), so the bar sits at the
# very bottom (iPhone 12: 390 x 787). Screens
# shorter than 680 (after scaling to the width) shrink instead. The iframe fills the whole screen (no seams at the notch / home
# bar); the cover tells each game the safe-area insets, which iOS doesn't pass into iframes.
NACALC = ("var NA_W=390,NA_H=763,NA_MIN=680;function naCalc(s,W,H,rot,r270){s={t:s.t,l:s.l,r:s.r,b:Math.min(s.b,10)};var w=W-s.l-s.r,h=H-s.t-s.b,cw=rot?h:w,ch=rot?w:h,"
          "k=Math.min(cw/NA_W,ch/NA_MIN),sh=ch/k,a=rot?(r270?90:-90):0;return {k:k,sh:sh,a:a,"
          "st:'translate('+(s.l+w/2)+'px,'+(s.t+h/2)+'px) rotate('+a+'deg) scale('+k+') translate('+(-NA_W/2)+'px,'+(-sh/2)+'px)'}}")
STAGE = ('<style>html.stg #app{position:fixed!important;left:0!important;top:0!important;right:auto!important;bottom:auto!important;'
         'width:390px!important;height:var(--sh)!important;margin:0!important;transform-origin:0 0!important;transform:var(--st)!important}'
         # one background for the whole screen: on the html (some games only painted the body, which iOS can leave short)
         'html.stg{padding:0!important;height:100%!important;background:linear-gradient(#07030f,rgba(7,3,15,0) 64px),radial-gradient(120% 55% at 50% 0%,rgba(255,43,214,.18),transparent 60%),radial-gradient(120% 45% at 50% 100%,rgba(25,243,255,.13),transparent 60%),#07030f!important}'
         'html.stg body{background:transparent!important}html.stg.rot #app,html.stg #app{background:transparent!important;padding:0!important}'
         # iOS does give the home-bar inset inside the games after all: the bars added it as padding, lifting them ~34pt
         'html.stg .bar{padding-bottom:0!important}html.stg main{max-height:none!important}html.stg body:not(.flip) main{padding-bottom:6px!important}html.stg body:not(.flip) .side{max-height:none!important}'
         # title at the top, bar at the bottom, the game takes the room between (grows where it can, else centred);
         # the 2-player flip modes keep their own layout
         'html.stg body:not(.flip) main>h1{flex:none!important;max-height:none!important}html.stg body:not(.flip) main>.bar{flex:none!important;margin-top:auto!important}'
         'html.stg body:not(.flip) main>noscript+*,html.stg body:not(.flip) main>h1+:not(noscript){margin-top:auto!important}</style>\n'
         '<script>(function(){var de=document.documentElement;de.classList.add("stg");' + NACALC +
         'function st(){var W=innerWidth,H=innerHeight,rot=W>H&&H<600&&matchMedia("(pointer:coarse)").matches,a=0;'
         'if(rot){a=screen.orientation&&typeof screen.orientation.angle==="number"?screen.orientation.angle:(window.orientation===-90?270:90)}'
         'var s={t:0,r:0,b:0,l:0};try{s=parent.__safe()}catch(e){}var r=naCalc(s,W,H,rot,a===270);'
         'de.style.setProperty("--sh",r.sh+"px");de.style.setProperty("--st",r.st)}'
         'st();addEventListener("resize",st);addEventListener("orientationchange",function(){setTimeout(st,90)});'
         # the stage is never short, so drop the games' short-screen classes
         'try{new MutationObserver(function(){if(de.classList.contains("short"))de.classList.remove("short");if(de.classList.contains("tiny"))de.classList.remove("tiny")}).observe(de,{attributes:true,attributeFilter:["class"]})}catch(e){}'
         '})()</script>\n')
PANEL_A = "function place(){if(document.documentElement.classList.contains('rot')){"
PANEL_B = "function place(){if(document.documentElement.classList.contains('rot')||document.documentElement.classList.contains('stg')){"
for name in ('kb', 'oth', 'ws', 'sdk', 'rem'):
    g = globals()[name]
    assert g.count('</head>') == 1 and g.count(PANEL_A) == 1, name
    globals()[name] = g.replace('</head>', STAGE + '</head>', 1).replace(PANEL_A, PANEL_B, 1)

# Fonts: if games/fonts/ holds PressStart2P-Regular and VT323-Regular (.woff2, .woff or .ttf), they are packed
# into the page so the games never depend on Google Fonts (works offline even if the fonts were never saved).
# The cover declares them once; each game copies that declaration from the cover when it loads.
import base64, io, os
GLINK = '<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">'
FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
def font_face(name, family):
    for ext in ('woff2', 'woff', 'ttf'):
        f = os.path.join(FDIR, name + '.' + ext)
        if not os.path.exists(f):
            continue
        data, mime, fmt = open(f, 'rb').read(), ext, {'woff2': 'woff2', 'woff': 'woff', 'ttf': 'truetype'}[ext]
        try:  # keep only the characters the games use, saved as compressed woff
            from fontTools import subset
            from fontTools.ttLib import TTFont
            ft = TTFont(io.BytesIO(data))
            o = subset.Options(); o.flavor = 'woff'; o.ignore_missing_unicodes = True; o.name_IDs = ['*']  # keeps the OFL licence text in the font
            sub = subset.Subsetter(o)
            sub.populate(unicodes=list(range(0x20, 0x7f)) + list(range(0xa0, 0x180)) + list(range(0x2010, 0x2050)) + [0x2190, 0x2192, 0x2605, 0x25ae, 0x2713, 0xd7])
            sub.subset(ft); buf = io.BytesIO(); ft.flavor = 'woff'; ft.save(buf)
            data, mime, fmt = buf.getvalue(), 'woff', 'woff'
        except Exception:
            pass
        return "@font-face{font-family:'%s';font-style:normal;font-weight:400;font-display:swap;src:url(data:font/%s;base64,%s) format('%s')}" % (
            family, mime, base64.b64encode(data).decode(), fmt)
    return None
FONTS = [font_face('PressStart2P-Regular', 'Press Start 2P'), font_face('VT323-Regular', 'VT323')]
PACK_FONTS = all(FONTS)
if PACK_FONTS:
    COPY = '<script>try{var nf=parent.document.getElementById("nafonts");if(nf){var st=document.createElement("style");st.textContent=nf.textContent;document.head.appendChild(st)}}catch(e){}</script>'
    for name in ('kb', 'oth', 'ws', 'sdk', 'rem'):
        assert globals()[name].count(GLINK) == 1, name
        globals()[name] = globals()[name].replace(GLINK, COPY)
else:
    print('Note: games/fonts/ not found or incomplete, using Google Fonts')

games = json.dumps({'kb': kb, 'oth': oth, 'ws': ws, 'sdk': sdk, 'rem': rem}).replace('</', '<\\/')

page = r'''<!DOCTYPE html>
<html lang="en" class="stg">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Neon Arcade</title>
<meta name="description" content="Neon Arcade: Knucklebones, Othello, Water Sort, Sudoku and Remi. Play solo, against the CPU or a friend on one phone.">
<meta name="theme-color" content="#07030f">
<meta name="apple-mobile-web-app-title" content="Neon Arcade">
<meta name="application-name" content="Neon Arcade">
<meta property="og:title" content="Neon Arcade">
<meta property="og:description" content="Five neon arcade games: Knucklebones, Othello, Water Sort, Sudoku and Remi. Play solo, against the CPU or a friend on one phone.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://need4ink.github.io/neon_arcade_90s/">
<meta property="og:image" content="https://need4ink.github.io/neon_arcade_90s/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Neon Arcade: Knucklebones, Othello, Water Sort, Sudoku and Remi">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%95%B9%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="icon.png">
<link rel="manifest" href="manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
<style>
:root{--bg:#07030f;--panel:#10072a;--line:#2e1d66;--ink:#eaf6ff;--mut:#9a8bd6;--mag:#ff2bd6;--cy:#19f3ff;--yel:#ffe94d;--die:#0b0720;--or:#ff9e2c;--rd:#e8566a;
--px:"Press Start 2P","Courier New",monospace;--vt:"VT323","Courier New",monospace;color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--vt);font-size:18px}
#cover{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;justify-content:safe center;gap:22px;
 padding:calc(20px + env(safe-area-inset-top,0px)) 18px calc(20px + env(safe-area-inset-bottom,0px));overflow:auto;
 background:linear-gradient(#07030f,rgba(7,3,15,0) 64px),radial-gradient(120% 55% at 50% 0%,rgba(255,43,214,.2),transparent 60%),radial-gradient(120% 45% at 50% 100%,rgba(25,243,255,.15),transparent 60%),var(--bg)}
#cover::after{content:"";position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(to bottom,transparent 0 2px,rgba(0,0,0,.16) 2px 3px)}
.logo{text-align:center}
.logo h1{cursor:pointer;-webkit-tap-highlight-color:transparent}
.logo h1:focus-visible{outline:3px solid var(--yel);outline-offset:6px}
/* Share pop-up: tap the title for the QR code, home-screen steps and a share button */
.share{position:absolute;inset:0;z-index:30;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(7,3,15,.86);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px)}
.sbox{width:100%;max-width:300px;background:var(--panel);border:2px solid var(--cy);border-radius:10px;padding:16px 16px 14px;text-align:center;box-shadow:0 0 18px rgba(25,243,255,.45),inset 0 0 12px rgba(25,243,255,.08)}
.sbox .st{display:block;font:400 12px/1.4 var(--px);color:var(--yel);text-shadow:0 0 8px var(--yel);margin-bottom:12px}
.sbox .qr{width:min(200px,38vh);margin:0 auto;padding:10px;background:#fff;border-radius:8px;line-height:0}
.rot .sbox .qr{width:min(200px,38vw)}
.sbox .qr svg{width:100%;height:auto}
.sbox p{margin:6px 0 0;color:var(--mut);font-size:19px;line-height:20px}
.sbox p b{font-weight:400;color:var(--ink)}
.sbox .sp{margin-top:12px;color:var(--ink)}.sbox .sq{margin-top:6px;white-space:nowrap}.sbox .sq b{color:var(--cy)}
.sbtn{display:flex;justify-content:center;gap:10px;margin-top:14px}
.sbtn button{background:transparent;color:var(--cy);border:2px solid var(--cy);border-radius:4px;padding:6px 10px;font:400 10px/1.2 var(--px);cursor:pointer;text-shadow:0 0 8px var(--cy);box-shadow:0 0 10px rgba(25,243,255,.4)}
.sbtn button.y{color:var(--yel);border-color:var(--yel);text-shadow:0 0 8px var(--yel);box-shadow:0 0 10px rgba(255,233,77,.5)}
.sbtn button:active{background:currentColor}
.sbtn button:focus-visible{outline:3px solid var(--yel);outline-offset:2px}
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
.cards{display:flex;flex-direction:column;gap:12px;width:100%;max-width:360px}
.card{display:flex;align-items:center;gap:14px;width:100%;padding:10px;border-radius:8px;background:var(--panel);cursor:pointer;text-align:left;font:inherit;color:inherit;border:2px solid}
.card.kb{border-color:#39ff7a;box-shadow:0 0 10px rgba(57,255,122,.5),inset 0 0 14px rgba(57,255,122,.14)}
.card.oth{border-color:var(--mag);box-shadow:0 0 10px rgba(255,43,214,.5),inset 0 0 14px rgba(255,43,214,.14)}
.card.ws{border-color:var(--cy);box-shadow:0 0 10px rgba(25,243,255,.5),inset 0 0 14px rgba(25,243,255,.14)}
.card.sdk{border-color:var(--or);box-shadow:0 0 10px rgba(255,158,44,.5),inset 0 0 14px rgba(255,158,44,.14)}
.card.rem{border-color:var(--rd);box-shadow:0 0 10px rgba(232,86,106,.45),inset 0 0 14px rgba(232,86,106,.12)}
.card:active{transform:scale(.98);filter:brightness(1.3)}
.card:focus-visible{outline:3px solid var(--mag);outline-offset:3px}
/* Icon is exactly as tall as the text block: title 16px + 6px gap + two 20px lines = 62px */
.ic{flex:none;width:62px;height:62px;display:block}
.card b{display:block;font:400 12px/16px var(--px);margin-bottom:6px;white-space:nowrap}
/* Player-count flag: a fixed-size tab in the card's top-right corner */
.card{position:relative}
.flag{position:absolute;top:0;right:0;width:44px;height:16px;font:400 8px/16px var(--px);font-style:normal;text-align:center;color:#07030f;border-radius:0 5px 0 6px}
.card.kb .flag{background:#39ff7a}.card.oth .flag{background:var(--mag)}.card.ws .flag{background:var(--cy)}.card.sdk .flag{background:var(--or)}.card.rem .flag{background:var(--rd)}
.card.kb b{color:#39ff7a;text-shadow:0 0 8px #39ff7a}
.card.oth b{color:var(--mag);text-shadow:0 0 8px var(--mag)}
.card.ws b{color:var(--cy);text-shadow:0 0 8px var(--cy)}
.card.sdk b{color:var(--or);text-shadow:0 0 8px var(--or)}
.card.rem b{color:var(--rd);text-shadow:0 0 8px var(--rd)}
.card small{color:var(--mut);font-size:19px;line-height:20px;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden}
.card>span{min-width:0}
.blink{font:400 10px/1 var(--px);color:var(--yel);text-shadow:0 0 8px var(--yel);animation:blink 1.2s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
/* Phone held sideways: turn the cover back to portrait, like the games */
.rot #cover{inset:auto;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg);padding:calc(20px + env(safe-area-inset-right,0px)) 18px calc(20px + env(safe-area-inset-left,0px))}
.rot.r270 #cover{transform:translate(-50%,-50%) rotate(90deg);padding:calc(20px + env(safe-area-inset-left,0px)) 18px calc(20px + env(safe-area-inset-right,0px))}
.rot #cover::after{background:repeating-linear-gradient(to right,transparent 0 2px,rgba(0,0,0,.16) 2px 3px)}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
html.stg,html.stg body{background:linear-gradient(#07030f,rgba(7,3,15,0) 64px),radial-gradient(120% 55% at 50% 0%,rgba(255,43,214,.18),transparent 60%),radial-gradient(120% 45% at 50% 100%,rgba(25,243,255,.13),transparent 60%),#07030f}
/* iOS does not pass notch / home-bar insets into iframes, so keep the frame inside the safe area here. */
html{background:var(--bg)}
iframe{position:fixed;top:env(safe-area-inset-top,0px);bottom:env(safe-area-inset-bottom,0px);left:env(safe-area-inset-left,0px);right:env(safe-area-inset-right,0px);width:calc(100% - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px));height:calc(100% - env(safe-area-inset-top,0px) - env(safe-area-inset-bottom,0px));border:0;background:var(--bg)}
/* Stage (see build.py): the cover content is laid out at 390 x 763 and scaled to fit; iframes fill the screen */
html.stg #cover{inset:0!important;width:auto!important;height:auto!important;transform:none!important;padding:0!important;display:block;overflow:hidden}
#cstage{position:absolute;left:0;top:0;width:390px;height:var(--sh,763px);transform-origin:0 0;transform:var(--st);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:20px 15px}
.sbox{transform:var(--sr)}
iframe{top:0!important;left:0!important;right:0!important;bottom:auto!important;width:100%!important;height:var(--fullh,100%)!important}
html.stg #cover{bottom:auto!important;height:var(--fullh,100%)!important}
[hidden]{display:none!important}
</style>
</head>
<body>
<div id="cover">
 <div id="cstage">
 <div class="logo"><h1 id="logoT" role="button" tabindex="0" aria-label="Neon Arcade: share and add to home screen"><span class="w1">Neon</span><span class="w2">Arcade</span></h1><p><span class="md">Two modes</span> · <span class="md"><svg class="pi cy" viewBox="0 0 12 12" role="img" aria-label="P1"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg> vs <svg class="pi mg" viewBox="0 0 12 10" role="img" aria-label="CPU"><path d="M3 0h1v1h-1zM8 0h1v1h-1zM4 1h1v1h-1zM7 1h1v1h-1zM1 2h10v1h-10zM1 3h10v1h-10zM0 4h12v1h-12zM0 5h12v1h-12zM0 6h12v1h-12zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10z"/><path fill="#000" d="M3 4h2v1h-2zM7 4h2v1h-2zM3 5h2v1h-2zM7 5h2v1h-2zM3 7h1v1h-1zM8 7h1v1h-1zM4 8h4v1h-4z"/></svg></span> / <span class="md"><svg class="pi cy" viewBox="0 0 12 12" role="img" aria-label="P1"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg> vs <svg class="pi mg" viewBox="0 0 12 12" role="img" aria-label="P2"><path d="M4 0h4v1h-4zM3 1h6v1h-6zM3 2h6v1h-6zM3 3h6v1h-6zM4 4h4v1h-4zM2 6h8v1h-8zM1 7h10v1h-10zM1 8h10v1h-10zM1 9h10v1h-10zM1 10h10v1h-10zM1 11h10v1h-10z"/></svg></span></p></div>
 <div class="cards">
  <button type="button" class="card kb" data-g="kb">
   <i class="flag" role="img" aria-label="1 or 2 players">1–2P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#39ff7a" stroke-width="3"/>
    <g fill="#c9ffd9"><circle cx="17" cy="17" r="5.5"/><circle cx="47" cy="17" r="5.5"/><circle cx="32" cy="32" r="5.5"/><circle cx="17" cy="47" r="5.5"/><circle cx="47" cy="47" r="5.5"/></g></svg>
   <span><b>Knucklebones</b><small>Stack dice, multiply, smash rivals.</small></span>
  </button>
  <button type="button" class="card oth" data-g="oth">
   <i class="flag" role="img" aria-label="1 or 2 players">1–2P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#ff2bd6" stroke-width="3"/>
    <circle cx="20.5" cy="20.5" r="10" fill="#0b5f70" stroke="#19f3ff" stroke-width="2.5"/><circle cx="43.5" cy="43.5" r="10" fill="#0b5f70" stroke="#19f3ff" stroke-width="2.5"/>
    <circle cx="43.5" cy="20.5" r="10" fill="#7a0d65" stroke="#ff2bd6" stroke-width="2.5"/><circle cx="20.5" cy="43.5" r="10" fill="#7a0d65" stroke="#ff2bd6" stroke-width="2.5"/></svg>
   <span><b>Othello</b><small>Flip discs and grab the corners.</small></span>
  </button>
  <button type="button" class="card ws" data-g="ws">
   <i class="flag" role="img" aria-label="1 player">1P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><defs><clipPath id="tA"><path d="M14 10h14v34a7 7 0 0 1-14 0z"/></clipPath><clipPath id="tB"><path d="M36 10h14v34a7 7 0 0 1-14 0z"/></clipPath></defs>
    <rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#19f3ff" stroke-width="3"/>
    <g clip-path="url(#tA)"><rect x="14" y="21" width="14" height="10" fill="#ff2bd6"/><rect x="14" y="31" width="14" height="10" fill="#19f3ff"/><rect x="14" y="41" width="14" height="11" fill="#ff2bd6"/></g>
    <g clip-path="url(#tB)"><rect x="36" y="31" width="14" height="10" fill="#ffe94d"/><rect x="36" y="41" width="14" height="11" fill="#ffe94d"/></g>
    <path d="M14 10v34a7 7 0 0 0 14 0V10M36 10v34a7 7 0 0 0 14 0V10" fill="none" stroke="#c7fcff" stroke-width="2"/></svg>
   <span><b>Water Sort</b><small>Pour until each tube is one colour.</small></span>
  </button>
  <button type="button" class="card sdk" data-g="sdk">
   <i class="flag" role="img" aria-label="1 player">1P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#ff9e2c" stroke-width="3"/>
    <path d="M23.5 8v48M40.5 8v48M8 23.5h48M8 40.5h48" stroke="#ff9e2c" stroke-width="2" opacity=".7"/>
    <g font-family="'Press Start 2P',monospace" font-size="10" text-anchor="middle"><text x="15.5" y="20.5" fill="#eaf6ff">5</text><text x="48.5" y="20.5" fill="#19f3ff">3</text><text x="32" y="37.5" fill="#ffe94d">9</text><text x="15.5" y="54.5" fill="#39ff7a">1</text><text x="48.5" y="54.5" fill="#ff2bd6">7</text></g></svg>
   <span><b>Sudoku</b><small>Fill rows, columns and boxes 1–9.</small></span>
  </button>
  <button type="button" class="card rem" data-g="rem">
   <i class="flag" role="img" aria-label="1 player against 3 CPU">1P</i>
   <svg class="ic" viewBox="0 0 64 64" aria-hidden="true"><rect x="1.5" y="1.5" width="61" height="61" rx="8" fill="#0b0720" stroke="#e8566a" stroke-width="3"/>
    <g fill="#120a2e" stroke="#eaf6ff" stroke-width="2"><rect x="11" y="10" width="30" height="44" rx="4" opacity=".45"/><rect x="17" y="10" width="30" height="44" rx="4" opacity=".7"/><rect x="23" y="10" width="30" height="44" rx="4"/></g>
    <g fill="none" stroke-linecap="round" transform="translate(6 0)">
     <ellipse cx="32" cy="25" rx="9" ry="10.5" stroke="#eaf6ff" stroke-width="1.6"/>
     <path d="M25.5 20.5q3-2.6 5-.4M33.5 20.1q2-2.2 5 .4" stroke="#ffe94d" stroke-width="1.6"/>
     <path d="M26.6 23.6q1.9-1.5 3.8 0q-1.9 1.3-3.8 0zM33.6 23.6q1.9-1.5 3.8 0q-1.9 1.3-3.8 0z" fill="#19f3ff" stroke="#19f3ff" stroke-width=".8"/>
     <circle cx="32" cy="27" r="1.5" fill="#ff3b5c" stroke="none"/>
     <path d="M27 29.5q5 5.5 10 0" stroke="#ff3b5c" stroke-width="1.8"/>
     <ellipse cx="32" cy="45" rx="6" ry="4" stroke="#9a8bd6" stroke-width="1.2"/>
     <circle cx="32" cy="45" r="2" fill="#ffe94d" stroke="none"/></g></svg>
   <span><b>Remi</b><small>Romanian rummy: open 45, close first.</small></span>
  </button>
 </div>
 <div class="blink">Select a game</div>
 </div>
 <div class="share" id="share" role="dialog" aria-modal="true" aria-labelledby="shT" hidden><div class="sbox">
  <b class="st" id="shT">Scan to play</b>
  <div class="qr">__QR__</div>
  <p class="sp">Save it to your home screen:</p>
  <p class="sq"><b>iPhone</b>: Share › Add to Home Screen</p>
  <p class="sq"><b>Android</b>: Menu › Install app</p>
  <div class="sbtn"><button type="button" id="shShare">Copy link</button><button type="button" class="y" id="shClose">Close</button></div>
 </div></div>
</div>
<script>
var GAMES=__GAMES__;
// Safe-area insets (notch / home bar), read here and shared with the games (window.__SAFE overrides, for testing)
var naP=document.createElement('div');naP.style.cssText='position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)';document.body.appendChild(naP);
window.__safe=function(){if(window.__SAFE)return window.__SAFE;var c=getComputedStyle(naP);return {t:parseFloat(c.paddingTop)||0,r:parseFloat(c.paddingRight)||0,b:parseFloat(c.paddingBottom)||0,l:parseFloat(c.paddingLeft)||0}};
__NACALC__
// iOS home-screen apps with a see-through status bar draw the page from the top of the screen but report a
// height that leaves out the status bar, so a strip at the bottom stays empty. Detect it (page height + top inset =
// screen height) and use the full height. Not tied to navigator.standalone: newer iOS web apps don't set it.
function naFullH(){var s=__safe(),H=innerHeight;try{if(s.t>0&&innerWidth<innerHeight&&H<screen.height-1&&Math.abs(H+s.t-screen.height)<2)H+=s.t}catch(e){}return H}
function naCover(){var de=document.documentElement,H=naFullH();de.style.setProperty('--fullh',H+'px');var r=naCalc(__safe(),innerWidth,H,de.classList.contains('rot'),de.classList.contains('r270'));
 de.style.setProperty('--sh',r.sh+'px');de.style.setProperty('--st',r.st);de.style.setProperty('--sr','rotate('+r.a+'deg) scale('+r.k+')')}
// Keep each card description to two lines: shrink the text a little if it would wrap to a third.
function fitCards(){document.querySelectorAll('.card small').forEach(function(el){el.style.fontSize='';el.style.webkitLineClamp='unset';
 var f=19;while(el.scrollHeight>41&&f>14){f-=.5;el.style.fontSize=f+'px'}el.style.webkitLineClamp=''})}
// Same rule as the games: a phone (touch, short side under 600px) held sideways shows the cover upright.
function orientCover(){var de=document.documentElement,W=innerWidth,H=innerHeight,c=document.getElementById('cover'),
 rot=W>H&&H<600&&matchMedia('(pointer:coarse)').matches,a=0;
 if(rot){a=screen.orientation&&typeof screen.orientation.angle==='number'?screen.orientation.angle:(window.orientation===-90?270:90)}
 de.classList.toggle('rot',rot);de.classList.toggle('r270',rot&&a===270);
 c.style.width=rot?H+'px':'';c.style.height=rot?W+'px':'';naCover();fitCards()}
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
 if(!frames[g]){var f=document.createElement('iframe');f.title={kb:'Knucklebones',oth:'Othello',ws:'Water Sort',sdk:'Sudoku',rem:'Remi'}[g];f.setAttribute('allow','autoplay');
  f.srcdoc=GAMES[g];document.body.appendChild(f);frames[g]=f}
 current=g;
 if(push){try{history.pushState({g:g},'',location.pathname+location.search)}catch(e){}}
 setTimeout(function(){try{frames[g].contentWindow.focus()}catch(e){}},50)}
function showCover(){
 Object.keys(frames).forEach(function(k){frames[k].hidden=true});
 cover.hidden=false;current=null}
// Called by the Menu button inside each game. Games stay loaded, so a match in progress is kept.
// Share pop-up on the title
(function(){var sh=document.getElementById('share'),t=document.getElementById('logoT'),sb=document.getElementById('shShare'),URL='https://need4ink.github.io/neon_arcade_90s/',tm=null;
 function open(){sh.hidden=false;sb.textContent='Copy link';fitLines();setTimeout(function(){document.getElementById('shClose').focus()},0)}
 // keep each home-screen line on one line: shrink the text a little on narrow phones
 function fitLines(){sh.querySelectorAll('.sq').forEach(function(p){p.style.fontSize='';var f=19;while(p.scrollWidth>p.clientWidth&&f>14){f-=.5;p.style.fontSize=f+'px'}})}
 function close(){sh.hidden=true;t.focus()}
 t.onclick=open;t.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}};
 document.getElementById('shClose').onclick=close;sh.onclick=function(e){if(e.target===sh)close()};
 document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!sh.hidden)close()});
 sb.onclick=function(){
  function done(ok){sb.textContent=ok?'Copied!':URL;clearTimeout(tm);tm=setTimeout(function(){sb.textContent='Copy link'},2500)}
  try{navigator.clipboard.writeText(URL).then(function(){done(true)},function(){done(false)})}catch(e){done(false)}}})();
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
page = page.replace('__GAMES__', games).replace('__NACALC__', NACALC)
QR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons', 'qr.svg')
page = page.replace('__QR__', open(QR, encoding='utf-8').read() if os.path.exists(QR) else '')
if PACK_FONTS:
    assert page.count(GLINK) == 1
    page = page.replace(GLINK, '<style id="nafonts">' + ''.join(FONTS) + '</style>')
open(out, 'w', encoding='utf-8').write(page)
print(len(page))
